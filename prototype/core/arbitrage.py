"""
ASEAN Grid — Arbitrage Engine (สมองจัดสรรงาน)
สแกนราคาทุกช่องทาง → เลือกช่องทางที่จ่ายสูงสุดสุทธิ (Smart Yield Balancer)

🧠 Smart Yield Balancer (จุดสมดุล 3 ด้าน):
1. Zero-Effort UX — เจ้าของเครื่องกดปุ่มเดียว ระบบจัดการเอง 100%
2. Maximum Net Profit — สลับงานต่อเมื่อคุ้มจริง: กำไรใหม่ > กำไรเดิม + 15% (threshold)
   และกำไรที่เพิ่มช่วงที่เหลือ > ค่าเสียเวลาสลับ container (overhead)
3. Stability — สแกนตลาดทุก 60 วิ (กัน rate limit) + งานลูกค้าไม่หลุดกลางคูณ

🧠 AI HOOK จุดนี้: การเลือกช่องทางที่ดีที่สุด = `strategy.predict_best_channel()`
- พื้นฐาน: HeuristicStrategy (คะแนนจากราคา/คิว/latency)
- ใส่โมเดล AI จูน: implement AIStrategy → StrategyRegistry.register(...)
  (ดู ai/strategy_hooks.py + ai/fine_tune/dataset_schema.md)
"""
from dataclasses import dataclass
import time
from typing import List, Optional

from prototype.core.channels import ChannelQuote, get_all_quotes
from prototype.core.config import Config
from prototype.ai.strategy_hooks import StrategyRegistry


@dataclass
class BalancePolicy:
    """
    กฎจุดสมดุล (Balance Policy) — ระบบจะสลับงานก็ต่อเมื่อ:
      gain_pct > threshold (15%)  AND  extra_gain(ช่วงที่เหลือ) > overhead_cost
    ป้องกันการสลับถี่เกินไปจนกำไรสุทธิลดลง (เสียเวลาเคลียร์ memory/โหลดโมเดล/สร้าง container)
    """
    threshold_pct: float = 0.15          # ต่างกันไม่ถึง 15% → ไม่สลับ
    switch_overhead_sec: int = 180       # เสียเวลาสลับงาน ~3 นาที (container ใหม่)

    def should_switch(self, current_net: float, candidate_net: float,
                      hold_sec: float, remaining_hours: float = 24.0) -> bool:
        """คืน True เมื่อควรสลับไปช่องทางใหม่ — คุ้มทั้ง threshold และ overhead"""
        if candidate_net <= current_net:
            return False
        gain_pct = (candidate_net - current_net) / max(1e-9, current_net)
        if gain_pct < self.threshold_pct:
            return False                       # ต่างไม่ถึง 15% — อยู่กับงานเดิมต่อ
        # คุ้ม overhead: รายได้ที่เสียระหว่างสลับ < กำไรที่เพิ่มในช่วงเวลาที่เหลือ
        overhead_cost = current_net * (self.switch_overhead_sec / 3600.0)
        extra_gain = (candidate_net - current_net) * remaining_hours
        return extra_gain > overhead_cost


class ArbitrageEngine:
    """Engine กลาง: scan → ตัดสินใจ (AI/Heuristic + Balance) → ส่งงาน"""

    def __init__(self, config: Optional[Config] = None, strategy_name: str = "heuristic",
                 balance: Optional[BalancePolicy] = None):
        self.config = config or Config()
        # strategy เปลี่ยนได้ runtime — ใส่โมเดล AI จูนได้โดยไม่แตะ engine
        self.strategy = StrategyRegistry.get(strategy_name)
        self.balance = balance or BalancePolicy(
            threshold_pct=self.config.SWITCH_THRESHOLD_PCT,
            switch_overhead_sec=self.config.SWITCH_OVERHEAD_SEC,
        )
        # สถานะช่องทางปัจจุบัน (สำหรับ Balance — กันสลับถี่เกินไป)
        self._current_channel: Optional[str] = None
        self._current_net: float = 0.0
        self._hold_started: float = time.time()

    def scan_market(self) -> List[ChannelQuote]:
        """สแกนราคาทุกช่องทาง (จริง: ทุก 60 วินาที — Smart Yield Balancer)"""
        return get_all_quotes()

    def pick_best_channel(self, workload=None, region: str = "ASEAN") -> Optional[str]:
        """
        เลือกช่องทางที่ดีที่สุด:
        1. สแกนราคา (quotes)
        2. ถาม AI strategy (ถ้ามี) — ถ้า AI ไม่ตอบ ใช้ heuristic
        """
        quotes = self.scan_market()
        if not quotes:
            return None

        features = {
            "region": region,
            "workload_type": getattr(workload, "wtype", None),
            "quotes": [
                {"channel": q.channel, "price": q.price_usd_per_hour,
                 "queue": q.queue_depth, "latency": q.latency_ms,
                 "reliability": q.reliability}
                for q in quotes
            ],
        }

        # 🧠 AI hook: ให้ strategy ตัดสินใจก่อน
        ai_choice = self.strategy.predict_best_channel(features)
        candidate = None
        if ai_choice and any(q.channel == ai_choice for q in quotes):
            candidate = next(q for q in quotes if q.channel == ai_choice)
        if candidate is None:
            candidate = max(quotes, key=lambda q: q.score)

        # 🧠 Smart Yield Balancer: กันสลับถี่เกินไป (threshold + overhead)
        now = time.time()
        hold_sec = now - self._hold_started
        if (self._current_channel is not None
                and candidate.channel != self._current_channel
                and not self.balance.should_switch(self._current_net,
                                                   candidate.price_usd_per_hour,
                                                   hold_sec)):
            return self._current_channel     # ไม่คุ้ม — อยู่กับช่องทางเดิมต่อ

        if candidate.channel != self._current_channel:
            self._current_channel = candidate.channel
            self._current_net = candidate.price_usd_per_hour
            self._hold_started = now
        return candidate.channel

    def route(self, workload) -> str:
        """ส่งงานไปช่องทางที่เลือก → คืน job_id"""
        from prototype.core.channels import CHANNEL_REGISTRY
        channel_name = self.pick_best_channel(workload)
        if channel_name is None:
            raise RuntimeError("No channel available — grid offline")
        channel = CHANNEL_REGISTRY[channel_name]
        return channel.submit_workload(workload)

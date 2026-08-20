"""
ASEAN Grid — Arbitrage Engine (สมองจัดสรรงาน)
สแกนราคาทุกช่องทาง → เลือกช่องทางที่จ่ายสูงสุด (Maximizing Profit Seconds)

🧠 AI HOOK จุดนี้: การเลือกช่องทางที่ดีที่สุด = `strategy.predict_best_channel()`
- พื้นฐาน: HeuristicStrategy (คะแนนจากราคา/คิว/latency)
- ใส่โมเดล AI จูน: implement AIStrategy → StrategyRegistry.register(...)
  (ดู ai/strategy_hooks.py + ai/fine_tune/dataset_schema.md)
"""
from typing import List, Optional

from prototype.core.channels import ChannelQuote, get_all_quotes
from prototype.core.config import Config
from prototype.ai.strategy_hooks import StrategyRegistry


class ArbitrageEngine:
    """Engine กลาง: scan → ตัดสินใจ (AI/Heuristic) → ส่งงาน"""

    def __init__(self, config: Optional[Config] = None, strategy_name: str = "heuristic"):
        self.config = config or Config()
        # strategy เปลี่ยนได้ runtime — ใส่โมเดล AI จูนได้โดยไม่แตะ engine
        self.strategy = StrategyRegistry.get(strategy_name)

    def scan_market(self) -> List[ChannelQuote]:
        """สแกนราคาทุกช่องทาง (จริง: ทุก 5 วินาที — MAXIMIZING PROFIT SECONDS)"""
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
        if ai_choice and any(q.channel == ai_choice for q in quotes):
            return ai_choice

        # fallback: heuristic (คะแนนสูงสุด)
        return max(quotes, key=lambda q: q.score).channel

    def route(self, workload) -> str:
        """ส่งงานไปช่องทางที่เลือก → คืน job_id"""
        from prototype.core.channels import CHANNEL_REGISTRY
        channel_name = self.pick_best_channel(workload)
        if channel_name is None:
            raise RuntimeError("No channel available — grid offline")
        channel = CHANNEL_REGISTRY[channel_name]
        return channel.submit_workload(workload)

"""
ASEAN Grid — Scheduler (จัดคิวงานอัตโนมัติ)
จัดงานให้โหนดตาม: ค่าไฟรายช่วงเวลา (tariff-aware) + ค่าไฟรายประเทศ + ความน่าเชื่อถือ + ความพร้อม

🧠 AI HOOK จุดนี้: `StrategyRegistry` มี `forecast_demand()` + `score_node_trust()`
- ใส่โมเดลพยากรณ์ดีมานด์/ค่าไฟ → จัดคิวล่วงหน้าได้
"""
from typing import List, Optional

from prototype.core.config import Config
from prototype.core.models import Node, Workload
from prototype.ai.strategy_hooks import StrategyRegistry


class Scheduler:
    def __init__(self, config: Optional[Config] = None, strategy_name: str = "heuristic"):
        self.config = config or Config()
        # strategy เปลี่ยนได้ runtime — โมเดล AI จูนใส่ได้โดยไม่แตะ scheduler
        self.strategy = StrategyRegistry.get(strategy_name)

    def tariff_factor(self, hour: int) -> float:
        """ค่าไฟรายช่วงเวลา: กลางคืนถูกกว่า กลางวัน (ค่าเฉลี่ยอาเซียน)"""
        if 0 <= hour < 6:
            return 0.7    # กลางคืน ไฟถูก
        if 6 <= hour < 18:
            return 1.3    # กลางวัน ไฟแพง
        return 1.0        # เย็น

    def country_tariff(self, region: str) -> float:
        """ค่าไฟรายประเทศ เทียบกับค่าเฉลี่ยฐาน (ELECTRICITY_USD_PER_KWH)
        เช่น vn=0.12 → 0.8 (ถูกกว่าไทย 20%) / sg=0.22 → 1.47 (แพงกว่า 47%)"""
        base = self.config.ELECTRICITY_USD_PER_KWH
        kwh = self.config.ELECTRICITY_BY_REGION.get(region, base)
        return kwh / base

    def schedule(self, nodes: List[Node], workload: Workload, hour: int = 12) -> List[Node]:
        """
        เรียงโหนดที่เหมาะกับงานนี้ที่สุด:
        - ฟรี (ACTIVE)
        - ค่าไฟช่วงนี้ถูก x ค่าไฟประเทศถูก
        - trust สูง (รวมคะแนนจาก AI strategy ถ้ามี)
        """
        time_factor = self.tariff_factor(hour)
        demand = self.strategy.forecast_demand(workload.region if hasattr(workload, "region") else "ASEAN", 6)

        candidates = [n for n in nodes if n.status.value == "active"]

        def cost_key(n: Node) -> float:
            country = self.country_tariff(n.region)
            # ต้นทุนไฟ = ค่าไฟโหนด x ช่วงเวลา x ประเทศ — หารด้วย trust (AI ปรับให้)
            ai_trust = self.strategy.score_node_trust(n)
            cost = (n.electricity_usd_per_kwh * time_factor * country) / max(0.01, ai_trust)
            # ดีมานด์สูง → โหนดถูกไฟยิ่งมีค่ามากขึ้น (ลดต้นทุนรวมของเครือข่าย)
            if demand > 0.6:
                cost *= 0.9
            return cost

        return sorted(candidates, key=cost_key)[:3]  # prototype: คืน 3 อันดับแรก

"""
ASEAN Grid — Scheduler (จัดคิวงานอัตโนมัติ)
จัดงานให้โหนดตาม: ค่าไฟรายช่วงเวลา (tariff-aware) + ความน่าเชื่อถือ + ความพร้อม

🧠 AI HOOK จุดนี้: `StrategyRegistry` มี `forecast_demand()` + `score_node_trust()`
- ใส่โมเดลพยากรณ์ดีมานด์/ค่าไฟ → จัดคิวล่วงหน้าได้
"""
from typing import List, Optional

from prototype.core.config import Config
from prototype.core.models import Node, Workload


class Scheduler:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def tariff_factor(self, hour: int) -> float:
        """ค่าไฟรายช่วงเวลา: กลางคืนถูกกว่า กลางวัน (ค่าเฉลี่ยอาเซียน)"""
        if 0 <= hour < 6:
            return 0.7    # กลางคืน ไฟถูก
        if 6 <= hour < 18:
            return 1.3    # กลางวัน ไฟแพง
        return 1.0        # เย็น

    def schedule(self, nodes: List[Node], workload: Workload, hour: int = 12) -> List[Node]:
        """
        เรียงโหนดที่เหมาะกับงานนี้ที่สุด:
        - ฟรี (ACTIVE)
        - ค่าไฟช่วงนี้ถูก
        - trust สูง
        """
        factor = self.tariff_factor(hour)
        candidates = [n for n in nodes if n.status.value == "active"]
        return sorted(
            candidates,
            key=lambda n: (n.electricity_usd_per_kwh * factor) / max(0.01, n.trust_score),
        )[:3]  # prototype: คืน 3 อันดับแรก

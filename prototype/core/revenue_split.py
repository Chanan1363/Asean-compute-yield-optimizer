"""
ASEAN Grid — Revenue Split 75/20/5 (จัดสรรรายได้อัตโนมัติ)
Core ที่ยืนยันแล้ว (ภาพ 18 ส.ค. 2026):
- 75% ผู้ให้เครื่อง (จ่ายรายวัน แปลงบาทได้)
- 20% ค่าดูแลระบบ
- 5% กองทุนนักพัฒนา

Prototype นี้เป็น interface + logic บริสุทธิ์ — สมาร์ทคอนแทร็กต์จริง
ดู contracts/RevenueSplit.sol (Solidity stub) — ตรรกะต้องตรงกัน 100%
"""
from dataclasses import dataclass
from typing import Dict, Optional

from prototype.core.config import Config


@dataclass
class SplitResult:
    total_usd: float
    node_usd: float
    platform_usd: float
    developer_usd: float
    breakdown: Dict[str, float]

    def __repr__(self) -> str:
        return (f"SplitResult(total=${self.total_usd:.2f}, "
                f"node=${self.node_usd:.2f} (75%), platform=${self.platform_usd:.2f} (20%), "
                f"developer=${self.developer_usd:.2f} (5%))")


class RevenueSplit:
    """แบ่งรายได้ตาม Core 75/20/5 — จ่ายรายวันให้ผู้ให้เครื่อง"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def split(self, amount_usd: float) -> SplitResult:
        """แบ่งรายได้จากลูกค้า (USD) → 3 กอง"""
        node = amount_usd * self.config.NODE_SHARE
        platform = amount_usd * self.config.PLATFORM_SHARE
        developer = amount_usd * self.config.DEVELOPER_SHARE
        return SplitResult(
            total_usd=amount_usd,
            node_usd=node,
            platform_usd=platform,
            developer_usd=developer,
            breakdown={
                "node_75": node,
                "platform_20": platform,
                "developer_5": developer,
            },
        )

    def daily_payout(self, node_revenue_usd: float, thb_rate: float = 35.0) -> Dict[str, float]:
        """
        จ่ายรายวันให้โหนดเดียว: USD → THB (Local THB Exchange)
        thb_rate: อัตราแลกเปลี่ยน (prototype: 35 บาท/USD)
        """
        return {
            "usd": round(node_revenue_usd, 4),
            "thb": round(node_revenue_usd * thb_rate, 2),
            "note": "payout daily via smart contract",
        }

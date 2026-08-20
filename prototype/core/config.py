"""
ASEAN Grid — Central Configuration
ค่าตั้งศูนย์กลางของระบบ — ทุกค่าที่ "ของตาย" ของโปรเจกต์อยู่ที่นี่
เปลี่ยนที่นี่ที่เดียว แล้วทั้งระบบรับรู้ (ตามหลักข้อมูลศูนย์กลางเดียว)
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class Config:
    # ── Core Revenue Split (ยืนยันจากภาพ 18 ส.ค. 2026) ──────────────
    NODE_SHARE: float = 0.75        # 75% ผู้ให้เครื่อง/ร้านเน็ต (จ่ายรายวัน)
    PLATFORM_SHARE: float = 0.20    # 20% ค่าดูแลระบบ/เซิร์ฟเวอร์
    DEVELOPER_SHARE: float = 0.05   # 5% กองทุนนักพัฒนา (PR/ปลั๊กอิน/แก้ช่องโหว่)

    # ── B2C / B2B ────────────────────────────────────────────────────
    B2C_SUBSCRIPTION_USD: float = 1.00          # $1/เดือน Earn While You Sleep
    B2B_PREPAID_MIN_USD: float = 50.00          # เติมเงินล่วงหน้าขั้นต่ำ (องค์กร)
    BILLING_GRANULARITY_SEC: int = 1            # จ่ายวินาทีต่อวินาที (Pay-per-Compute)

    # ── Tokenomics ($GRID) ───────────────────────────────────────────
    SYSTEM_FEE_MIN: float = 0.03                # Buyback & Burn 3-5%
    SYSTEM_FEE_MAX: float = 0.05
    STAKE_REQUIRED_USD: float = 100.00          # Staking หลักประกันโหนด

    # ── Arbitrage Engine ─────────────────────────────────────────────
    SCAN_INTERVAL_SEC: int = 5                  # สแกนราคาทุก 5 วินาที (prototype)
    MAX_PROFIT_SECONDS: bool = True             # Maximizing Profit Seconds
    ELECTRICITY_USD_PER_KWH: float = 0.15       # ค่าไฟเฉลี่ยอาเซียน (ปรับตามประเทศ)

    # ── Region ───────────────────────────────────────────────────────
    REGION: str = "ASEAN"
    TARGET_LATENCY_MS: tuple = (20, 40)         # 20-40ms pipeline (Geopolitical Arbitrage)

    # ── Channels (5 ช่องทางรายได้ — pluggable) ──────────────────────
    CHANNELS: tuple = ("vast_ai", "io_net", "render", "direct_ai", "studios")

    # ── Sanity guard: สัดส่วนต้องรวม = 1.0 ───────────────────────────
    def __post_init__(self) -> None:
        total = self.NODE_SHARE + self.PLATFORM_SHARE + self.DEVELOPER_SHARE
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Revenue shares must sum to 1.0, got {total}")

"""
ASEAN Grid — Data Models
โมเดลข้อมูลหลักของระบบ: Node, Workload, Tenant, ApiKey, Payout
ใช้ dataclass ล้วน (stdlib) — ต่อยอดเป็น Pydantic/SQLAlchemy ได้เมื่อทำจริง
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ──────────────────────────────────────────────────────────────

class WorkloadType(str, Enum):
    AI_TRAINING = "ai_training"          # เทรนโมเดล AI
    AI_INFERENCE = "ai_inference"        # รันโมเดล (LLM query swarms)
    RENDERING = "rendering"              # เรนเดอร์ 3D/VFX/วิดีโอ
    MINING = "mining"                    # พูลขุดบล็อกเชน (ช่วงว่าง)
    SIMULATION = "simulation"            # ซิมูเลชันวิทยาศาสตร์
    CLOUD_GAMING = "cloud_gaming"        # สตรีมมิ่งเกม


class NodeStatus(str, Enum):
    REGISTERED = "registered"            # ลงทะเบียนแล้ว ยังไม่ได้ยืนยัน
    STAKED = "staked"                    # วางหลักประกัน $GRID แล้ว
    ACTIVE = "active"                    # พร้อมรับงาน
    BUSY = "busy"                        # กำลังรันงาน
    SUSPENDED = "suspended"              # ถูกพัก (fraud/uptime ต่ำ)
    RETIRED = "retired"                  # ออกจากเครือข่าย


# ── Core Models ────────────────────────────────────────────────────────

@dataclass
class Node:
    """โหนด — เครื่องเจ้าของ/ร้านเน็ตที่ปล่อยพลังว่าง"""
    node_id: str
    owner_name: str
    region: str                          # ประเทศ (th/vn/ph/id...)
    gpu_model: str                       # เช่น "RTX 4090"
    vram_gb: int
    idle_hours_per_day: float
    electricity_usd_per_kwh: float = 0.15
    status: NodeStatus = NodeStatus.REGISTERED
    stake_usd: float = 0.0               # $GRID staking
    trust_score: float = 1.0             # 0-1 (AI hook ใช้ประเมิน)
    uptime_pct: float = 100.0
    joined_at: datetime = field(default_factory=_now)

    @property
    def estimated_daily_revenue(self, rate_usd_per_hour: float = 0.30) -> float:
        """ประมาณรายได้คร่าวๆ: ชั่วโมงว่าง x อัตรา — prototype (เครื่องคำนวณจริงดูหน้าเว็บ)"""
        return self.idle_hours_per_day * rate_usd_per_hour


@dataclass
class Workload:
    """งานจากลูกค้า — ถูกจัดสรรไปยังโหนด/ช่องทาง"""
    workload_id: str
    tenant_id: str
    wtype: WorkloadType
    gpu_hours_required: float
    max_latency_ms: int = 100
    priority: int = 5                    # 1 (สูงสุด) - 10
    created_at: datetime = field(default_factory=_now)


@dataclass
class Tenant:
    """ลูกค้า — B2B องค์กร (prepaid API) หรือ B2C สมาชิก"""
    tenant_id: str
    name: str
    kind: str = "b2b"                    # b2b | b2c
    api_key_hash: str = ""
    balance_usd: float = 0.0             # ยอดคงเหลือ (เติมเงินล่วงหน้า)
    created_at: datetime = field(default_factory=_now)


@dataclass
class ApiKey:
    """Prepaid API Key — เติมเงินล่วงหน้า จ่ายวินาทีต่อวินาที"""
    key_id: str
    tenant_id: str
    key_prefix: str = ""                 # เก็บเฉพาะ prefix + hash (security)
    balance_usd: float = 0.0
    active: bool = True


@dataclass
class Payout:
    """การจ่ายรายวัน — 75% ให้ผู้ให้เครื่อง (แปลงบาทได้)"""
    payout_id: str
    node_id: str
    amount_usd: float
    split_breakdown: Dict[str, float] = field(default_factory=dict)
    paid_at: datetime = field(default_factory=_now)
    tx_ref: str = ""                     # เลขธุรกรรม (chain/ธนาคาร)

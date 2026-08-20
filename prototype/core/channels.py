"""
ASEAN Grid — 5 Revenue Channels (ช่องทางรายได้)
ทุกช่องทาง implement interface `ComputeChannel` เดียวกัน → เพิ่มช่องทางใหม่ได้ไม่จำกัด
(ช่องว่างที่เว้นไว้: Akash, Lambda, Together, จีน/เกาหลี domestic clouds...)

Prototype นี้เป็น stub — ต่อ API จริงของแต่ละแพลตฟอร์มที่ TODO ระบุ
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ChannelQuote:
    """ราคา/เงื่อนไขที่สแกนได้จากช่องทางหนึ่ง"""
    channel: str
    price_usd_per_hour: float
    available_gpus: int
    queue_depth: int                     # คิวยาว = งานเยอะ = ราคาดี
    latency_ms: int
    reliability: float                   # 0-1
    currency: str = "USD"

    @property
    def score(self) -> float:
        """คะแนนดิบก่อน AI strategy ปรับ — ยิ่งสูงยิ่งน่าส่งงาน"""
        return (self.price_usd_per_hour * self.reliability
                / max(1, self.queue_depth) * (100.0 / max(1, self.latency_ms)))


class ComputeChannel(ABC):
    """Interface กลางของทุกช่องทางรายได้"""

    name: str = "base"

    @abstractmethod
    def get_quote(self) -> Optional[ChannelQuote]:
        """สแกนราคา/คิวปัจจุบันของช่องทางนี้"""

    @abstractmethod
    def submit_workload(self, workload) -> str:
        """ส่งงานเข้าช่องทาง → คืน job_id"""

    @abstractmethod
    def get_payout_estimate(self) -> float:
        """ประมาณยอดที่จะได้รับ (USD/วัน)"""


# ── 5 ช่องทาง (Core) ───────────────────────────────────────────────────

class VastAIChannel(ComputeChannel):
    """1. Vast.ai — ตลาดเช่า GPU (สแกนราคาเรียลไทม์)"""
    name = "vast_ai"

    def get_quote(self) -> Optional[ChannelQuote]:
        # TODO: GET https://vast.ai/api/v0/prices/ — ดึงราคาจริง
        return ChannelQuote("vast_ai", 0.42, 1200, 3, 35, 0.97)

    def submit_workload(self, workload) -> str:
        # TODO: POST https://vast.ai/api/v0/offers/{id}/order/
        return f"vast-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 12.50


class IoNetChannel(ComputeChannel):
    """2. io.net — เครือข่าย DePIN สำหรับ AI/ML"""
    name = "io_net"

    def get_quote(self) -> Optional[ChannelQuote]:
        # TODO: io.net API (ต้องเป็น approved supplier)
        return ChannelQuote("io_net", 0.38, 900, 5, 40, 0.95)

    def submit_workload(self, workload) -> str:
        return f"io-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 10.20


class RenderChannel(ComputeChannel):
    """3. Render Network — เรนเดอร์กราฟิก 3D/VFX"""
    name = "render"

    def get_quote(self) -> Optional[ChannelQuote]:
        # TODO: Render Network API
        return ChannelQuote("render", 0.30, 600, 2, 45, 0.96)

    def submit_workload(self, workload) -> str:
        return f"rnd-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 8.75


class DirectAIChannel(ComputeChannel):
    """4. ช่องทางตรง — บริษัท AI/ห้องแล็บ (Moonshot/Kimi, DeepSeek...) ผ่าน Prepaid API"""
    name = "direct_ai"

    def get_quote(self) -> Optional[ChannelQuote]:
        # ราคาเราตั้งเอง (B2B prepaid) — ไม่มีคู่แข่งสแกน กำไรดีที่สุด
        return ChannelQuote("direct_ai", 0.55, 9999, 0, 25, 0.99)

    def submit_workload(self, workload) -> str:
        return f"dai-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 18.00


class StudiosChannel(ComputeChannel):
    """5. สตูดิโอ/บริษัทเกม — เรนเดอร์ 4K-8K, cloud gaming"""
    name = "studios"

    def get_quote(self) -> Optional[ChannelQuote]:
        # สัญญาระยะยาว/โปรเจกต์ — ราคาคงที่
        return ChannelQuote("studios", 0.35, 300, 1, 30, 0.98)

    def submit_workload(self, workload) -> str:
        return f"std-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 9.40


# ── Registry — ลงทะเบียนช่องทาง (Dev เพิ่มช่องทางใหม่ได้ตรงนี้) ────────

CHANNEL_REGISTRY: Dict[str, ComputeChannel] = {
    "vast_ai": VastAIChannel(),
    "io_net": IoNetChannel(),
    "render": RenderChannel(),
    "direct_ai": DirectAIChannel(),
    "studios": StudiosChannel(),
}


def get_all_quotes() -> List[ChannelQuote]:
    """สแกนราคาทุกช่องทาง — เรียกโดย Arbitrage Engine"""
    return [ch.get_quote() for ch in CHANNEL_REGISTRY.values() if ch.get_quote() is not None]

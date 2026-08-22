"""
ASEAN Grid — 7 Revenue Channels (ช่องทางรายได้)
ทุกช่องทาง implement interface `ComputeChannel` เดียวกัน → เพิ่มช่องทางใหม่ได้ไม่จำกัด
(ช่องว่างที่เว้นไว้: Lambda, Together, จีน/เกาหลี domestic clouds...)

Prototype นี้เป็น stub — ต่อ API จริงของแต่ละแพลตฟอร์มที่ TODO ระบุ
(Vast.ai ต่อ API จริงแล้ว — console.vast.ai/api/v0/bundles — ราคาสดจากตลาดจริง)
"""
import json
import logging
import time
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("channels")


# ── สถานะการเชื่อมต่อช่องทาง ─────────────────────────────────────────
CONNECTED = "connected"      # ✅ เชื่อม API แล้ว พร้อมรับงานจริง
PENDING = "pending"          # ⏳ สมัคร/รออนุมัติ (ยังรับงานไม่ได้)
NOT_CONNECTED = "not_connected"  # 🔒 ยังไม่ได้เชื่อมต่อ


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
    status: str = CONNECTED              # สถานะการเชื่อมต่อ (default: พร้อมรับงาน)

    @property
    def score(self) -> float:
        """คะแนนดิบก่อน AI strategy ปรับ — ยิ่งสูงยิ่งน่าส่งงาน
        ช่องทางที่ยังเชื่อมต่อไม่ได้ (pending/not_connected) ได้คะแนน 0 — ห้ามส่งงาน"""
        if self.status != CONNECTED:
            return 0.0
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
    """1. Vast.ai — ตลาดเช่า GPU (ราคาสดจาก API จริง console.vast.ai/api/v0/bundles)
    ดึง offer ทั้งตลาด → คำนวณราคาเฉลี่ยของ GPU เกมมิ่งระดับ grid (RTX 4090)"""

    name = "vast_ai"
    VAST_API = "https://console.vast.ai/api/v0/bundles/"
    _cache: Optional[ChannelQuote] = None
    _cache_ts: float = 0.0
    CACHE_SEC: int = 60           # Smart Yield Balancer — สแกนตลาดทุก 60 วิ (กัน rate limit)

    def _fetch_live_quote(self) -> Optional[ChannelQuote]:
        """ยิง API จริง → หา offers GPU เกมมิ่ง (RTX 4090/3090/4070) → ราคาเฉลี่ย"""
        try:
            req = urllib.request.Request(self.VAST_API, headers={
                "User-Agent": "ASEAN-Grid-prototype/0.1",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            offers = data.get("offers") or []
            if not offers:
                return None

            # เลือก GPU เกมมิ่งที่ grid เราใช้จริง (RTX 4090 เป็นตัวแทนหลัก)
            gpu_keys = ("4090", "3090", "4070", "5080", "5090")
            candidates = [
                o for o in offers
                if any(g in str(o.get("gpu_name", "")) for g in gpu_keys)
                and (o.get("dph_total") or 0) > 0
            ]
            if not candidates:
                candidates = [o for o in offers if (o.get("dph_total") or 0) > 0]

            # ราคาเฉลี่ยถ่วงน้ำหนัก (เฉลี่ยตรงๆ ของ offer เดี่ยว)
            single = [o for o in candidates if (o.get("gpu_ids") is None
                                                or len(o.get("gpu_ids") or []) == 1)]
            pool = single or candidates
            avg_price = sum(o["dph_total"] for o in pool) / len(pool)
            # คิว = จำนวน offer ที่ว่างในตลาด, reliability = ฐาน 0.97 (prototype)
            return ChannelQuote(
                channel=self.name,
                price_usd_per_hour=round(avg_price, 4),
                available_gpus=len(pool),
                queue_depth=max(1, len(offers) // 10),   # ตลาดหนาแน่น
                latency_ms=35,                            # ASEAN → US (prototype)
                reliability=0.97,
            )
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, ZeroDivisionError) as e:
            logger.warning("[%s] fetch failed: %s (%s)", self.name, e, type(e).__name__)
            return None   # fallback ข้างล่าง

    def get_quote(self) -> Optional[ChannelQuote]:
        now = time.time()
        if self._cache is None or (now - self._cache_ts) > self.CACHE_SEC:
            live = self._fetch_live_quote()
            if live is not None:
                self._cache, self._cache_ts = live, now
        if self._cache is not None:
            return self._cache
        # fallback: API ล่ม/เน็ตไม่มี → ค่าจำลองเดิม
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
        return ChannelQuote("io_net", 0.38, 900, 5, 40, 0.95, status=PENDING)

    def submit_workload(self, workload) -> str:
        return f"io-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 10.20


class RenderChannel(ComputeChannel):
    """3. Render Network — เรนเดอร์กราฟิก 3D/VFX"""
    name = "render"

    def get_quote(self) -> Optional[ChannelQuote]:
        # TODO: Render Network API (ต้องเป็น node operator)
        return ChannelQuote("render", 0.30, 600, 2, 45, 0.96, status=PENDING)

    def submit_workload(self, workload) -> str:
        return f"rnd-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 8.75


class DirectAIChannel(ComputeChannel):
    """4. ช่องทางตรง — บริษัท AI/สตาร์ทอัพ/ห้องแล็บ (ผ่าน Prepaid API)"""
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


class AkashChannel(ComputeChannel):
    """6. Akash Network — ตลาดเช่า GPU กระจายศูนย์ (DePIN)
    ดึงราคา lease จริงจาก REST node ของ Akash chain (market module)
    — ลองหลาย endpoint (cosmos.directory / polkachu / official) เผื่อ node ล่ม
    ถ้าเชื่อมไม่ได้ → fallback ค่าจำลอง status=PENDING (ต้องเป็น approved tenant)
    """
    name = "akash"
    AKT_USD_EST: float = 0.15            # ราคา AKT โดยประมาณ (prototype — เปลี่ยนตามตลาด)
    BLOCK_SEC: int = 6                   # Akash block ≈ 6 วินาที → แปลงราคา/block → /ชั่วโมง
    REST_ENDPOINTS: tuple = (
        "https://rest.cosmos.directory/akash",
        "https://akash-api.polkachu.com",
        "https://api.akashnet.net",
    )
    _cache: Optional[ChannelQuote] = None
    _cache_ts: float = 0.0
    CACHE_SEC: int = 60                  # ตลาด DePIN ผันผวนช้ากว่า Vast — สแกนทุก 60 วิ

    def _fetch_live_quote(self) -> Optional[ChannelQuote]:
        """ยิง REST ของ Akash chain → นับ active leases + ราคาเฉลี่ย (uakt/block → USD/ชม.)"""
        for base in self.REST_ENDPOINTS:
            try:
                url = (f"{base}/akash/market/v1beta1/leases/list"
                       f"?state=active&pagination.limit=200")
                req = urllib.request.Request(url, headers={
                    "User-Agent": "ASEAN-Grid-prototype/0.2",
                    "Accept": "application/json",
                })
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                leases = data.get("leases") or []
                if not leases:
                    continue   # node นี้ไม่มีข้อมูล → ลอง node ถัดไป
                prices = []
                for lease in leases:
                    try:
                        price = lease.get("price") or {}
                        amt = float(price.get("amount") or 0)
                        denom = price.get("denom", "uakt")
                        usd_per_block = amt * 1e-6 * self.AKT_USD_EST if denom == "uakt" else amt
                        prices.append(usd_per_block * (3600.0 / self.BLOCK_SEC))
                    except (TypeError, ValueError):
                        continue
                if not prices:
                    continue
                avg_price = sum(prices) / len(prices)
                return ChannelQuote(
                    channel=self.name,
                    price_usd_per_hour=round(avg_price, 4),
                    available_gpus=len(leases),
                    queue_depth=max(1, len(leases) // 5),  # ตลาดหนาแน่นปานกลาง
                    latency_ms=60,                          # global mesh — สูงกว่า regional
                    reliability=0.90,                       # DePIN — ผันผวนกว่า Vast
                )
            except (urllib.error.URLError, json.JSONDecodeError, KeyError, ZeroDivisionError) as e:
                logger.debug("[%s] node skipped: %s (%s)", self.name, e, type(e).__name__)
                continue   # node ล่ม → ลอง node ถัดไป
        return None

    def get_quote(self) -> Optional[ChannelQuote]:
        now = time.time()
        if self._cache is None or (now - self._cache_ts) > self.CACHE_SEC:
            live = self._fetch_live_quote()
            if live is not None:
                self._cache, self._cache_ts = live, now
        if self._cache is not None:
            return self._cache
        # fallback: ยังไม่ได้เป็น approved tenant → สถานะรออนุมัติ (ห้ามส่งงาน)
        return ChannelQuote("akash", 0.36, 500, 4, 60, 0.90, status=PENDING)

    def submit_workload(self, workload) -> str:
        # TODO: สร้าง deployment บน Akash (SDL) แล้วรอ lease — ต้องเป็น approved tenant
        return f"akt-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 9.80


class RunPodChannel(ComputeChannel):
    """7. RunPod — คลาวด์ GPU สำหรับ AI/ML (serverless + on-demand)
    ดึงราคาจริงจาก GraphQL API — gpuTypes.lowestPrice เปิดได้โดยไม่ต้อง API key
    (minimumBidPrice = ราคาต่ำสุดต่อชั่วโมงของ GPU แต่ละรุ่น)
    """
    name = "runpod"
    GRAPHQL_URL = "https://api.runpod.io/graphql"
    QUERY = ('{"query":"{ gpuTypes { id displayName lowestPrice '
             '{ minimumBidPrice uninterruptablePrice } } }"}')
    GPU_KEYS = ("4090", "3090", "4070", "4080", "4060", "5080", "5090", "3080")
    _cache: Optional[ChannelQuote] = None
    _cache_ts: float = 0.0
    CACHE_SEC: int = 60

    def _fetch_live_quote(self) -> Optional[ChannelQuote]:
        """ยิง GraphQL → กรอง GPU เกมมิ่งที่ grid ใช้ → เฉลี่ยราคาต่ำสุด/ชม."""
        try:
            req = urllib.request.Request(
                self.GRAPHQL_URL,
                data=self.QUERY.encode("utf-8"),
                headers={"Content-Type": "application/json",
                         "User-Agent": "ASEAN-Grid-prototype/0.2"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            gpus = (data.get("data") or {}).get("gpuTypes") or []
            candidates = [
                g for g in gpus
                if any(k in str(g.get("id", "")) + str(g.get("displayName", ""))
                       for k in self.GPU_KEYS)
            ]
            prices = []
            for g in candidates:
                lp = (g.get("lowestPrice") or {})
                price = lp.get("minimumBidPrice") or lp.get("uninterruptablePrice")
                if price:
                    prices.append(float(price))
            if not prices:
                return None
            return ChannelQuote(
                channel=self.name,
                price_usd_per_hour=round(sum(prices) / len(prices), 4),
                available_gpus=len(candidates),
                queue_depth=max(1, len(prices) // 8),
                latency_ms=30,          # cloud จัดการ — latency ดีกว่า P2P
                reliability=0.96,       # managed cloud — เสถียร
            )
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, ZeroDivisionError) as e:
            logger.warning("[%s] fetch failed: %s (%s)", self.name, e, type(e).__name__)
            return None

    def get_quote(self) -> Optional[ChannelQuote]:
        now = time.time()
        if self._cache is None or (now - self._cache_ts) > self.CACHE_SEC:
            live = self._fetch_live_quote()
            if live is not None:
                self._cache, self._cache_ts = live, now
        if self._cache is not None:
            return self._cache
        # fallback: API ล่ม → สถานะรอ (ห้ามส่งงาน)
        return ChannelQuote("runpod", 0.40, 400, 4, 30, 0.96, status=PENDING)

    def submit_workload(self, workload) -> str:
        # TODO: สร้าง pod ผ่าน GraphQL mutation (ต้องมี API key)
        return f"rpd-{workload.workload_id}"

    def get_payout_estimate(self) -> float:
        return 10.50


# ── Registry — ลงทะเบียนช่องทาง (Dev เพิ่มช่องทางใหม่ได้ตรงนี้) ────────

CHANNEL_REGISTRY: Dict[str, ComputeChannel] = {
    "vast_ai": VastAIChannel(),
    "io_net": IoNetChannel(),
    "render": RenderChannel(),
    "direct_ai": DirectAIChannel(),
    "studios": StudiosChannel(),
    "akash": AkashChannel(),
    "runpod": RunPodChannel(),
}


def get_all_quotes() -> List[ChannelQuote]:
    """สแกนราคาทุกช่องทาง — เรียกโดย Arbitrage Engine
    เรียก get_quote ครั้งละ 1 รอบต่อช่องทาง (กันเปลืองทรัพยากร + ผลไม่ consistent)"""
    out: List[ChannelQuote] = []
    for ch in CHANNEL_REGISTRY.values():
        q = ch.get_quote()
        if q is not None:
            out.append(q)
    return out

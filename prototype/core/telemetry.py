"""
ASEAN Grid — Fleet Telemetry (ข้อมูลสถานะเครื่องใน fleet)
เก็บสถานะ live ของแต่ละ Node (online/health/latency/queue) → ใช้กรองก่อน schedule งาน

Node ใน models.py เก็บข้อมูลที่เปลี่ยนช้า (identity, stake, trust_score)
ส่วน telemetry.py เก็บข้อมูลที่เปลี่ยนเร็ว (สุขภาพ ณ วินาทีนี้) — คนละหน้าที่ แต่เชื่อมกันด้วย node_id
(Node in models.py holds slow-changing data; telemetry.py holds fast-changing live health,
linked to it by the shared node_id field)

เก็บข้อมูลเป็น JSON ที่ prototype/data/hosts.json (stdlib เท่านั้น ไม่ใช้ library ภายนอก)
Stores records as JSON at prototype/data/hosts.json (stdlib only, no external deps)
"""
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("telemetry")

# ── สถานะสุขภาพ GPU ─────────────────────────────────────────────────
HEALTHY = "healthy"        # ✅ ทำงานปกติ พร้อมรับงาน
DEGRADED = "degraded"      # ⚠️ ทำงานได้แต่ประสิทธิภาพลดลง (ร้อนเกิน/driver มีปัญหา)
OFFLINE = "offline"        # 🔒 ไม่ตอบสนอง ห้ามส่งงาน

DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "hosts.json"


@dataclass
class HostTelemetry:
    """สถานะของ node หนึ่งตัวใน fleet ณ เวลาที่รายงาน
    (Snapshot of a single fleet node's live status at report time)
    node_id ตรงกับ Node.node_id ใน models.py (matches Node.node_id in models.py)"""
    node_id: str
    gpu_health: str                # HEALTHY / DEGRADED / OFFLINE
    uptime_seconds: int
    latency_ms: int
    queue_depth: int
    reported_at: float = field(default_factory=time.time)

    @property
    def is_available(self) -> bool:
        """node พร้อมรับงานหรือไม่ — เฉพาะ healthy เท่านั้นที่รับงานได้
        (Whether this node can currently accept work — only healthy nodes qualify)"""
        return self.gpu_health == HEALTHY

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "HostTelemetry":
        return cls(**data)


class TelemetryCollector:
    """เก็บ/อัปเดต/อ่านข้อมูล telemetry ของทุก node ใน fleet
    (Collects, updates, and reads telemetry for every node in the fleet)

    เก็บลงไฟล์ JSON แบบง่าย — ไม่ต้องพึ่ง database ภายนอก เหมาะกับ prototype
    (Persists to a simple JSON file — no external database needed, fits a prototype)
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, dict]:
        """โหลดข้อมูลทั้งหมดจากไฟล์ — คืน dict ว่างถ้าไฟล์ไม่มีหรือเสีย
        (Load all records from disk — returns empty dict if file is missing/corrupt)"""
        if not self.registry_path.exists():
            return {}
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("[telemetry] load failed: %s (%s)", e, type(e).__name__)
            return {}

    def _save(self, records: Dict[str, dict]) -> None:
        """เขียนข้อมูลทั้งหมดกลับลงไฟล์ (Write all records back to disk)"""
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.warning("[telemetry] save failed: %s (%s)", e, type(e).__name__)

    def report(self, node_id: str, gpu_health: str, uptime_seconds: int,
               latency_ms: int, queue_depth: int) -> HostTelemetry:
        """บันทึกสถานะล่าสุดของ node หนึ่งตัว → เขียนทับข้อมูลเก่า
        (Record the latest status for one node — overwrites any prior record)"""
        record = HostTelemetry(
            node_id=node_id,
            gpu_health=gpu_health,
            uptime_seconds=uptime_seconds,
            latency_ms=latency_ms,
            queue_depth=queue_depth,
        )
        records = self._load()
        records[node_id] = record.to_dict()
        self._save(records)
        return record

    def get(self, node_id: str) -> Optional[HostTelemetry]:
        """อ่านสถานะล่าสุดของ node ตัวเดียว (Read the latest status for one node)"""
        records = self._load()
        data = records.get(node_id)
        return HostTelemetry.from_dict(data) if data else None

    def get_all(self) -> List[HostTelemetry]:
        """อ่านสถานะของทุก node ใน fleet (Read the latest status for every node)"""
        records = self._load()
        return [HostTelemetry.from_dict(d) for d in records.values()]

    def get_available_node_ids(self) -> List[str]:
        """คืนเฉพาะ node_id ที่ healthy และพร้อมรับงาน
        (Return only the node_ids that are healthy and available for work)"""
        return [h.node_id for h in self.get_all() if h.is_available]

    def filter_available(self, nodes: List) -> List:
        """
        กรอง list ของ Node (จาก models.py) ให้เหลือเฉพาะตัวที่ telemetry บอกว่า healthy
        (Filter a list of Node objects from models.py down to only the ones telemetry
        reports as healthy — this is the hook point for scheduler.py)

        Node ที่ยังไม่เคยรายงาน telemetry เลย จะถูกปล่อยผ่าน (ไม่กรองออก) — กันไม่ให้ node
        ใหม่/ยังไม่ตั้ง collector ถูกตัดสิทธิ์ทั้งหมด
        (A node with no telemetry record yet is passed through, not excluded — avoids
        locking out every node just because the collector hasn't run for it)
        """
        available_ids = set(self.get_available_node_ids())
        reported_ids = {h.node_id for h in self.get_all()}
        return [
            n for n in nodes
            if n.node_id not in reported_ids or n.node_id in available_ids
        ]

    def remove(self, node_id: str) -> None:
        """ลบ node ออกจาก registry (เช่น เมื่อเจ้าของถอนเครื่องออกจาก fleet)
        (Remove a node from the registry, e.g. when the owner withdraws it)"""
        records = self._load()
        if node_id in records:
            del records[node_id]
            self._save(records)


# ── Registry instance กลาง — ใช้ตัวเดียวกันทั้งระบบ ──────────────────
# (Shared singleton instance — used across the codebase, e.g. by scheduler.py)
HOST_REGISTRY = TelemetryCollector()
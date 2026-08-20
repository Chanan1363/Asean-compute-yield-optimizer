"""
ASEAN Grid — Genesis Ledger (บันทึกผู้บุกเบิกถาวร)
ตาม PROGRAM_GOALS E2: บันทึกสาธารณะ ถาวร แก้ไข/ลบไม่ได้ (append-only)
ชื่อผู้บุกเบิก (Genesis Builders) ทุกคนถูกจารึกที่นี่ — 3 บทบาท:
  compute / developer / ambassador
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class GenesisEntry:
    builder_name: str
    role: str                       # compute | developer | ambassador
    detail: str = ""                # เช่น GPU model / contribution / region
    joined_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    entry_hash: str = ""            # ผูกกับ entry ก่อนหน้า (chain — กันแก้ย้อนหลัง)

    def compute_hash(self, prev_hash: str) -> str:
        payload = f"{self.builder_name}|{self.role}|{self.detail}|{self.joined_at}|{prev_hash}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class GenesisLedger:
    """Ledger แบบ append-only — แต่ละ entry ผูก hash กับ entry ก่อน (เหมือน blockchain)"""

    def __init__(self):
        self._entries: List[GenesisEntry] = []
        self._prev_hash: str = "GENESIS"   # รากแรกของ chain

    def add(self, builder_name: str, role: str, detail: str = "") -> GenesisEntry:
        if role not in ("compute", "developer", "ambassador"):
            raise ValueError(f"Unknown role: {role}")
        entry = GenesisEntry(builder_name, role, detail)
        entry.entry_hash = entry.compute_hash(self._prev_hash)
        self._entries.append(entry)
        self._prev_hash = entry.entry_hash
        return entry

    @property
    def entries(self) -> List[GenesisEntry]:
        return list(self._entries)   # copy — กันแก้จากข้างนอก

    def verify(self) -> bool:
        """ตรวจความถูกต้องของ chain ทั้งหมด (กันแก้ย้อนหลัง)"""
        prev = "GENESIS"
        for e in self._entries:
            if e.entry_hash != e.compute_hash(prev):
                return False
            prev = e.entry_hash
        return True

    def export_json(self) -> str:
        return json.dumps(
            [{"name": e.builder_name, "role": e.role, "detail": e.detail,
              "joined": e.joined_at, "hash": e.entry_hash} for e in self._entries],
            ensure_ascii=False, indent=2,
        )

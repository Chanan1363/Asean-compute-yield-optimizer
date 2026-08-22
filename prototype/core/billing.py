"""
ASEAN Grid — Billing (Prepaid API Key, Pay-per-Compute)
B2B: ลูกค้าเติมเงินล่วงหน้า → สร้าง API Key → หักวินาทีต่อวินาทีตามงานจริง
"No computing, zero expenses." — ไม่ทำงาน = ไม่จ่าย
"""
import hashlib
import secrets
import time
from typing import Optional

from prototype.core.config import Config
from prototype.core.models import ApiKey, Tenant


class Billing:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._keys: dict = {}      # prototype: เก็บใน memory (จริง: DB)

    # ── Prepaid Top-up ────────────────────────────────────────────────

    def create_tenant(self, name: str, kind: str = "b2b") -> Tenant:
        return Tenant(tenant_id=f"t-{secrets.token_hex(4)}", name=name, kind=kind)

    def top_up(self, tenant: Tenant, amount_usd: float) -> float:
        """ลูกค้าเติมเงินล่วงหน้า → เราได้เงินสดล่วงหน้า (Upfront Cash Flow)"""
        if amount_usd < self.config.B2B_PREPAID_MIN_USD:
            raise ValueError(f"Minimum top-up is ${self.config.B2B_PREPAID_MIN_USD}")
        tenant.balance_usd += amount_usd
        return tenant.balance_usd

    def issue_api_key(self, tenant: Tenant) -> ApiKey:
        """สร้าง API Key — คืน raw key ให้ผู้ใช้ครั้งเดียว (ผู้ใช้ต้องเก็บไว้เอง)
        ระบบเก็บเฉพาะ hash (กันรั่ว) — raw key ไม่ถูกเก็บในระบบ"""
        raw = f"ag-{secrets.token_hex(16)}"
        key = ApiKey(
            key_id=f"k-{secrets.token_hex(4)}",
            tenant_id=tenant.tenant_id,
            key_prefix=raw[:12],
            raw_key=raw,               # คืนให้ผู้ใช้ (แสดงครั้งเดียว)
            balance_usd=tenant.balance_usd,
        )
        self._keys[key.key_id] = {"raw_hash": self._hash(raw), "tenant": tenant.tenant_id}
        return key

    @staticmethod
    def _hash(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Pay-per-Compute (วินาทีต่อวินาที) ─────────────────────────────

    def charge_seconds(self, tenant: Tenant, seconds: int, rate_usd_per_hour: float) -> float:
        """
        คิดเงินตามวินาทีจริงที่คำนวณ (micro-billing)
        seconds=0 → charge=0 (ไม่ทำงาน = ไม่จ่าย)
        """
        cost = (seconds / 3600.0) * rate_usd_per_hour
        if cost > tenant.balance_usd + 1e-9:
            raise ValueError(f"Insufficient balance: need ${cost:.4f}, have ${tenant.balance_usd:.4f}")
        tenant.balance_usd -= cost
        return cost

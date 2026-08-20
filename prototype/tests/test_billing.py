"""Test: Billing — Prepaid API + Pay-per-Compute (วินาทีต่อวินาที)"""
import unittest

from prototype.core.billing import Billing
from prototype.core.config import Config


class TestBilling(unittest.TestCase):

    def setUp(self):
        self.billing = Billing(Config())

    def test_topup_and_balance(self):
        tenant = self.billing.create_tenant("Bangkok AI Startup (test)")
        self.billing.top_up(tenant, 500.0)
        self.assertAlmostEqual(tenant.balance_usd, 500.0)

    def test_topup_below_minimum_rejected(self):
        tenant = self.billing.create_tenant("small")
        with self.assertRaises(ValueError):
            self.billing.top_up(tenant, 10.0)

    def test_charge_per_second(self):
        """1 ชั่วโมง @ $0.50/hr = $0.50; 3600 วินาที"""
        tenant = self.billing.create_tenant("dev")
        self.billing.top_up(tenant, 100.0)
        cost = self.billing.charge_seconds(tenant, 3600, 0.50)
        self.assertAlmostEqual(cost, 0.50)
        self.assertAlmostEqual(tenant.balance_usd, 99.50)

    def test_no_compute_no_charge(self):
        """ไม่ทำงาน = ไม่จ่าย (No computing, zero expenses)"""
        tenant = self.billing.create_tenant("idle")
        self.billing.top_up(tenant, 50.0)
        cost = self.billing.charge_seconds(tenant, 0, 0.50)
        self.assertAlmostEqual(cost, 0.0)
        self.assertAlmostEqual(tenant.balance_usd, 50.0)

    def test_insufficient_balance_blocks(self):
        tenant = self.billing.create_tenant("poor")
        self.billing.top_up(tenant, 50.0)
        with self.assertRaises(ValueError):
            self.billing.charge_seconds(tenant, 3600 * 200, 0.50)  # $100 > $50

    def test_api_key_hash_stored_not_raw(self):
        tenant = self.billing.create_tenant("org")
        self.billing.top_up(tenant, 100.0)
        key = self.billing.issue_api_key(tenant)
        stored = self.billing._keys[key.key_id]
        self.assertNotIn(key.key_prefix, stored["raw_hash"])   # เก็บ hash เท่านั้น


if __name__ == "__main__":
    unittest.main()

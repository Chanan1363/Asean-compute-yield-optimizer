"""Test: Revenue Split 75/20/5 (Core ยืนยันจากภาพ 18 ส.ค. 2026)"""
import unittest

from prototype.core.config import Config
from prototype.core.revenue_split import RevenueSplit


class TestRevenueSplit(unittest.TestCase):

    def setUp(self):
        self.rs = RevenueSplit(Config())

    def test_split_75_20_5(self):
        result = self.rs.split(1000.00)
        self.assertAlmostEqual(result.node_usd, 750.00)
        self.assertAlmostEqual(result.platform_usd, 200.00)
        self.assertAlmostEqual(result.developer_usd, 50.00)

    def test_split_sums_to_total(self):
        for amount in (0.01, 1.0, 1234.56, 999999.99):
            r = self.rs.split(amount)
            self.assertAlmostEqual(r.node_usd + r.platform_usd + r.developer_usd, amount)

    def test_split_never_loses_money(self):
        r = self.rs.split(0.01)   # เงินน้อยที่สุดต้องไม่สูญหาย
        self.assertAlmostEqual(r.node_usd + r.platform_usd + r.developer_usd, 0.01)

    def test_config_rejects_wrong_shares(self):
        with self.assertRaises(ValueError):
            Config(NODE_SHARE=0.5, PLATFORM_SHARE=0.3, DEVELOPER_SHARE=0.1)  # รวม = 0.9

    def test_daily_payout_thb(self):
        payout = self.rs.daily_payout(7.5, thb_rate=35.0)
        self.assertAlmostEqual(payout["usd"], 7.5)
        self.assertAlmostEqual(payout["thb"], 262.5)


if __name__ == "__main__":
    unittest.main()

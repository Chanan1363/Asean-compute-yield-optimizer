"""Test: Smart Yield Balancer — สลับงานเมื่อคุ้มจริง (threshold + overhead)"""
import unittest

from prototype.core.arbitrage import ArbitrageEngine, BalancePolicy
from prototype.core.config import Config
from prototype.ai.strategy_hooks import AIStrategy, StrategyRegistry


class TestBalancePolicy(unittest.TestCase):

    def setUp(self):
        self.policy = BalancePolicy(threshold_pct=0.15, switch_overhead_sec=180)

    def test_no_switch_when_candidate_lower(self):
        self.assertFalse(self.policy.should_switch(0.50, 0.40, 3600))

    def test_no_switch_below_threshold(self):
        # ต่างกัน 10% (< 15%) → ไม่สลับ
        self.assertFalse(self.policy.should_switch(0.50, 0.55, 3600))

    def test_switch_when_above_threshold_and_worth_it(self):
        # 0.50 → 0.60 = +20% (> 15%) และคุ้ม overhead (24 ชม. เหลือ)
        self.assertTrue(self.policy.should_switch(0.50, 0.60, 3600))

    def test_no_switch_when_overhead_not_covered(self):
        # ต่าง 20% แต่เหลือเวลาแค่ 0.1 ชม. → กำไรเพิ่ม 0.01 < overhead 0.025 → ไม่สลับ
        self.assertFalse(self.policy.should_switch(0.50, 0.60, 3600, remaining_hours=0.1))


class TestEngineBalance(unittest.TestCase):

    def test_engine_keeps_current_channel_when_not_worth(self):
        """AI แนะนำช่องทางใหม่ที่แพงกว่าเล็กน้อย (<15%) → ระบบคงช่องทางเดิม"""
        class PickIoNet(AIStrategy):
            name = "pick-io"
            def predict_best_channel(self, features):
                return "io_net"          # 0.38 vs direct_ai 0.55 → ต่ำกว่าเดิม

        StrategyRegistry.register("pick-io", PickIoNet())
        engine = ArbitrageEngine(Config(), strategy_name="pick-io")
        # จำลองว่าระบบทำงานบน direct_ai (0.55) อยู่
        engine._current_channel = "direct_ai"
        engine._current_net = 0.55
        best = engine.pick_best_channel()
        self.assertEqual(best, "direct_ai")    # อยู่กับงานเดิม — ไม่สลับลงราคา

    def test_engine_switches_when_candidate_much_better(self):
        """AI แนะนำช่องทางที่กำไรสูงกว่าชัดเจน (>15%) → สลับ"""
        class PickDirect(AIStrategy):
            name = "pick-direct"
            def predict_best_channel(self, features):
                return "direct_ai"       # 0.55 สูงสุดในตลาด

        StrategyRegistry.register("pick-direct", PickDirect())
        engine = ArbitrageEngine(Config(), strategy_name="pick-direct")
        # จำลองว่าระบบทำงานบน vast_ai (0.30 ราคาต่ำ) อยู่
        engine._current_channel = "render"
        engine._current_net = 0.30
        best = engine.pick_best_channel()
        self.assertEqual(best, "direct_ai")    # คุ้ม — สลับไปช่องทางจ่ายสูง


if __name__ == "__main__":
    unittest.main()

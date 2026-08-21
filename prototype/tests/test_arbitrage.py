"""Test: Arbitrage Engine + AI Strategy Hooks (หัวใจระบบ)"""
import unittest

from prototype.core.arbitrage import ArbitrageEngine
from prototype.core.config import Config
from prototype.core.models import Workload, WorkloadType
from prototype.ai.strategy_hooks import AIStrategy, StrategyRegistry


class TestArbitrage(unittest.TestCase):

    def setUp(self):
        self.engine = ArbitrageEngine(Config())

    def test_scan_returns_7_channels(self):
        quotes = self.engine.scan_market()
        self.assertEqual(len(quotes), 7)   # 7 ช่องทาง (Core + akash + runpod)

    def test_best_channel_is_direct_ai_by_heuristic(self):
        """direct_ai ราคา 0.55/ชม. ควรชนะด้วยคะแนน (กำไรดีสุด ไม่มีคิว)"""
        best = self.engine.pick_best_channel()
        self.assertEqual(best, "direct_ai")

    def test_route_returns_job_id(self):
        wl = Workload(workload_id="w-1", tenant_id="t-1", wtype=WorkloadType.AI_INFERENCE,
                      gpu_hours_required=2)
        job = self.engine.route(wl)
        self.assertTrue(job.startswith(("vast-", "io-", "rnd-", "dai-", "std-", "akt-", "rpd-")))

    def test_ai_strategy_hook_overrides_heuristic(self):
        """AI จูนใส่โมเดล → ระบบใช้โมเดลนั้นทันที (โดยไม่แตะ engine)"""
        class AlwaysIoNet(AIStrategy):
            name = "always-io"
            def predict_best_channel(self, features):
                return "io_net"

        StrategyRegistry.register("always-io", AlwaysIoNet())
        engine = ArbitrageEngine(Config(), strategy_name="always-io")
        self.assertEqual(engine.pick_best_channel(), "io_net")

    def test_unknown_strategy_raises(self):
        with self.assertRaises(KeyError):
            ArbitrageEngine(Config(), strategy_name="does-not-exist")


if __name__ == "__main__":
    unittest.main()

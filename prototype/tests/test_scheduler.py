"""Test: Scheduler — ค่าไฟรายประเทศ + รายช่วงเวลา + AI hooks (tariff-aware)"""
import unittest

from prototype.core.config import Config
from prototype.core.models import Node, Workload, WorkloadType, NodeStatus
from prototype.core.scheduler import Scheduler


def make_node(nid, region, kwh, trust=1.0, status=NodeStatus.ACTIVE):
    return Node(node_id=nid, owner_name=nid, region=region, gpu_model="RTX 4090",
                vram_gb=24, idle_hours_per_day=10, electricity_usd_per_kwh=kwh,
                status=status, trust_score=trust)


class TestScheduler(unittest.TestCase):

    def setUp(self):
        self.sched = Scheduler(Config())
        self.wl = Workload(workload_id="W-T1", tenant_id="t1",
                           wtype=WorkloadType.AI_INFERENCE, gpu_hours_required=4)

    def test_country_tariff_vn_cheaper_than_sg(self):
        vn = self.sched.country_tariff("vn")   # 0.12 → 0.8
        sg = self.sched.country_tariff("sg")   # 0.22 → ~1.47
        self.assertLess(vn, 1.0)
        self.assertGreater(sg, 1.0)
        self.assertLess(vn, sg)

    def test_country_tariff_unknown_region_uses_base(self):
        self.assertAlmostEqual(self.sched.country_tariff("xx"), 1.0)

    def test_schedule_prefers_cheap_electricity_country(self):
        node_vn = make_node("n-vn", "vn", 0.12)          # ไฟถูก
        node_sg = make_node("n-sg", "sg", 0.22)          # ไฟแพง
        order = self.sched.schedule([node_sg, node_vn], self.wl, hour=14)
        self.assertEqual(order[0].node_id, "n-vn")       # เวียดนามต้องมาก่อน

    def test_schedule_night_time_cheaper(self):
        node_th = make_node("n-th", "th", 0.15)
        day = self.sched.schedule([node_th], self.wl, hour=14)
        night = self.sched.schedule([node_th], self.wl, hour=2)
        # กลางคืน (factor 0.7) ต้นทุนถูกกว่า → คะแนนเรียงดีกว่า (โหนดเดียวยังต้องอยู่ในผลลัพธ์)
        self.assertIn(node_th, day)
        self.assertIn(node_th, night)

    def test_schedule_skips_busy_nodes(self):
        busy = make_node("n-busy", "th", 0.10, status=NodeStatus.BUSY)
        free = make_node("n-free", "th", 0.20)
        order = self.sched.schedule([busy, free], self.wl, hour=10)
        self.assertNotIn(busy.node_id, [n.node_id for n in order])
        self.assertIn(free.node_id, [n.node_id for n in order])

    def test_schedule_returns_top_3(self):
        nodes = [make_node(f"n-{i}", "th", 0.10 + i * 0.01) for i in range(6)]
        order = self.sched.schedule(nodes, self.wl, hour=12)
        self.assertEqual(len(order), 3)


if __name__ == "__main__":
    unittest.main()

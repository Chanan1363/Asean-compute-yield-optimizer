"""Test: Telemetry — สถานะ live ของ node ใน fleet (health/uptime/latency/queue)"""
import shutil
import tempfile
import unittest
from pathlib import Path

from prototype.core.models import Node, NodeStatus
from prototype.core.telemetry import (
    HostTelemetry, TelemetryCollector, HEALTHY, DEGRADED, OFFLINE,
)


def make_node(nid, region="th", status=NodeStatus.ACTIVE):
    return Node(node_id=nid, owner_name=nid, region=region, gpu_model="RTX 4090",
                vram_gb=24, idle_hours_per_day=10, status=status)


class TestHostTelemetry(unittest.TestCase):

    def test_is_available_when_healthy(self):
        rec = HostTelemetry(node_id="n-1", gpu_health=HEALTHY, uptime_seconds=100,
                            latency_ms=30, queue_depth=1)
        self.assertTrue(rec.is_available)

    def test_is_not_available_when_degraded_or_offline(self):
        degraded = HostTelemetry(node_id="n-1", gpu_health=DEGRADED, uptime_seconds=100,
                                 latency_ms=30, queue_depth=1)
        offline = HostTelemetry(node_id="n-2", gpu_health=OFFLINE, uptime_seconds=0,
                                latency_ms=999, queue_depth=0)
        self.assertFalse(degraded.is_available)
        self.assertFalse(offline.is_available)

    def test_to_dict_and_from_dict_round_trip(self):
        rec = HostTelemetry(node_id="n-1", gpu_health=HEALTHY, uptime_seconds=500,
                            latency_ms=25, queue_depth=2)
        restored = HostTelemetry.from_dict(rec.to_dict())
        self.assertEqual(rec, restored)


class TestTelemetryCollector(unittest.TestCase):

    def setUp(self):
        # ใช้โฟลเดอร์ชั่วคราวแยกต่างหาก — ไม่แตะ prototype/data/hosts.json จริง
        # (Use a temp folder so tests never touch the real prototype/data/hosts.json)
        self._tmp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self._tmp_dir) / "hosts.json"
        self.collector = TelemetryCollector(registry_path=self.registry_path)

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test_report_creates_registry_file(self):
        self.collector.report("n-1", HEALTHY, 100, 30, 1)
        self.assertTrue(self.registry_path.exists())

    def test_report_and_get_round_trip(self):
        self.collector.report("n-1", HEALTHY, 3600, 28, 0)
        rec = self.collector.get("n-1")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.node_id, "n-1")
        self.assertEqual(rec.gpu_health, HEALTHY)
        self.assertEqual(rec.uptime_seconds, 3600)
        self.assertEqual(rec.latency_ms, 28)
        self.assertEqual(rec.queue_depth, 0)

    def test_get_unknown_node_returns_none(self):
        self.assertIsNone(self.collector.get("does-not-exist"))

    def test_report_overwrites_previous_record(self):
        self.collector.report("n-1", HEALTHY, 100, 30, 1)
        self.collector.report("n-1", OFFLINE, 0, 999, 0)
        rec = self.collector.get("n-1")
        self.assertEqual(rec.gpu_health, OFFLINE)

    def test_get_all_returns_every_node(self):
        self.collector.report("n-1", HEALTHY, 100, 30, 1)
        self.collector.report("n-2", DEGRADED, 200, 60, 4)
        all_records = self.collector.get_all()
        self.assertEqual(len(all_records), 2)

    def test_get_all_empty_when_no_file(self):
        self.assertEqual(self.collector.get_all(), [])

    def test_get_available_node_ids_excludes_unhealthy(self):
        self.collector.report("n-1", HEALTHY, 100, 30, 1)
        self.collector.report("n-2", OFFLINE, 0, 999, 0)
        self.collector.report("n-3", DEGRADED, 50, 80, 3)
        self.assertEqual(self.collector.get_available_node_ids(), ["n-1"])

    def test_remove_deletes_node(self):
        self.collector.report("n-1", HEALTHY, 100, 30, 1)
        self.collector.remove("n-1")
        self.assertIsNone(self.collector.get("n-1"))

    def test_remove_unknown_node_does_not_raise(self):
        self.collector.remove("does-not-exist")   # ต้องไม่พัง (idempotent)

    def test_corrupt_registry_file_falls_back_to_empty(self):
        """ไฟล์ JSON เสีย → โหลดล้มเหลว → คืน list ว่างแทนที่จะ crash
        (Corrupt JSON file → load fails safely → returns empty list, doesn't crash)"""
        self.registry_path.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(self.collector.get_all(), [])


class TestFilterAvailable(unittest.TestCase):
    """test_scheduler.py จะเรียกใช้ filter_available() ก่อนเลือก candidates
    (scheduler.py calls filter_available() before choosing candidates)"""

    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self._tmp_dir) / "hosts.json"
        self.collector = TelemetryCollector(registry_path=self.registry_path)

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test_filters_out_offline_nodes(self):
        healthy = make_node("n-healthy")
        offline = make_node("n-offline")
        self.collector.report("n-healthy", HEALTHY, 100, 30, 1)
        self.collector.report("n-offline", OFFLINE, 0, 999, 0)

        result = self.collector.filter_available([healthy, offline])
        self.assertIn(healthy, result)
        self.assertNotIn(offline, result)

    def test_nodes_with_no_telemetry_pass_through(self):
        """node ที่ยังไม่เคยรายงาน telemetry เลย ต้องไม่ถูกกรองออก (กัน node ใหม่ถูกตัดสิทธิ์)
        (A node with no telemetry report yet must not be excluded — protects new nodes)"""
        unreported = make_node("n-new")
        result = self.collector.filter_available([unreported])
        self.assertIn(unreported, result)

    def test_empty_node_list_returns_empty(self):
        self.assertEqual(self.collector.filter_available([]), [])

    def test_mixed_healthy_offline_and_unreported(self):
        healthy = make_node("n-healthy")
        offline = make_node("n-offline")
        unreported = make_node("n-new")
        self.collector.report("n-healthy", HEALTHY, 100, 30, 1)
        self.collector.report("n-offline", OFFLINE, 0, 999, 0)

        result = self.collector.filter_available([healthy, offline, unreported])
        result_ids = [n.node_id for n in result]
        self.assertIn("n-healthy", result_ids)
        self.assertIn("n-new", result_ids)
        self.assertNotIn("n-offline", result_ids)


if __name__ == "__main__":
    unittest.main()
"""Test: Channels — registry 6 ช่องทาง + Akash channel (#6) fallback ปลอดภัย"""
import unittest

from prototype.core.channels import (
    CHANNEL_REGISTRY, AkashChannel, CONNECTED, PENDING,
)


class TestChannels(unittest.TestCase):

    def test_registry_has_six_channels(self):
        self.assertEqual(len(CHANNEL_REGISTRY), 6)

    def test_akash_registered(self):
        self.assertIn("akash", CHANNEL_REGISTRY)
        self.assertIsInstance(CHANNEL_REGISTRY["akash"], AkashChannel)

    def test_akash_quote_never_none(self):
        """Akash ต้องคืน quote เสมอ — fallback ปลอดภัย (PENDING = ห้ามส่งงาน)"""
        q = AkashChannel().get_quote()
        self.assertIsNotNone(q)
        self.assertEqual(q.channel, "akash")
        self.assertIn(q.status, (CONNECTED, PENDING))

    def test_akash_fallback_has_zero_score(self):
        """ช่องทางที่ยังไม่เชื่อมต่อ (PENDING) ต้องได้คะแนน 0 — ห้ามส่งงาน"""
        fallback = AkashChannel().get_quote()
        if fallback.status == PENDING:
            self.assertEqual(fallback.score, 0.0)

    def test_akash_submit_returns_job_id(self):
        class FakeWL:
            workload_id = "W-AKASH-1"
        self.assertEqual(CHANNEL_REGISTRY["akash"].submit_workload(FakeWL()),
                         "akt-W-AKASH-1")

    def test_all_quotes_include_akash(self):
        from prototype.core.channels import get_all_quotes
        names = [q.channel for q in get_all_quotes()]
        self.assertIn("akash", names)


if __name__ == "__main__":
    unittest.main()

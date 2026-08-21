"""Test: Sandbox — orchestrator ต้องรันได้เสมอ (fallback stub) + lifecycle ครบ"""
import unittest

from prototype.core.sandbox import (
    SandboxSpec, DockerSandboxStub, get_orchestrator, DOCKER_SDK_AVAILABLE,
)


class FakeWorkload:
    workload_id = "W-SBX-1"
    command = "echo hello"


class TestSandbox(unittest.TestCase):

    def test_get_orchestrator_always_available(self):
        """เครื่องที่ไม่มี Docker ต้องได้ stub — โปรแกรมรันได้เสมอ"""
        orch = get_orchestrator()
        self.assertTrue(hasattr(orch, "create_sandbox"))

    def test_lifecycle_create_run_verify_destroy(self):
        orch = get_orchestrator()
        spec = SandboxSpec(image="nvidia/cuda:12.4-runtime", memory_gb=8)
        sid = orch.create_sandbox(spec, FakeWorkload())
        self.assertTrue(sid.startswith("sbx-"))
        # verify ก่อนรัน (เกณฑ์ข้อ 1: ตรวจแยกขาดก่อนทำงาน)
        self.assertTrue(orch.verify_isolation(sid))
        result = orch.run_workload(sid, FakeWorkload())
        self.assertIn("run-ok", result)
        orch.destroy_sandbox(sid)
        self.assertFalse(orch.verify_isolation(sid))

    def test_stub_unknown_sandbox_fails_verify(self):
        stub = DockerSandboxStub()
        self.assertFalse(stub.verify_isolation("sbx-does-not-exist"))

    def test_stub_destroy_is_idempotent(self):
        stub = DockerSandboxStub()
        spec = SandboxSpec(image="img")
        sid = stub.create_sandbox(spec, FakeWorkload())
        stub.destroy_sandbox(sid)
        stub.destroy_sandbox(sid)   # ลบซ้ำต้องไม่พัง


if __name__ == "__main__":
    unittest.main()

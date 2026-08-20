"""
ASEAN Grid — One-Click Docker Sandbox (ความปลอดภัย)
งานลูกค้าทุกรันในกล่องแยก — หนีออกมาควบคุมเครื่องเจ้าของไม่ได้
Private Data Protected: ข้อมูลส่วนตัวแยกขาดจากงานลูกค้า

Prototype: interface + stub — Dev ต่อ Docker/K8s จริงที่ TODO
Security Goals (PROGRAM_GOALS C1/C2): escape = 0 ตลอดไป
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class SandboxSpec:
    """สเปกกล่องสำหรับงานหนึ่ง"""
    image: str                          # เช่น "nvidia/cuda:12.4-runtime"
    gpu_required: int = 1
    memory_gb: int = 16
    network_isolated: bool = True       # แยกเน็ตจากโฮสต์
    host_fs_readonly: bool = True       # โฮสต์มองเห็นแบบ read-only (กันรั่วข้อมูล)
    max_run_seconds: int = 86400
    seccomp_profile: str = "default"    # จำกัด syscall


class SandboxOrchestrator(ABC):
    """Interface: ทุก runtime (docker/podman/k8s) ต้อง implement นี้"""

    @abstractmethod
    def create_sandbox(self, spec: SandboxSpec, workload) -> str:
        """สร้างกล่อง → คืน sandbox_id"""

    @abstractmethod
    def run_workload(self, sandbox_id: str, workload) -> str:
        """รันงานในกล่อง → คืน log/result ref"""

    @abstractmethod
    def destroy_sandbox(self, sandbox_id: str) -> None:
        """ทำลายกล่องหลังจบงาน (ไม่เหลือร่องรอย)"""

    @abstractmethod
    def verify_isolation(self, sandbox_id: str) -> bool:
        """ตรวจว่าแยกขาดจริง (เรียกทุกครั้งก่อนรันงาน)"""


class DockerSandboxStub(SandboxOrchestrator):
    """
    Stub สำหรับ prototype — Dev ต่อ docker SDK จริงที่ TODO
    หลัก: create → verify_isolation → run → destroy
    """

    def __init__(self):
        self._sandboxes: dict = {}

    def create_sandbox(self, spec: SandboxSpec, workload) -> str:
        # TODO: docker.from_env().containers.run(... detach=True)
        sid = f"sbx-{workload.workload_id}"
        self._sandboxes[sid] = {"spec": spec, "status": "created"}
        return sid

    def run_workload(self, sandbox_id: str, workload) -> str:
        # TODO: รันจริง + เก็บ log
        return f"run-ok:{workload.workload_id}"

    def destroy_sandbox(self, sandbox_id: str) -> None:
        self._sandboxes.pop(sandbox_id, None)

    def verify_isolation(self, sandbox_id: str) -> bool:
        # TODO: ตรวจ cgroup/namespace/seccomp จริง — prototype คืน True
        return sandbox_id in self._sandboxes

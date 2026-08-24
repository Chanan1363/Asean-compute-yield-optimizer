"""
ASEAN Grid — REST API (FastAPI)
โครงสร้าง endpoint หลัก — Dev ต่อยอดได้ทันที (ดู ai/prompts/agents.md ข้อ 4)

รัน: uvicorn prototype.api.app:app --reload  (ต้อง pip install fastapi uvicorn)
"""
import time
from typing import Dict, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover — prototype รันโดยไม่ต้องมี fastapi ก็ได้
    _FASTAPI_AVAILABLE = False
    FastAPI = object

from prototype.core.config import Config
from prototype.core.revenue_split import RevenueSplit
from prototype.core.arbitrage import ArbitrageEngine
from prototype.core.genesis import GenesisLedger
from prototype.core import db as node_db

app = FastAPI(title="ASEAN Grid API", version="0.1.0") if _FASTAPI_AVAILABLE else None

_config = Config()
_split = RevenueSplit(_config)
_engine = ArbitrageEngine(_config)
_ledger = GenesisLedger()


if _FASTAPI_AVAILABLE:

    class SplitRequest(BaseModel):
        amount_usd: float

    class BuilderRequest(BaseModel):
        name: str
        role: str          # compute | developer | ambassador
        detail: str = ""

    class EstimateRequest(BaseModel):
        gpu_hours: float
        rate_usd_per_hour: float = 0.0   # 0 = ใช้ราคาช่องทางที่ดีที่สุดตอนนี้

    @app.get("/", include_in_schema=False)
    def landing() -> FileResponse:
        """หน้าแรกกลาง — หนึ่ง URL หลายบทบาท (portal/supply/docs/dashboard)"""
        return FileResponse("prototype/landing.html")

    @app.get("/portal", include_in_schema=False)
    def portal() -> FileResponse:
        """หน้า Customer Portal — มุมมองลูกค้า (Demand)"""
        return FileResponse("prototype/customer_portal.html")

    @app.get("/health")
    def health() -> Dict[str, str]:
        """สถานะระบบ + รายงาน DB backend (postgres/sqlite) + driver จริง"""
        try:
            import pg8000
            driver = f"pg8000 {pg8000.__version__}"
        except Exception:
            driver = "MISSING"
        return {"status": "ok", "region": _config.REGION,
                "db": "postgres" if node_db.DATABASE_URL else "sqlite",
                "driver": driver}

    @app.get("/market")
    def market() -> Dict:
        """สแกนราคาทุกช่องทาง (Arbitrage Engine) — รวมคะแนน AI strategy"""
        quotes = []
        for q in _engine.scan_market():
            item = q.__dict__.copy()
            item["score"] = round(q.score, 4)   # score เป็น property — ต้องคำนวณส่งออกเอง
            quotes.append(item)
        return {"quotes": quotes}

    @app.get("/market/best")
    def best_channel() -> Dict:
        """ช่องทางที่จ่ายสูงสุดตอนนี้ (ผ่าน AI strategy)"""
        return {"best": _engine.pick_best_channel()}

    @app.get("/market/channels")
    def channels_status() -> Dict:
        """สถานะทุกช่องทาง (พร้อมรับงาน / รออนุมัติ / ออฟไลน์) + ราคาล่าสุด"""
        from prototype.core.channels import CHANNEL_REGISTRY
        out = []
        for name, ch in CHANNEL_REGISTRY.items():
            q = ch.get_quote()
            out.append({
                "channel": name,
                "status": q.status if q else "offline",
                "price_usd_per_hour": q.price_usd_per_hour if q else None,
                "available_gpus": q.available_gpus if q else 0,
                "latency_ms": q.latency_ms if q else None,
            })
        return {"channels": out}

    @app.post("/workload/estimate")
    def workload_estimate(req: EstimateRequest) -> Dict:
        """ประมาณราคางาน: gpu_hours x อัตรา (หรือราคา best channel) + แบ่ง 75/20/5"""
        if req.gpu_hours <= 0:
            raise HTTPException(400, "gpu_hours must be positive")
        rate = req.rate_usd_per_hour
        if rate <= 0:
            best = _engine.pick_best_channel()
            quote = next((q for q in _engine.scan_market() if q.channel == best), None)
            rate = quote.price_usd_per_hour if quote else 0.30
        total = req.gpu_hours * rate
        split = _split.split(total)
        return {
            "gpu_hours": req.gpu_hours,
            "rate_usd_per_hour": round(rate, 4),
            "total_usd": round(total, 4),
            "split": split.breakdown,
            "note": "pay-per-compute: no computing, zero expenses",
        }

    @app.post("/revenue/split")
    def revenue_split(req: SplitRequest) -> Dict:
        """แบ่งรายได้ 75/20/5 — ตรรกะเดียวกับ smart contract"""
        if req.amount_usd <= 0:
            raise HTTPException(400, "amount must be positive")
        return _split.split(req.amount_usd).breakdown

    @app.post("/genesis/builders")
    def add_builder(req: BuilderRequest) -> Dict:
        """จารึกชื่อผู้บุกเบิก (Genesis Ledger — append-only)"""
        entry = _ledger.add(req.name, req.role, req.detail)
        return {"added": True, "entry_hash": entry.entry_hash, "verify": _ledger.verify()}


    # ── Node Agent v0 (Supply Side) — เกมเมอร์ลงทะเบียน + ส่งชีพจร ──
    class NodeRegisterRequest(BaseModel):
        name: str = "gamer-pc"
        gpu_model: str = "unknown"
        region: str = "th"

    class NodeStatusRequest(BaseModel):
        node_id: str
        gpu_util_pct: float = 0.0
        cpu_load_pct: float = 0.0
        uptime_sec: int = 0

    _node_counter = 0

    @app.post("/nodes/register")
    def node_register(req: NodeRegisterRequest) -> Dict:
        """เกมเมอร์ลงทะเบียนเครื่อง -> ได้ node_id"""
        global _node_counter
        existing = node_db.all_nodes()
        _node_counter = max((int(n["node_id"][1:]) for n in existing), default=0)
        _node_counter += 1
        node_id = f"n{_node_counter:03d}"
        node_db.register(node_id, req.name, req.gpu_model, req.region)
        return {"node_id": node_id, "registered": True}

    @app.post("/nodes/status")
    def node_status(req: NodeStatusRequest) -> Dict:
        """เกมเมอร์ส่งชีพจร (ทุก 60 วิ)"""
        if not node_db.exists(req.node_id):
            raise HTTPException(404, "node not found - register first")
        node_db.update_status(req.node_id, req.gpu_util_pct, req.uptime_sec)
        return {"ok": True, "node_id": req.node_id}

    @app.get("/supply")
    def supply_page() -> FileResponse:
        """หน้า Node Monitor (ฝั่ง Supply — UI การ์ดโหนด)"""
        return FileResponse("prototype/nodes.html")

    @app.get("/nodes")
    def node_list() -> Dict:
        """ดูโหนดทั้งหมด (จาก SQLite — อยู่ถาวร)"""
        return {"nodes": node_db.all_nodes()}
    # ── Job Pipeline v0.5 — ลูกค้าส่งงาน → โหนดรับ → รัน → ผล (design: docs/NODE_AGENT_V05_DESIGN.md) ──
    class JobCreateRequest(BaseModel):
        job_type: str = "DEMO"
        gpu_model: str = "any"
        gpu_count: int = 1
        hours: float = 1.0
        payload: dict = {}

    class JobNodeRequest(BaseModel):
        node_id: str

    class JobResultRequest(BaseModel):
        node_id: str
        result: dict = {}
        elapsed_sec: float = 0.0

    @app.post("/jobs")
    def job_create(req: JobCreateRequest) -> Dict:
        """ลูกค้าส่งงานใหม่ -> queued (โหนดจะมารับอัตโนมัติ)"""
        job_id = node_db.create_job(req.job_type, req.gpu_model, req.gpu_count, req.hours, req.payload)
        return {"job_id": job_id, "status": "queued", "note": "job queued — node will pick it up"}

    @app.get("/jobs")
    def job_list() -> Dict:
        """งานทั้งหมด (ล่าสุดก่อน) — ลูกค้า/admin ดู"""
        return {"jobs": node_db.all_jobs()}

    @app.get("/jobs/{job_id}")
    def job_get(job_id: str) -> Dict:
        """ดูสถานะงานเดียว (รอ/รัน/เสร็จ + ผล)"""
        job = node_db.get_job(job_id)
        if not job:
            raise HTTPException(404, "job not found")
        return job

    @app.post("/jobs/next")
    def job_next(req: JobNodeRequest) -> Dict:
        """โหนดขอรับงาน (poll): ได้งาน queued -> assigned -> คืนให้โหนด"""
        if not node_db.exists(req.node_id):
            raise HTTPException(404, "node not found - register first")
        node_db.requeue_stale()
        job = node_db.claim_next_job(req.node_id)
        return {"job": job} if job else {"job": None}

    @app.post("/jobs/{job_id}/start")
    def job_start(job_id: str, req: JobNodeRequest) -> Dict:
        """โหนดยืนยันเริ่มรัน (assigned -> running)"""
        node_db.mark_running(job_id, req.node_id)
        return {"ok": True, "job_id": job_id, "status": "running"}

    @app.post("/jobs/{job_id}/result")
    def job_result(job_id: str, req: JobResultRequest) -> Dict:
        """โหนดส่งผลงาน -> done (เฉพาะโหนดเจ้าของงาน)"""
        if not node_db.submit_result(job_id, req.node_id, req.result, req.elapsed_sec):
            raise HTTPException(403, "not this job's node")
        return {"ok": True, "job_id": job_id, "status": "done"}

    @app.post("/jobs/{job_id}/fail")
    def job_fail(job_id: str, req: JobNodeRequest) -> Dict:
        """โหนดแจ้งงานล้มเหลว -> failed (requeue_stale คุ้มครองค้างอยู่แล้ว)"""
        node_db.fail_job(job_id, req.node_id)
        return {"ok": True, "job_id": job_id, "status": "failed"}

    @app.get("/genesis/ledger")
    def genesis() -> Dict:
        return {"entries": _ledger.entries, "chain_valid": _ledger.verify()}

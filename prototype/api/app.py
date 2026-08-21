"""
ASEAN Grid — REST API (FastAPI)
โครงสร้าง endpoint หลัก — Dev ต่อยอดได้ทันที (ดู ai/prompts/agents.md ข้อ 4)

รัน: uvicorn prototype.api.app:app --reload  (ต้อง pip install fastapi uvicorn)
"""
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
    def portal() -> FileResponse:
        """หน้า Customer Portal — มุมมองลูกค้า (UI สวยงาม)"""
        return FileResponse("prototype/customer_portal.html")

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "region": _config.REGION}

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

    @app.get("/genesis/ledger")
    def genesis() -> Dict:
        return {"entries": _ledger.entries, "chain_valid": _ledger.verify()}

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

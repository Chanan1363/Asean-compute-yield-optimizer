# ⚡ ASEAN Grid — Program Prototype (v1.3.1-demo) [![Version](https://img.shields.io/badge/version-1.3.1--demo-cyan)](../VERSION.md)

> **The Anti-Fragile, Decentralized GPU Yield Optimizer for Southeast Asia — Program Prototype.**
> ต้นแบบโปรแกรม (Program Prototype) ของ The ASEAN Grid — สร้างจากความรู้ทั้งหมดของโปรเจกต์ (Blueprint v8, PROGRAM_GOALS, Core 75/20/5 + Nous Alignment (DisTrO/Psyche)) ออกแบบให้ **AI จูนนิ่ง (fine-tuning) ใส่เข้าไปได้** และ **Dev ทั่วโลก fork ต่อยอดได้**

---

## 🆕 What's New — v1.3 (23 Aug 2026)

| ของใหม่ | ที่ไหน |
|---|---|
| 🧬 **Nous Alignment Plan** (Part A เทคนิค + B เงิน — align DisTrO/Psyche) | [docs/NOUS_ALIGNMENT.md](../docs/NOUS_ALIGNMENT.md) |
| 💰 **RevenueSplitV2** (points + permissionless claim + collateral) | [contracts/RevenueSplitV2.sol](contracts/RevenueSplitV2.sol) |
| 🧪 **DeMo Proof PASS** — Level 1 (GPU) + Level 2 (multi-process 2 & 4 workers) | [docs/DEMO_PROOF.md](../docs/DEMO_PROOF.md) |
| 📘 **Blueprint v8** | [The_ASEAN_Grid_Blueprint_v8.md](../The_ASEAN_Grid_Blueprint_v8.md) |
| 📝 **VERSION.md** (version log + bump checklist) | [VERSION.md](../VERSION.md) |

---

## 🌍 Why This Prototype, Right Now — ทำไมต้องเป็นตอนนี้ (สิงหาคม 2026)

| Global situation / สถานการณ์โลกปัจจุบัน | Impact on design / ผลกระทบต่อการออกแบบ |
|---|---|
| **Global Compute Crisis** — big data centers hit walls (power/weather/chip embargo) / data center ใหญ่ชนกำแพง (ค่าไฟ/สภาพอากาศ/embargo ชิป) | Must be "light-asset" — no new data centers, use idle power that exists / ต้องเป็น light-asset ไม่สร้าง data center ใช้พลังว่างที่มีอยู่ |
| **AI demand exploding** (training + inference + agentic AI) / AI demand ระเบิด | Support all workload types: training / inference / rendering / mining / simulation / รองรับงานหลายประเภท |
| **DePIN matured** (Vast.ai, io.net, Render, Akash, RunPod) but no smart broker for ASEAN yet / DePIN โตแล้ว แต่ยังไม่มีตัวกลางอัจฉริยะสำหรับอาเซียน | **Arbitrage Engine** across 7 channels = unique selling point / จุดขายไม่ซ้ำใคร |
| **Geopolitics:** ASEAN sits next to the biggest AI demand (China/Korea/Japan) / ภูมิรัฐศาสตร์: อาเซียนติดดีมานด์ AI ใหญ่สุด | 20-40ms latency pipeline = the moat / latency 20-40ms pipeline เป็น moat |
| **AI fine-tuning** is now mainstream / AI fine-tuning กลายเป็นของธรรมดา | Every decision point is an **AI Hook** — plug your own tuned model in / ทุกจุดตัดสินใจในระบบออกแบบเป็น AI Hook — ใส่โมเดลจูนเองได้ |

---

## 🏗️ Architecture at a Glance — สถาปัตยกรรมโดยย่อ

![ASEAN Grid Prototype Architecture](../assets/prototype_architecture.png)

*System overview: Global Tenants → API/Billing → Arbitrage Engine (AI hooks) → 7 channels → Scheduler → Docker Sandbox → Home GPU Nodes → Revenue Split 75/20/5 → Genesis Ledger. / ภาพรวมระบบ: ลูกค้าโลก → API/บิลลิ่ง → สมอง Arbitrage (AI) → 7 ช่องทาง → จัดคิว → Sandbox → เครื่องเจ้าของ → แบ่งรายได้ 75/20/5 → บันทึกถาวร*

```
[ GLOBAL TENANTS ]  (AI Labs / Studios / Game Cos. / Devs)
        │  จ่าย USD/Crypto — Prepaid API Key
        ▼
[ API GATEWAY ] ──→ [ BILLING (pay-per-second) ] ──→ [ LEDGER ]
        │
        ▼
[ ARBITRAGE ENGINE ]  ←── AI STRATEGY HOOK (จูนได้)
   │   │   │
   ▼   ▼   ▼
[Vast.ai] [io.net] [Render] [Direct AI] [Studios] [Akash] [RunPod]   ← 7 ช่องทาง (pluggable)
        │
        ▼
[ SCHEDULER ]  (ค่าไฟ/เวลา/ความน่าเชื่อถือ — tariff-aware)
        │
        ▼
[ SMART YIELD BALANCER ]  (สลับงานเมื่อคุ้มจริง: >15% + คุ้ม overhead — One-Click & Forget)
        │
        ▼
[ NODE ORCHESTRATOR ] ──→ [ DOCKER SANDBOX ] ──→ [ HOME GPU / INTERNET CAFE NODES ]
        │
        ▼
[ REVENUE SPLIT 75/20/5 ] (Smart Contract interface) → ผู้ให้เครื่อง 75% / ระบบ 20% / Dev 5%
        │
        ▼
[ GENESIS LEDGER ] (บันทึกผู้บุกเบิกถาวร — append-only)
```

---

## 📦 โครงสร้างโปรเจกต์ (Project Structure)

```
prototype/
├── README.md               ← ไฟล์นี้ — เริ่มต้นจากตรงนี้
├── architecture.md         ← สถาปัตยกรรมละเอียด + จุดต่อขยายทุกจุด
├── requirements.txt        ← deps (fastapi/uvicorn/pydantic — ทั้งหมด optional)
├── demo.py                 ← รันคำสั่งเดียว: python prototype/demo.py — เห็นทั้งระบบทำงาน
├── dashboard.py            ← Live Dashboard (Streamlit) — ราคาช่องทางสด + 75/20/5 (โชว์เดโม)
├── requirements-dashboard.txt ← deps สำหรับ dashboard (streamlit/pandas — venv แยก)
├── customer_portal.html    ← หน้าเว็บลูกค้า (UI สวยงาม — เสิร์ฟโดย FastAPI ที่ /)
│
├── core/                   ← แกนระบบ (Python 3.11, stdlib เป็นหลัก)
│   ├── config.py           ← ค่าตั้งศูนย์กลาง (75/20/5, fees, timeouts)
│   ├── models.py           ← Data models: Node, Workload, Tenant, ApiKey, Payout
│   ├── channels.py         ← 7 ช่องทางรายได้ (Vast/RunPod = API จริง / Akash = REST จริง + fallback)
│   ├── arbitrage.py        ← Arbitrage Engine + Strategy interface
│   ├── scheduler.py        ← จัดคิวงาน (tariff-aware)
│   ├── billing.py          ← Prepaid API + จ่ายวินาทีต่อวินาที
│   ├── revenue_split.py    ← แบ่งรายได้ 75/20/5 (Smart Contract interface)
│   ├── sandbox.py          ← Docker Sandbox (จริงเมื่อมี runtime — fallback stub อัตโนมัติ)
│   └── genesis.py          ← บันทึกผู้บุกเบิก (append-only registry)
│
├── ai/                     ← 🧠 จุดที่ AI จูนนิ่งใส่ได้ (THE AI HOOKS)
│   ├── strategy_hooks.py   ← AIStrategy interface + registry (pluggable)
│   ├── fine_tune/          ← จุดเตรียม data + train สำหรับ AI จูน
│   │   ├── dataset_schema.md   ← schema ของ training data
│   │   ├── build_dataset.py    ← สร้าง dataset จริง (ดึงราคา Vast.ai API)
│   │   ├── dataset.jsonl       ← dataset 72 rows (สร้างแล้ว — ราคาสด)
│   │   └── trainer.py          ← เทรนโมเดลแรก (data-driven) → register อัตโนมัติ
│   └── prompts/            ← prompts สำหรับ AI dev agents
│       └── agents.md
│
├── api/                    ← REST API (FastAPI — optional dep)
│   └── app.py
│
├── contracts/              ← Smart Contract (implementation จริง — compile ด้วย solc ผ่าน)
│   └── RevenueSplit.sol    ← 75/20/5 + batchPayout + claim (CEI — กัน reentrancy)
│
└── tests/                  ← unittest — รันได้ทันที ไม่ต้องติดตั้งอะไร
    ├── test_revenue_split.py
    ├── test_billing.py
    ├── test_arbitrage.py
    ├── test_channels.py      ← 7 ช่องทาง + Akash/RunPod fallback
    ├── test_scheduler.py     ← ค่าไฟรายประเทศ/ช่วงเวลา
    └── test_sandbox.py       ← lifecycle sandbox (fallback เสมอ)
```

---

## 🚀 เริ่มต้นใช้งาน (Quick Start)

> **English:** Everything below runs with pure Python stdlib — nothing to install for the core.
> **ไทย:** ทุกคำสั่งด้านล่างใช้ stdlib ล้วน — ไม่ต้องติดตั้งอะไรสำหรับแกนระบบ

```bash
# 1. Test the core system (stdlib only — nothing to install)
#    ทดสอบระบบแกน (ไม่ต้องติดตั้งอะไร — stdlib ล้วน)
python -m unittest discover -s prototype/tests -v

# 2. Try the Arbitrage Engine + see the revenue split
#    ทดลอง Arbitrage Engine + ดูสัดส่วนรายได้
python - <<'EOF'
from prototype.core.config import Config
from prototype.core.revenue_split import RevenueSplit

cfg = Config()
rs = RevenueSplit(cfg)
result = rs.split(1000.00)          # customer pays 1,000 USD / ลูกค้าจ่าย 1,000 USD
print(result)                        # {'node': 750.0, 'platform': 200.0, 'developer': 50.0}
EOF

# 3. (Optional) Live Dashboard (Streamlit) — live channel prices + 75/20/5 split
#    (Optional) รัน Live Dashboard (Streamlit) — ราคาสด + แบ่งรายได้ 75/20/5
# uv venv .venv-dashboard --python 3.11
# uv pip install --python .venv-dashboard/Scripts/python.exe -r prototype/requirements-dashboard.txt
# .venv-dashboard\Scripts\streamlit run prototype/dashboard.py
# แล้วเปิด http://localhost:8501 — ดูราคาทุกช่องทางสด / ช่องทางที่ดีที่สุด / สไลด์แบ่งรายได้

# 4. (Optional) Customer Portal web UI — requires fastapi/uvicorn
#    (Optional) รันเว็บ Customer Portal — ต้องติดตั้ง fastapi/uvicorn
# pip install fastapi uvicorn
# uvicorn prototype.api.app:app --reload
# แล้วเปิด http://127.0.0.1:8000/ — หน้าเว็บลูกค้า (ดูราคาสด/คำนวณรายได้/จารึกชื่อ)
```

---

## 🧠 AI Hooks — จุดที่ "AI จูนนิ่ง" ใส่เข้าไปได้ (หัวใจของ prototype)
## 🧠 AI Hooks — where your fine-tuned AI plugs in (the heart of the prototype)

> **English:** Every key decision point is an AI plugin. Bring your own tuned model — plug it in without touching the core.
> **ไทย:** ระบบออกแบบให้จุดตัดสินใจสำคัญ **เป็นปลั๊กอิน AI** — ทีม/Dev คนใดมีโมเดลจูนของตัวเอง ใส่ได้ทันทีโดยไม่แตะแกนระบบ

| Hook | จุดแทรก (Insertion point) | ใส่โมเดลอะไรได้ (Model options) |
|---|---|---|
| **Channel Selection** | `AIStrategy.predict_best_channel(features)` | Model that predicts the highest-paying channel (train on historical prices) / โมเดลพยากรณ์ช่องทางจ่ายสูงสุด (เทรนจากราคาประวัติ) |
| **Pricing** | `AIStrategy.predict_price_curve(hour, region)` | GPU price forecasting model / โมเดลคาดการณ์ราคา GPU ล่วงหน้า |
| **Fraud / Node Trust** | `AIStrategy.score_node_trust(node)` | Node reliability scorer (anti-fraud) / โมเดลให้คะแนนความน่าเชื่อถือโหนด (กันโกง) |
| **Demand Forecast** | `AIStrategy.forecast_demand(region, window)` | Demand forecasting → schedule ahead / โมเดลพยากรณ์ดีมานด์ → จัดคิวล่วงหน้า |
| **Workload Routing** | `AIStrategy.route_workload(workload, nodes)` | Route by latency/price/risk / โมเดลเลือกเส้นทางงานตาม latency/ราคา/ความเสี่ยง |

**How to plug in your model / วิธีใส่โมเดลของคุณ:**
1. See `ai/fine_tune/dataset_schema.md` — schema for building training data / ดู schema สำหรับสร้าง training data
2. Train with `ai/fine_tune/trainer.py` (first data-driven model — real dataset included) or your own pipeline / เทรนด้วย trainer.py (โมเดลแรก data-driven — มี dataset จริงแล้ว) หรือ pipeline ของคุณเอง
3. Implement `AIStrategy` (see `ai/strategy_hooks.py`) then register / implement `AIStrategy` แล้วลงทะเบียน:
```python
from prototype.ai.strategy_hooks import StrategyRegistry, AIStrategy

class MyTunedStrategy(AIStrategy):
    def predict_best_channel(self, features):
        return "io.net"  # ← ใส่โมเดลคุณตรงนี้ / plug your model here

StrategyRegistry.register("my-tuned", MyTunedStrategy())
```

---

## 🔌 Dev Hooks — จุดที่ Dev ทั่วโลกต่อยอดได้ (where developers extend)

> **English:** Intentional extension points — grab one and open a PR. AGPL-3.0: fork, modify, contribute. The 5% Developer Treasury rewards core maintainers.
> **ไทย:** จุดต่อยอดที่ตั้งใจเว้นไว้ — เลือกได้เลยแล้วส่ง PR ภายใต้ AGPL-3.0 (5% Developer Treasury สำหรับผู้รักษาแกนกริด)

| Extension point / ช่องว่างที่ตั้งใจเว้นไว้ | How to extend / วิธีต่อยอด |
|---|---|
| `core/channels.py` | ✅ 7 channels live (Vast/RunPod real API, Akash REST) — add #8 (Lambda, Together...) via the same interface / เพิ่มช่องทางใหม่ตาม interface เดิม |
| `core/sandbox.py` | ✅ Real Docker (needs docker runtime) — extend to K8s/podman / ต่อ K8s/podman ต่อได้ |
| `contracts/RevenueSplit.sol` | ✅ Real implementation (compiles solc 0.8.24) — deploy on-chain / deploy ต่อยอดบน chain |
| `api/app.py` | ✅ `/market/channels` + `/workload/estimate` exist — add more endpoints / เพิ่ม endpoint ต่อได้ |
| `core/scheduler.py` | ✅ Tariff-aware + AI hooks — tune weights/optimization / ปรับน้ำหนัก/optimization ต่อได้ |
| `ai/fine_tune/` | ✅ Real 72-row dataset (live Vast prices) + data-driven trainer — scale it up / ต่อยอดโมเดลที่หนักขึ้นได้ |

**License:** AGPL-3.0 — fork freely, send PRs. The 5% Developer Treasury rewards those who maintain the core (see Blueprint).
**กติกา (AGPL-3.0):** fork ได้ แก้ได้ ส่ง PR ได้ — ตามสาส์นชี้ชวนใน Blueprint (5% Developer Treasury สำหรับผู้รักษาแกนกริด)

---

## 🧪 สถานะของ Prototype นี้ (Prototype Status)

- [x] Core system: config / models / 7 channels / arbitrage + hooks / billing / 75/20/5 / scheduler / sandbox / genesis registry / แกนระบบครบ
- [x] Tests pass (unittest — stdlib only) / tests รันผ่าน
- [x] demo.py — one-command live demo / สาธิตทั้งระบบด้วยคำสั่งเดียว
- [x] Customer Portal — web UI (FastAPI + bilingual) / หน้าเว็บลูกค้า
- [x] Live Dashboard (Streamlit) — live channel prices + best channel + 75/20/5 slider / ราคาช่องทางสด + สไลด์แบ่งรายได้
- [x] Vast.ai real API connected (console.vast.ai/api/v0/bundles — live prices, 60s cache, auto fallback) / เชื่อม Vast.ai API จริงแล้ว
- [x] Akash channel (real REST multi-endpoint + auto fallback — needs approved tenant) / ช่องทาง Akash
- [x] Real Docker sandbox (needs docker runtime — stub fallback) / Docker sandbox จริง
- [x] RevenueSplit.sol real implementation (compiles solc 0.8.24 — not yet deployed) / สมาร์ทคอนแทร็กต์จริง
- [x] First data-driven AI model (trained on real 72-row dataset — in-sample 100%) / AI โมเดลแรก
- [x] Smart Yield Balancer (15% threshold + overhead cost — prevents flapping & rate limits) / Yield Balancer
- [ ] io.net / Render real API (need approved supplier / node operator / tenant first) / รอการอนุมัติจากแพลตฟอร์ม

---

*Licensed under AGPL-3.0 — สร้างจาก Blueprint v6 + PROGRAM_GOALS (DRAFT 20 ส.ค. 2026) — Open Architecture: fork, PR, claim your code ownership.*

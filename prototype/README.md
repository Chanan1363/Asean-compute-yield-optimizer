# ⚡ ASEAN Grid — Program Prototype (v0.1)

> **The Anti-Fragile, Decentralized GPU Yield Optimizer for Southeast Asia — Program Prototype.**
> ต้นแบบโปรแกรม (Program Prototype) ของ The ASEAN Grid — สร้างจากความรู้ทั้งหมดของโปรเจกต์ (Blueprint v6, PROGRAM_GOALS, Core 75/20/5) ออกแบบให้ **AI จูนนิ่ง (fine-tuning) ใส่เข้าไปได้** และ **Dev ทั่วโลก fork ต่อยอดได้**

---

## 🌍 Why This Prototype, Right Now — ทำไมต้องเป็นตอนนี้ (สิงหาคม 2026)

| สถานการณ์โลกปัจจุบัน | ผลกระทบต่อการออกแบบ |
|---|---|
| Global Compute Crisis — data center ใหญ่ชนกำแพง (ค่าไฟ/สภาพอากาศ/embargo ชิป) | ต้องเป็น "light-asset" — ไม่สร้าง data center ใช้พลังว่างที่มีอยู่ |
| AI demand ระเบิด (training + inference + agentic AI) | รองรับงานหลายประเภท: training / inference / rendering / mining / simulation |
| DePIN โตแล้ว (Vast.ai, io.net, Render) แต่ยังไม่มี "ตัวกลางอัจฉริยะ" สำหรับอาเซียน | Arbitrage Engine ข้าม 5 ช่องทาง = จุดขายไม่ซ้ำใคร |
| ภูมิรัฐศาสตร์: อาเซียนติดดีมานด์ AI ใหญ่สุด (จีน/เกาหลี/ญี่ปุ่น) | latency 20-40ms pipeline เป็น moat |
| AI fine-tuning กลายเป็นของธรรมดา | ทุกจุดตัดสินใจในระบบออกแบบเป็น **AI Hook** — ใส่โมเดลจูนเองได้ |

---

## 🏗️ Architecture at a Glance — สถาปัตยกรรมโดยย่อ

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
[Vast.ai] [io.net] [Render] [Direct AI] [Studios]   ← 5 ช่องทาง (pluggable)
        │
        ▼
[ SCHEDULER ]  (ค่าไฟ/เวลา/ความน่าเชื่อถือ — tariff-aware)
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
│
├── core/                   ← แกนระบบ (Python 3.11, stdlib เป็นหลัก)
│   ├── config.py           ← ค่าตั้งศูนย์กลาง (75/20/5, fees, timeouts)
│   ├── models.py           ← Data models: Node, Workload, Tenant, ApiKey, Payout
│   ├── channels.py         ← 5 ช่องทางรายได้ (interface + stub)
│   ├── arbitrage.py        ← Arbitrage Engine + Strategy interface
│   ├── scheduler.py        ← จัดคิวงาน (tariff-aware)
│   ├── billing.py          ← Prepaid API + จ่ายวินาทีต่อวินาที
│   ├── revenue_split.py    ← แบ่งรายได้ 75/20/5 (Smart Contract interface)
│   ├── sandbox.py          ← Docker Sandbox orchestration (interface + stub)
│   └── genesis.py          ← บันทึกผู้บุกเบิก (append-only registry)
│
├── ai/                     ← 🧠 จุดที่ AI จูนนิ่งใส่ได้ (THE AI HOOKS)
│   ├── strategy_hooks.py   ← AIStrategy interface + registry (pluggable)
│   ├── fine_tune/          ← จุดเตรียม data + train สำหรับ AI จูน
│   │   ├── dataset_schema.md
│   │   └── trainer_stub.py
│   └── prompts/            ← prompts สำหรับ AI dev agents
│       └── agents.md
│
├── api/                    ← REST API (FastAPI — optional dep)
│   └── app.py
│
├── contracts/              ← Smart Contract (interface-level stub)
│   └── RevenueSplit.sol
│
└── tests/                  ← unittest — รันได้ทันที ไม่ต้องติดตั้งอะไร
    ├── test_revenue_split.py
    ├── test_billing.py
    └── test_arbitrage.py
```

---

## 🚀 เริ่มต้นใช้งาน (Quick Start)

```bash
# 1. ทดสอบระบบแกน (ไม่ต้องติดตั้งอะไร — stdlib ล้วน)
python -m unittest discover -s prototype/tests -v

# 2. ทดลอง Arbitrage Engine + ดูสัดส่วนรายได้
python - <<'EOF'
from prototype.core.config import Config
from prototype.core.revenue_split import RevenueSplit

cfg = Config()
rs = RevenueSplit(cfg)
result = rs.split(1000.00)          # ลูกค้าจ่าย 1,000 USD
print(result)                        # {'node': 750.0, 'platform': 200.0, 'developer': 50.0}
EOF

# 3. (Optional) รัน API — ต้องติดตั้ง fastapi/uvicorn
# pip install fastapi uvicorn
# uvicorn prototype.api.app:app --reload
```

---

## 🧠 AI Hooks — จุดที่ "AI จูนนิ่ง" ใส่เข้าไปได้ (หัวใจของ prototype)

ระบบออกแบบให้จุดตัดสินใจสำคัญ **เป็นปลั๊กอิน AI** — ทีม/Dev คนใดมีโมเดลจูนของตัวเอง ใส่ได้ทันทีโดยไม่แตะแกนระบบ:

| Hook | จุดแทรก | ใส่โมเดลอะไรได้ |
|---|---|---|
| **Channel Selection** | `AIStrategy.predict_best_channel(features)` | โมเดลพยากรณ์ช่องทางจ่ายสูงสุด (เทรนจากราคาประวัติ) |
| **Pricing** | `AIStrategy.predict_price_curve(hour, region)` | โมเดลคาดการณ์ราคา GPU ล่วงหน้า |
| **Fraud / Node Trust** | `AIStrategy.score_node_trust(node)` | โมเดลให้คะแนนความน่าเชื่อถือโหนด (กันโกง) |
| **Demand Forecast** | `AIStrategy.forecast_demand(region, window)` | โมเดลพยากรณ์ดีมานด์ → จัดคิวล่วงหน้า |
| **Workload Routing** | `AIStrategy.route_workload(workload, nodes)` | โมเดลเลือกเส้นทางงานตาม latency/ราคา/ความเสี่ยง |

**วิธีใส่โมเดลของคุณ:**
1. ดู `ai/fine_tune/dataset_schema.md` — schema สำหรับสร้าง training data
2. เทรนด้วย `ai/fine_tune/trainer_stub.py` (หรือ pipeline ของคุณเอง)
3. implement `AIStrategy` (ดู `ai/strategy_hooks.py`) แล้วลงทะเบียน:
```python
from prototype.ai.strategy_hooks import StrategyRegistry, AIStrategy

class MyTunedStrategy(AIStrategy):
    def predict_best_channel(self, features):
        return "io.net"  # ← ใส่โมเดลคุณตรงนี้

StrategyRegistry.register("my-tuned", MyTunedStrategy())
```

---

## 🔌 Dev Hooks — จุดที่ Dev ทั่วโลกต่อยอดได้

| ช่องว่างที่ตั้งใจเว้นไว้ | วิธีต่อยอด |
|---|---|
| `core/channels.py` | เพิ่มช่องทางที่ 6 (Akash, Together, Lambda...) — implement `ComputeChannel` |
| `core/sandbox.py` | ต่อ Docker/K8s จริง — ตอนนี้เป็น interface + stub |
| `contracts/RevenueSplit.sol` | เขียน smart contract จริง (Solidity) ตาม interface |
| `api/app.py` | เพิ่ม endpoint — โครงสร้าง FastAPI พร้อม |
| `core/scheduler.py` | เพิ่ม optimization algorithm (ค่าไฟรายประเทศ/รายช่วงเวลา) |
| `ai/fine_tune/` | สร้าง dataset จริงจาก logs เมื่อระบบรันจริง |

**กติกา (AGPL-3.0):** fork ได้ แก้ได้ ส่ง PR ได้ — ตามสาส์นชี้ชวนใน Blueprint (5% Developer Treasury สำหรับผู้รักษาแกนกริด)

---

## 🧪 สถานะของ Prototype นี้

- [x] แกนระบบ: config / models / 5 channels / arbitrage + hooks / billing / 75/20/5 / scheduler / sandbox interface / genesis registry
- [x] tests รันผ่าน (unittest — stdlib ล้วน)
- [ ] Docker sandbox จริง (ต้องมี docker runtime)
- [ ] Smart contract จริงบน chain (มี interface แล้ว)
- [ ] AI โมเดลจูนจริง (มี hooks + schema แล้ว — รอ data จริง)
- [ ] เชื่อม Vast.ai / io.net / Render API จริง (มี stub แล้ว)

---

*Licensed under AGPL-3.0 — สร้างจาก Blueprint v6 + PROGRAM_GOALS (DRAFT 20 ส.ค. 2026) — Open Architecture: fork, PR, claim your code ownership.*

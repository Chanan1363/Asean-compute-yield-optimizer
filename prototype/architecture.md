# ASEAN Grid — Prototype Architecture (สถาปัตยกรรมต้นแบบ)

> เอกสารนี้อธิบายสถาปัตยกรรมของ Program Prototype + **ทุกจุดที่เว้นไว้ให้ต่อยอด**
> (AI hooks + Dev hooks) — อ่านคู่กับ `README.md` และ `ai/prompts/agents.md`

---

## 1. หลักการออกแบบ (Design Principles)

1. **Core ของตายแยกจากของต่อยอด** — สัดส่วน 75/20/5, ค่าธรรมเนียม, สกุลเงิน อยู่ใน `core/config.py` ที่เดียว (ข้อมูลศูนย์กลางเดียว — ตามหลัก ERP ของผู้ก่อตั้ง)
2. **ทุกจุดตัดสินใจเป็นปลั๊กอิน AI** — ระบบต้องฉลาดขึ้นได้โดยไม่ต้องเขียนแกนใหม่ (AI จูนนิ่งใส่ได้)
3. **Interface ก่อน Implementation** — ทุกโมดูลมี interface (ABC) + stub — Dev ต่อของจริงโดยไม่รื้อโครง
4. **รันได้ทันทีโดยไม่ต้องติดตั้ง** — แกนระบบใช้ stdlib ล้วน (tests 16 ข้อผ่านโดยไม่ pip install)
5. **AGPL-3.0** — ทุกคน fork/PR ได้ — กองทุน Dev 5% เป็นแรงจูงใจ

---

## 2. โมดูลและความรับผิดชอบ (Modules & Responsibilities)

| โมดูล | ไฟล์ | รับผิดชอบ | สถานะ |
|---|---|---|---|
| Config | `core/config.py` | ค่าตั้งศูนย์กลาง (75/20/5, fees, region) | ✅ พร้อม |
| Models | `core/models.py` | Node/Workload/Tenant/ApiKey/Payout | ✅ พร้อม |
| Channels | `core/channels.py` | 6 ช่องทาง (Vast/io.net/Render/Direct/Studios/Akash) | Vast = API จริง / Akash = REST จริง+fallback / ที่เหลือรอ approved supplier |
| Arbitrage | `core/arbitrage.py` | สแกน → เลือกช่องทาง (AI hook) → ส่งงาน | ✅ พร้อม + 🧠 hook |
| Scheduler | `core/scheduler.py` | จัดคิวตามค่าไฟ/trust | ✅ พร้อม + 🧠 hook |
| Billing | `core/billing.py` | Prepaid API + จ่ายวินาทีต่อวินาที | ✅ พร้อม (memory) |
| RevenueSplit | `core/revenue_split.py` | 75/20/5 + จ่ายรายวัน THB | ✅ พร้อม (ตรง Solidity stub) |
| Sandbox | `core/sandbox.py` | Docker isolation | 🔌 stub — ต่อ Docker จริง |
| Genesis | `core/genesis.py` | บันทึกผู้บุกเบิกถาวร (append-only) | ✅ พร้อม |
| AI Hooks | `ai/strategy_hooks.py` | StrategyRegistry + AIStrategy | ✅ พร้อม + 🧠 ใส่โมเดล |
| API | `api/app.py` | REST endpoints (FastAPI) | 🔌 optional dep |
| Contract | `contracts/RevenueSplit.sol` | Smart contract 75/20/5 | 🔌 interface stub |

**สัญลักษณ์:** ✅ พร้อมใช้ / 🔌 ต้องต่อยอด / 🧠 จุด AI จูน

---

## 3. Data Flow หลัก (เส้นทางเงิน + งาน)

```
ลูกค้าจ่าย (USD/Crypto) ──→ Billing.top_up() ──→ Tenant.balance
                              │
   งานเข้า (Workload) ────────┤
                              ▼
   ArbitrageEngine.pick_best_channel()  ← 🧠 AIStrategy.predict_best_channel()
                              │
                              ▼
   Channel.submit_workload()  (6 ช่องทาง)
                              │
                              ▼
   Scheduler.schedule()  ← 🧠 AIStrategy.forecast_demand() / score_node_trust()
                              │
                              ▼
   SandboxOrchestrator (Docker isolation) → Node รันงาน
                              │
                              ▼
   Billing.charge_seconds()  (หักวินาทีต่อวินาที — ไม่ทำงาน = ไม่จ่าย)
                              │
                              ▼
   RevenueSplit.split() → 75% Node (รายวัน THB) / 20% Platform / 5% Dev
                              │
                              ▼
   GenesisLedger (บันทึกทุกธุรกรรม/ผู้บุกเบิก — chain hash)
```

---

## 4. จุดต่อขยายทั้งหมด (Extension Points — "ร่อง/รู/ช่องว่าง" ที่ตั้งใจเว้น)

### 🧠 AI Fine-tuning Hooks (สิ่งที่ AI จูนใส่ได้)
| Hook | ไฟล์ | สิ่งที่โมเดลทำ | dataset schema |
|---|---|---|---|
| predict_best_channel | `ai/strategy_hooks.py` | เลือกช่องทางจ่ายสูงสุด | `ai/fine_tune/dataset_schema.md` §1 |
| score_node_trust | `ai/strategy_hooks.py` | ให้คะแนนโหนด กันโกง | §2 |
| forecast_demand | `ai/strategy_hooks.py` | พยากรณ์ดีมานด์ → จัดคิว | §3 |
| predict_price_curve | `ai/strategy_hooks.py` | คาดการณ์ราคา GPU | (ต่อยอด schema) |
| route_workload | `ai/strategy_hooks.py` | เลือกเส้นทางงาน | (ต่อยอด schema) |

**วิธีใส่โมเดล (3 ขั้น):** สร้าง data ตาม schema → เทรน (`trainer.py` — โมเดลแรก data-driven พร้อม dataset จริง 72 rows — หรือ pipeline ของคุณ) → `StrategyRegistry.register()` — ระบบใช้ทันที (มี test `test_ai_strategy_hook_overrides_heuristic` พิสูจน์แล้ว)

### 🔌 Developer Hooks (สิ่งที่ Dev ต่อยอดได้)
| ช่องว่าง | งานที่รอ | พร้อมแล้ว |
|---|---|---|
| `core/channels.py` | ต่อ API จริง Vast/io.net/Render + เพิ่มช่องทางใหม่ | interface + stub + test |
| `core/sandbox.py` | Docker/K8s จริง + verify_isolation เชิงรุก | interface + stub |
| `contracts/RevenueSplit.sol` | Solidity จริง + Foundry tests | interface + spec (ใน agents.md) |
| `core/billing.py` | เปลี่ยน memory → SQLite/Postgres + idempotency | logic พร้อม + test |
| `api/app.py` | endpoint เพิ่ม (nodes/keys/payouts) | FastAPI skeleton |
| `ai/fine_tune/` | dataset จริงจาก logs + pipeline จริง | schema + stub + prompts |

---

## 5. ความปลอดภัย (ตาม PROGRAM_GOALS C1/C2)

- **Sandbox ก่อนรันเสมอ**: create → `verify_isolation()` → run → destroy (interface บังคับ)
- **API key เก็บ hash**: `billing.py` เก็บ SHA-256 เท่านั้น (test พิสูจน์)
- **Genesis chain**: ทุก entry ผูก hash กับ entry ก่อน (กันแก้ย้อนหลัง — `verify()` ตรวจได้)
- **Config guard**: สัดส่วนรายได้รวม ≠ 1.0 → ระบบไม่ start (`__post_init__`)

---

## 6. แผนต่อจาก prototype (Roadmap จริง)

1. **Phase 0 (ตอนนี้):** prototype นี้ — พิสูจน์ logic + ดึง dev ผ่าน PR
2. **Phase 1:** ต่อ Vast.ai API จริง + Docker sandbox จริง → รันบนเครื่องพี่เต้ 1-2 เครื่อง (alpha)
3. **Phase 2:** ร้านเน็ตไทย/เวียดนาม (Blueprint Phase 2) + billing จริง (DB)
4. **Phase 3:** Smart contract จริง + $GRID + ติดต่อ Nous Research (Blueprint Phase 3)
5. **ต่อเนื่อง:** เก็บ logs → สร้าง dataset จริง → AI จูนโมเดล arbitrage → ดีขึ้นทุกไตรมาส (PROGRAM_GOALS กติกา)

---

*AGPL-3.0 — Open Architecture: fork, PR, claim your code ownership. สร้าง 20 ส.ค. 2026 จาก Blueprint v6 + PROGRAM_GOALS.*

# AI Dev Agent Prompts — พรอมต์สำหรับ AI ที่มาช่วยพัฒนาต่อ

คอลเลกชัน prompt สำเร็จรูปสำหรับ AI coding agents (Cursor, Claude Code, Codex, Copilot...)
ให้ Dev วางใน agent แล้วให้ช่วยพัฒนาต่อในจุดที่ prototype เว้นไว้

---

## 1. สร้าง Docker Sandbox จริง (แทน stub)

```
You are working on the ASEAN Grid prototype (AGPL-3.0). Implement the real
Docker sandbox in prototype/core/sandbox.py:
- Use the docker SDK to create an isolated container per workload
- Enforce: host filesystem read-only, network isolation, seccomp default,
  GPU passthrough via nvidia-container-runtime
- verify_isolation() must actively check cgroup/namespace separation
- Add integration tests in tests/ that run only when docker is available
Requirements: keep the SandboxOrchestrator interface unchanged; security
first — escape attempts must be impossible (PROGRAM_GOALS C1: zero escapes).
```

## 2. เชื่อมช่องทาง Vast.ai API จริง

```
Implement VastAIChannel.get_quote() in prototype/core/channels.py using the
real Vast.ai API (https://vast.ai/api/v0/prices/). Map the response to
ChannelQuote. Handle: pagination, rate limits, offline fallback (return None).
Keep the other 4 channels as stubs. Add unit tests with mocked HTTP.
```

## 3. สร้าง Smart Contract จริง (Solidity)

```
prototype/contracts/RevenueSplit.sol is an interface stub. Implement a real
Solidity contract that:
- Receives payments in USD stablecoin (USDT)
- Splits automatically: 75% node providers (daily, batch), 20% platform ops,
  5% developer pool (claimable by verified contributors)
- Emits events for every payout; owner can update payout addresses only via
  multi-sig; the split ratio is immutable (core confirmed 75/20/5)
Write Foundry tests. Follow the exact interface in the stub.
```

## 4. สร้าง API keys + billing จริง

```
prototype/core/billing.py uses in-memory storage. Replace with a real
backend (SQLite/Postgres) while keeping the Billing API identical:
create_tenant, top_up, issue_api_key, charge_seconds. Store only key hashes
(SHA-256). Add an idempotency layer so charge_seconds never double-charges
on retry (pay-per-second billing must be exact — no compute, no charge).
```

## 5. เตรียม fine-tuning pipeline จริง

```
prototype/ai/fine_tune/trainer_stub.py is a stub. Build a real pipeline:
1. Parse logs from the arbitrage engine into the JSONL schema in
   ai/fine_tune/dataset_schema.md
2. Train a channel-selection model (start with gradient boosting; document
   the path to a neural net)
3. Wrap it as an AIStrategy and register it in StrategyRegistry
Deliver: working code, a small synthetic dataset for tests, and a README
explaining how to retrain on real data.
```

---

## หลักการสำหรับทุก agent

- **อย่าแตะแกนที่ "ของตาย"**: สัดส่วน 75/20/5 (config.py) ห้ามแก้ — เปลี่ยนไม่ได้ถ้าไม่ใช่การตัดสินใจระดับโปรเจกต์
- **เก็บ interface เดิม**: ทุก TODO ต้อง implement ตาม interface ที่มี — ต่อยอด ไม่ใช่รื้อ
- **AGPL-3.0**: โค้ดทั้งหมดอยู่ใต้สัญญานี้ — เขียน docstring ระบุที่มาเสมอ
- **ทดสอบก่อน PR**: ทุกงานต้องมี tests — ดู tests/ เป็นตัวอย่าง

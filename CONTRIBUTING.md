# 🤝 Contributing to The ASEAN Grid — คู่มือร่วมพัฒนา

> **Open architecture, open contributions.** The ASEAN Grid is licensed under AGPL-3.0: anyone may fork, modify, and contribute. Merged pull requests qualify for the **5% Developer Pool** described in the blueprint — the network pays its builders.
>
> **สถาปัตยกรรมเปิด เปิดรับทุกการมีส่วนร่วม** โปรเจกต์นี้ใช้สัญญา AGPL-3.0: fork ได้ แก้ได้ ส่ง PR ได้ PR ที่ถูกรวมมีสิทธิ์ใน **กองทุนนักพัฒนา 5%** ตามพิมพ์เขียว — เครือข่ายจ่ายค่าแรงคนสร้าง

---

## 1. เริ่มต้น (Quick Start)

```bash
# 1. Fork repo บน GitHub (ปุ่ม Fork มุมขวาบน)
# 2. Clone สำเนาของคุณมาที่เครื่อง
git clone https://github.com/<your-username>/Asean-compute-yield-optimizer.git
cd Asean-compute-yield-optimizer

# 3. รัน tests ก่อนแก้อะไร — ต้องผ่านทั้งหมด (16 ตัว)
python -m unittest discover -s prototype/tests -v

# 4. สร้าง branch สำหรับงานของคุณ
git checkout -b feature/<ชื่องาน>

# 5. แก้โค้ด → รัน tests อีกครั้ง → commit → push
git add .
git commit -m "Describe your change clearly"
git push origin feature/<ชื่องาน>

# 6. เปิด Pull Request บน GitHub (เปรียบเทียบ main ← branch คุณ)
```

**ข้อกำหนด Python:** 3.11+ (แกนระบบใช้ stdlib ล้วน — ไม่ต้องติดตั้งอะไร) / FastAPI + uvicorn เฉพาะงาน API เท่านั้น

---

## 2. กติกา (Contribution Rules)

1. **Tests ต้องผ่านเสมอ** — `python -m unittest discover -s prototype/tests -v` ก่อนส่ง PR
2. **ภาษาในโค้ด:** ไทย + อังกฤษ (comment/docstring สองภาษา ตามสไตล์โปรเจกต์)
3. **สัดส่วน 75/20/5 ห้ามแตะ** — `prototype/core/config.py` คือ "ของตาย": 75% ผู้ให้เครื่อง / 20% ระบบ / 5% นักพัฒนา (ยืนยันภาพ 18 ส.ค. 2026) — PR ที่เปลี่ยนตัวเลขนี้โดยไม่ผ่านการตกลงร่วมจะไม่ถูกรวม
4. **AI hooks ก่อน hardcode** — จุดตัดสินใจสำคัญต้องผ่าน `StrategyRegistry` (ดู prototype/ai/strategy_hooks.py) ไม่ใช่เขียนเงื่อนไขตายตัว
5. **ไม่ผูกเครื่องมือ** — ใช้สถาปัตยกรรม/เครื่องมือที่ถนัดได้อิสระ (stack-agnostic)
6. **เคารพลิขสิทธิ์** — ห้ามนำโค้ด/เอกสารของแพลตฟอร์มอื่น (Vast.ai, io.net, Render...) เข้ามาโดยไม่ได้รับอนุญาต ใช้ API ทางการเท่านั้น

---

## 3. งานที่ประกาศ (Good First Issues & Bounties)

| ป้าย / Label | ความหมาย | เหมาะกับ |
|---|---|---|
| `good-first-issue` | งานเริ่มต้น — อ่านโค้ดแล้วแก้ง่าย | Dev ใหม่ |
| `genesis-bounty` | งานประกาศรางวัล — รวม PR ได้สิทธิ์กองทุน 5% | Dev ที่มีประสบการณ์ |
| `ai-hook` | งานจุดแทรก AI (strategy/pricing/trust/forecast) | สาย ML/AI |

### งานที่เปิดอยู่ตอนนี้ (ช่องว่างที่ตั้งใจเว้นไว้)

| จุด | งาน | ความยาก |
|---|---|---|
| `prototype/core/channels.py` | เพิ่มช่องทางที่ 6 (Akash, Together, Lambda, ...) — implement `ComputeChannel` | ง่าย |
| `prototype/api/app.py` | เพิ่ม endpoint REST (โครงสร้าง FastAPI พร้อม) | ง่าย |
| `prototype/core/scheduler.py` | เพิ่ม optimization (ค่าไฟรายประเทศ/รายช่วงเวลา) | กลาง |
| `prototype/core/sandbox.py` | ต่อ Docker/K8s จริง (ตอนนี้เป็น interface) | กลาง |
| `prototype/contracts/RevenueSplit.sol` | เขียน smart contract จริงตาม interface | กลาง-ยาก |
| `prototype/ai/fine_tune/` | สร้าง dataset จริง + เทรนโมเดลแรก | ยาก |

---

## 4. มาตรฐานการ Review

PR จะได้รับการตรวจภายใน **48 ชั่วโมง** (ตาม Genesis Pilot) เกณฑ์:

- [ ] Tests รันผ่านครบ
- [ ] โค้ดอ่านง่าย ไม่ซ้ำซ้อน
- [ ] ไม่แตะสัดส่วน 75/20/5
- [ ] มี docstring ไทย/อังกฤษ (อย่างน้อยภาษาใดภาษาหนึ่ง)
- [ ] ไม่นำโค้ดของแพลตฟอร์มอื่นมาโดยไม่ได้รับอนุญาต

---

## 5. รางวัล (Developer Pool — 5%)

ตาม blueprint และ PROGRAM_GOALS E5:

- **PR ที่ merge** → บันทึกชื่อใน Genesis Ledger (บทบาท developer — ถาวร)
- **ผลงานสำคัญ** (ปลั๊กอิน, แก้ช่องโหว่, โมเดล AI) → มีสิทธิ์รับเงินจากกองทุน 5% เมื่อระบบเปิดจ่าย
- **Contributor อันดับ 1-3** → Founder Advisory Seat (สิทธิ์ออกเสียงทิศทางโปรเจกต์)

> หลักการ: งานที่ทำเพื่อเครือข่าย ถูกบันทึกและตอบแทนอย่างเป็นธรรม — "ดีขึ้นเรื่อยๆ ไม่มีดีที่สุด"

---

## 6. ช่องทางติดต่อ

- **Issues / Discussions:** เปิดบน GitHub repo นี้
- **Genesis Ledger:** ชื่อคุณจะถูกจารึกเมื่อ PR แรกถูกรวม (ดู `prototype/core/genesis.py`)

*Licensed under AGPL-3.0 — fork, build, claim your code ownership.*

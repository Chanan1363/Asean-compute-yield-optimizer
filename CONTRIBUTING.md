# 🤝 Contributing to The ASEAN Grid

> **English:** Welcome! We're thrilled you're here. Whether you're fixing a bug, improving documentation, or building new GPU routing features — every contribution matters. The ASEAN Grid is open under AGPL-3.0: anyone may fork, modify, and contribute. And yes, the network pays its builders.
>
> **ไทย:** ยินดีต้อนรับครับ! เราดีใจมากที่คุณสนใจมาร่วมสร้าง ASEAN Grid ไม่ว่าจะเป็นการแก้บั๊ก ปรับปรุงเอกสาร หรือพัฒนาโมดูลจัดสรร GPU — ทุกการมีส่วนร่วมมีคุณค่าเสมอ โปรเจกต์นี้เปิดภายใต้สัญญา AGPL-3.0: fork ได้ แก้ได้ ส่งงานได้ และที่สำคัญ — เครือข่ายจ่ายค่าแรงคนสร้าง

---

## Why Contribute? / ทำไมควรร่วมพัฒนา?

- **5% Developer Pool** — Every merged PR, plugin, or security fix qualifies for the 5% Developer Pool (the 75/20/5 split coded into the project blueprint). The network pays its builders, fairly and transparently.
- **กองทุนนักพัฒนา 5%** — ทุก PR, ปลั๊กอิน หรือการแก้ช่องโหว่ที่ถูกรวม มีสิทธิ์ในกองทุน 5% ตามสัดส่วน 75/20/5 ที่ระบุในพิมพ์เขียวของโปรเจกต์ เครือข่ายจ่ายค่าแรงคนสร้างอย่างเป็นธรรมและโปร่งใส

- **Open architecture, no vendor lock-in** — We strictly oppose locking anyone in. You own your code, and you're free to propose better tools, frameworks, or microservices.
- **สถาปัตยกรรมเปิด ไม่ผูกขาดเทคโนโลยี** — เราไม่ผูกขาดใครไว้กับเครื่องมือใด คุณเป็นเจ้าของโค้ด และมีอิสระเต็มที่ในการเสนอสิ่งที่ดีกว่า ไม่ว่าจะเป็นเครื่องมือ เฟรมเวิร์ก หรือไมโครเซอร์วิส

- **Regional impact** — Help build the compute backbone that powers AI across Southeast Asia.
- **สร้างอิมแพคระดับภูมิภาค** — ร่วมสร้างโครงสร้างพื้นฐานประมวลผลที่ขับเคลื่อน AI ทั่วภูมิภาคอาเซียน

---

## How to Get Started / เริ่มต้นง่ายๆ แค่ 5 ขั้นตอน

1. **Fork** the repository to your own GitHub account.
   **Fork** repo ไปที่บัญชี GitHub ของคุณ (ปุ่ม Fork มุมขวาบน)

2. **Clone & create a branch** for your work.
   **Clone** ลงเครื่องและสร้าง branch สำหรับงานของคุณ
   ```bash
   git clone https://github.com/<your-username>/Asean-compute-yield-optimizer.git
   cd Asean-compute-yield-optimizer
   git checkout -b feature/<your-work>
   ```

3. **Run the tests** — all must pass before you change anything (16 tests).
   **รัน tests ก่อน** — ต้องผ่านทั้งหมดก่อนเริ่มแก้ (16 ตัว)
   ```bash
   python -m unittest discover -s prototype/tests -v
   ```

4. **Make your changes**, run the tests again, then commit and push.
   **แก้โค้ด** → รัน tests อีกครั้ง → commit → push
   ```bash
   git add .
   git commit -m "Describe your change clearly"
   git push origin feature/<your-work>
   ```

5. **Open a Pull Request** against the `main` branch — and done! 🎉
   **เปิด Pull Request** เทียบกับ branch `main` — เสร็จแล้ว! 🎉

> **Python requirement / ข้อกำหนด Python:** 3.11+ (the core system is pure stdlib — nothing to install / แกนระบบใช้ stdlib ล้วน ไม่ต้องติดตั้งอะไร). FastAPI + uvicorn are only needed for API work / ใช้เฉพาะงาน API เท่านั้น.

---

## Contribution Rules / กติกาเบาๆ เพื่อให้ทุกคนเดินไปทางเดียวกัน

1. **Tests must always pass** — `python -m unittest discover -s prototype/tests -v` before opening a PR.
   **Tests ต้องผ่านเสมอ** — รันให้ครบก่อนส่ง PR

2. **Code language:** Thai + English (bilingual comments/docstrings, following the project style).
   **ภาษาในโค้ด:** ไทย + อังกฤษ (comment/docstring สองภาษา ตามสไตล์โปรเจกต์)

3. **The 75/20/5 split is sacred** — `prototype/core/config.py` defines the core economics: 75% to machine providers / 20% to the system / 5% to developers. PRs that change these numbers without collective agreement won't be merged — this is the heart of the network, and we protect it together.
   **สัดส่วน 75/20/5 คือหัวใจของระบบ** — 75% ผู้ให้เครื่อง / 20% ระบบ / 5% นักพัฒนา ถูกนิยามไว้ใน `prototype/core/config.py` PR ที่เปลี่ยนตัวเลขนี้โดยไม่ผ่านการตกลงร่วมจะไม่ถูกรวม — เพราะนี่คือแกนกลางที่เราช่วยกันปกป้อง

4. **AI hooks before hardcoding** — important decision points go through `StrategyRegistry` (see `prototype/ai/strategy_hooks.py`), not fixed conditions.
   **AI hooks ก่อน hardcode** — จุดตัดสินใจสำคัญต้องผ่าน `StrategyRegistry` (ดู `prototype/ai/strategy_hooks.py`) ไม่ใช่เขียนเงื่อนไขตายตัว

5. **Tool-agnostic** — you're free to use whatever stack you're comfortable with.
   **ไม่ผูกเครื่องมือ** — ใช้สถาปัตยกรรม/เครื่องมือที่ถนัดได้อิสระ

6. **Respect copyright** — don't bring in code or docs from other platforms (Vast.ai, io.net, Render, ...) without permission; use official APIs only.
   **เคารพลิขสิทธิ์** — ห้ามนำโค้ด/เอกสารของแพลตฟอร์มอื่น (Vast.ai, io.net, Render...) มาโดยไม่ได้รับอนุญาต ใช้ API ทางการเท่านั้น

---

## Looking for Tasks? / กำลังหางานทำอยู่ใช่ไหม?

Check our [GitHub Issues](https://github.com/Chanan1363/Asean-compute-yield-optimizer/issues) and look for these labels:
ลองดูที่ [GitHub Issues](https://github.com/Chanan1363/Asean-compute-yield-optimizer/issues) แล้วมองหาป้ายเหล่านี้:

| Label / ป้าย | Meaning / ความหมาย | Best for / เหมาะกับ |
|---|---|---|
| `good-first-issue` | Great for beginners — easy to pick up / งานเริ่มต้น อ่านโค้ดแล้วแก้ง่าย | New devs / Dev ใหม่ |
| `genesis-bounty` | Bounty work — merged PRs qualify for the 5% Developer Pool / งานประกาศรางวัล — PR ที่รวมได้สิทธิ์กองทุน 5% | Experienced devs / Dev ที่มีประสบการณ์ |
| `ai-hook` | AI integration points (strategy/pricing/trust/forecast) / งานจุดแทรก AI | ML/AI folks / สาย ML/AI |

### Currently open (deliberately left for the community) / งานที่เปิดอยู่ตอนนี้ (ช่องว่างที่ตั้งใจเว้นไว้ให้ชุมชน)

| Area / จุด | Task / งาน | Difficulty / ความยาก |
|---|---|---|
| `prototype/core/channels.py` | Add a 6th channel (Akash, Together, Lambda, ...) — implement `ComputeChannel` / เพิ่มช่องทางที่ 6 | Easy / ง่าย |
| `prototype/api/app.py` | Add a REST endpoint (FastAPI scaffolding ready) / เพิ่ม endpoint REST (โครงสร้าง FastAPI พร้อม) | Easy / ง่าย |
| `prototype/core/scheduler.py` | Add optimization (per-country / per-time electricity costs) / เพิ่ม optimization (ค่าไฟรายประเทศ/รายช่วงเวลา) | Medium / กลาง |
| `prototype/core/sandbox.py` | Hook up real Docker/K8s (currently an interface) / ต่อ Docker/K8s จริง (ตอนนี้เป็น interface) | Medium / กลาง |
| `prototype/contracts/RevenueSplit.sol` | Write the real smart contract from the interface / เขียน smart contract จริงตาม interface | Medium–Hard / กลาง-ยาก |
| `prototype/ai/fine_tune/` | Build a real dataset + train the first model / สร้าง dataset จริง + เทรนโมเดลแรก | Hard / ยาก |

---

## Code of Conduct / ข้อตกลงร่วมกัน

**English:** We are committed to a welcoming, respectful, and inclusive environment for everyone. Please be kind, collaborative, and constructive in all discussions — ideas are welcome, people are respected.

**ไทย:** เรามุ่งมั่นที่จะสร้างพื้นที่ที่เปิดกว้าง ให้เกียรติ และเคารพซึ่งกันและกันสำหรับทุกคน โปรดใช้ความสุภาพ ให้ความร่วมมือ และสร้างสรรค์ในการพูดคุยทุกครั้ง — ไอเดียทุกอันมีค่า และทุกคนมีศักดิ์ศรี

---

## Review & Rewards / การตรวจงานและรางวัล

PRs are reviewed within **48 hours** (per Genesis Pilot). Checkpoints:
PR จะได้รับการตรวจภายใน **48 ชั่วโมง** (ตาม Genesis Pilot) เกณฑ์ตรวจ:

- [ ] Tests pass / Tests รันผ่านครบ
- [ ] Readable, non-duplicated code / โค้ดอ่านง่าย ไม่ซ้ำซ้อน
- [ ] 75/20/5 split untouched / ไม่แตะสัดส่วน 75/20/5
- [ ] Bilingual docstrings (at least one language) / มี docstring ไทย/อังกฤษ (อย่างน้อยภาษาใดภาษาหนึ่ง)
- [ ] No unauthorized code from other platforms / ไม่นำโค้ดของแพลตฟอร์มอื่นมาโดยไม่ได้รับอนุญาต

Once merged, you're in the Genesis Ledger (permanent). Notable work (plugins, security fixes, AI models) qualifies for the 5% Developer Pool once payouts go live, and top-3 contributors earn a Founder Advisory Seat with voting rights on the project's direction.
เมื่อ PR ถูกรวม ชื่อของคุณจะถูกจารึกใน Genesis Ledger (ถาวร) ผลงานสำคัญ (ปลั๊กอิน, แก้ช่องโหว่, โมเดล AI) มีสิทธิ์รับเงินจากกองทุน 5% เมื่อระบบเปิดจ่าย และ Contributor อันดับ 1-3 ได้ที่นั่ง Founder Advisory Seat (สิทธิ์ออกเสียงทิศทางโปรเจกต์)

> The principle: work done for the network is recorded and rewarded fairly — "better every day, no such thing as best."
> หลักการ: งานที่ทำเพื่อเครือข่าย ถูกบันทึกและตอบแทนอย่างเป็นธรรม — "ดีขึ้นเรื่อยๆ ไม่มีดีที่สุด"

---

## Contact / ช่องทางติดต่อ

- **Issues / Discussions:** open them right here on the GitHub repo / เปิดได้บน GitHub repo นี้
- **Genesis Ledger:** your name gets inscribed when your first PR merges (see `prototype/core/genesis.py`) / ชื่อคุณจะถูกจารึกเมื่อ PR แรกถูกรวม (ดู `prototype/core/genesis.py`)

*Licensed under AGPL-3.0 — fork, build, claim your code ownership.*

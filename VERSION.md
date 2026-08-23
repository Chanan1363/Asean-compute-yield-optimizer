# ASEAN Grid — Version Log (บันทึกเวอร์ชัน)

> **กฎเหล็ก (Golden Rule):** เวลา bump เวอร์ชัน → ต้องแก้ **ทุกไฟล์ใน checklist นี้พร้อมกัน** ใน commit เดียว
> (หลัก Single Source of Truth — กันเวอร์ชันแตก ไม่ตรงกัน)

---

## 📋 Checklist เวลา bump เวอร์ชัน (แก้พร้อมกันเสมอ)

| # | ไฟล์ | จุดที่แก้ |
|---|---|---|
| 1 | `prototype/customer_portal.html` | `VERSION` constant + footer (บรรทัด "vX.Y.Z") |
| 2 | `README.md` | version badge (`img.shields.io/badge/version-...`) |
| 3 | `VERSION.md` | เพิ่มแถวประวัติด้านล่าง |
| 4 | *(เฉพาะเวอร์ชันเอกสาร)* `The_ASEAN_Grid_Blueprint_vX.md` | เปลี่ยนชื่อไฟล์ + version history table |

---

## 📜 ประวัติเวอร์ชัน (Version History)

| เวอร์ชัน | วันที่ | สิ่งที่เปลี่ยน | ไฟล์หลักที่เกี่ยวข้อง |
|---|---|---|---|
| **v1.3.0-nous** | 23 ส.ค. 2026 | **Nous Alignment ครบชุด**: RevenueSplitV2 (points + permissionless claim + collateral — ดีไซน์จาก Psyche), Blueprint v8, Nous Alignment Plan (Part A เทคนิค + B เงิน), portal badge/footer "DisTrO-inspired" | `prototype/contracts/RevenueSplitV2.sol`, `docs/NOUS_ALIGNMENT.md`, `The_ASEAN_Grid_Blueprint_v8.md`, `prototype/architecture.md` (section 7), `prototype/customer_portal.html`, `README.md` |
| **v1.3.1-demo** | 23 ส.ค. 2026 | **DeMo Proof-of-Concept PASS** — loss ลด 84.2% บน T4 GPU (หลักฐาน: `docs/DEMO_PROOF.md`) — Nous Alignment Part A Phase 1 เสร็จ | `docs/DEMO_PROOF.md` |
| v0.1 | 20 ส.ค. 2026 | Prototype เริ่มแรก — Customer Portal, core modules (arbitrage/scheduler/channels), Genesis Ledger | `prototype/customer_portal.html`, `prototype/core/*`, `prototype/contracts/RevenueSplit.sol` (v1) |

---

*The ASEAN Grid — Democratizing Compute for ASEAN · AGPL-3.0*

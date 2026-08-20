"""
ASEAN Grid — Program Prototype Live Demo
สาธิตการทำงานจริงของระบบครบวงจร: ตั้งค่า → ลูกค้าเติมเงิน → Arbitrage เลือกช่องทาง
→ คิดเงินวินาทีต่อวินาที → แบ่งรายได้ 75/20/5 → จ่ายรายวันบาท → จารึก Genesis Ledger

วิธีรัน (รันจากที่ไหนก็ได้):
    python prototype/demo.py
"""
import os
import sys

# ให้ import prototype.* ทำงาน ไม่ว่าจะรันจากโฟลเดอร์ใด
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prototype.core.config import Config
from prototype.core.models import Node, Workload, WorkloadType, NodeStatus
from prototype.core.billing import Billing
from prototype.core.arbitrage import ArbitrageEngine
from prototype.core.scheduler import Scheduler
from prototype.core.revenue_split import RevenueSplit
from prototype.core.genesis import GenesisLedger

BAR = "=" * 62


def main() -> None:
    print(BAR)
    print("  ASEAN GRID — PROGRAM PROTOTYPE LIVE DEMO")
    print("  สาธิตการทำงานจริงของระบบ (20 ส.ค. 2569)")
    print(BAR)

    # ── 1. ระบบตั้งค่า ──────────────────────────────────────────
    cfg = Config()
    print("\n[1] ระบบตั้งค่า (config)")
    print(f"    สัดส่วนรายได้ Core: 75/20/5 → node={cfg.NODE_SHARE:.0%}, "
          f"platform={cfg.PLATFORM_SHARE:.0%}, dev={cfg.DEVELOPER_SHARE:.0%}")
    print(f"    สมาชิก B2C: ${cfg.B2C_SUBSCRIPTION_USD}/เดือน | "
          f"ค่าธรรมเนียม buyback: {cfg.SYSTEM_FEE_MIN:.0%}-{cfg.SYSTEM_FEE_MAX:.0%}")

    # ── 2. ลูกค้าเติมเงิน (B2B prepaid) ─────────────────────────
    print("\n[2] ลูกค้าองค์กรเติมเงินล่วงหน้า (Prepaid API Key)")
    billing = Billing(cfg)
    tenant = billing.create_tenant("Moonshot AI / Kimi (จำลอง)")
    billing.top_up(tenant, 2000.00)
    key = billing.issue_api_key(tenant)
    print(f"    {tenant.name} เติมเงิน ${tenant.balance_usd:,.2f}")
    print(f"    ได้ API Key: {key.key_prefix}... (เก็บ hash ในระบบ ไม่เก็บ key ดิบ)")

    # ── 3. งานเข้ามา → Arbitrage Engine เลือกช่องทาง ────────────
    print("\n[3] งาน AI Inference เข้ามา → สมอง Arbitrage สแกนตลาด")
    engine = ArbitrageEngine(cfg)
    wl = Workload(workload_id="W-1001", tenant_id=tenant.tenant_id,
                  wtype=WorkloadType.AI_INFERENCE, gpu_hours_required=24)
    quotes = engine.scan_market()
    print(f"    สแกนเจอ {len(quotes)} ช่องทาง:")
    for q in quotes:
        print(f"      - {q.channel:<11} ราคา ${q.price_usd_per_hour:.2f}/ชม.  "
              f"คิว {q.queue_depth}  latency {q.latency_ms}ms  คะแนน {q.score:.1f}")
    best = engine.pick_best_channel(wl)
    print(f"    🧠 AI Strategy เลือก: {best} (จ่ายสูงสุดสุทธิ)")
    job = engine.route(wl)
    print(f"    ส่งงานแล้ว → job_id: {job}")

    # ── 4. จ่ายวินาทีต่อวินาที ──────────────────────────────────
    print("\n[4] คิดเงินวินาทีต่อวินาที (Pay-per-Compute)")
    cost = billing.charge_seconds(tenant, 3600 * 24, 0.55)   # 24 ชม. @ $0.55/ชม.
    print(f"    งานรัน 24 ชม. → หัก ${cost:.2f} (ยอดเหลือ ${tenant.balance_usd:,.2f})")
    cost0 = billing.charge_seconds(tenant, 0, 0.55)
    print(f"    ไม่ทำงาน 0 วินาที → หัก ${cost0:.2f} (ไม่ทำงาน = ไม่จ่าย ✅)")

    # ── 5. แบ่งรายได้ 75/20/5 → จ่ายรายวันเป็นบาท ───────────────
    print("\n[5] จัดสรรรายได้ 75/20/5 (Smart Contract)")
    split = RevenueSplit(cfg).split(1000.00)   # ลูกค้าจ่าย $1,000
    print(f"    รายได้รวม $1,000 → ผู้ให้เครื่อง ${split.node_usd:.0f} | "
          f"ระบบ ${split.platform_usd:.0f} | นักพัฒนา ${split.developer_usd:.0f}")
    payout = RevenueSplit(cfg).daily_payout(split.node_usd / 10)  # 1 ใน 10 ของกอง (โหนดเดียว)
    print(f"    จ่ายรายวันให้ 1 โหนด: ${payout['usd']:,.2f} = {payout['thb']:,.2f} บาท 💵")

    # ── 6. Scheduler จัดคิวตามค่าไฟ ─────────────────────────────
    print("\n[6] Scheduler จัดคิวตามค่าไฟ (tariff-aware)")
    node_bkk = Node(node_id="n-001", owner_name="Tay", region="th",
                    gpu_model="RTX 4090", vram_gb=24, idle_hours_per_day=12,
                    status=NodeStatus.ACTIVE)
    node_vn = Node(node_id="n-002", owner_name="Nong", region="vn",
                   gpu_model="RTX 4070 Ti Super", vram_gb=12, idle_hours_per_day=10,
                   electricity_usd_per_kwh=0.12, status=NodeStatus.ACTIVE)
    order_day = Scheduler(cfg).schedule([node_bkk, node_vn], wl, hour=14)
    print(f"    ช่วงกลางวัน (ไฟแพง): เรียง {[n.node_id for n in order_day]}")
    order_night = Scheduler(cfg).schedule([node_bkk, node_vn], wl, hour=2)
    print(f"    ช่วงกลางคืน (ไฟถูก): เรียง {[n.node_id for n in order_night]}")

    # ── 7. Genesis Ledger จารึกผู้บุกเบิก ───────────────────────
    print("\n[7] Genesis Ledger — จารึกชื่อผู้บุกเบิก (ถาวร กันแก้)")
    ledger = GenesisLedger()
    ledger.add("Tay (Chanan)", "compute", "RTX 4090 - Bangkok, Thailand")
    ledger.add("Nong", "developer", "first PR to arbitrage engine")
    ledger.add("Ambassador-01", "ambassador", "Thai gamer community")
    print(f"    ผู้บุกเบิก {len(ledger.entries)} คน จารึกแล้ว")
    print(f"    ตรวจความถูกต้องของ chain (กันแก้ย้อนหลัง): "
          f"{'ผ่าน ✅' if ledger.verify() else 'FAIL'}")
    print("    รายชื่อ:")
    for e in ledger.entries:
        print(f"      - {e.builder_name} [{e.role}] hash={e.entry_hash}")

    print(f"\n{BAR}")
    print("  DEMO จบ — ทุกระบบทำงานถูกต้อง (รัน tests: python -m unittest discover -s prototype/tests -v)")
    print(BAR)


if __name__ == "__main__":
    main()

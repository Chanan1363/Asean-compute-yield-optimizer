"""
ASEAN Grid — Live Dashboard (Streamlit)
One page: live channel prices → best channel → 75/20/5 revenue split → daily node-owner profit example
หน้ารวม: ราคาช่องทางสด → ช่องทางที่ดีที่สุด → การแบ่งรายได้ 75/20/5 → ตัวอย่างกำไรรายวัน

Run / รัน:
  .venv-dashboard\Scripts\streamlit run prototype/dashboard.py
or / หรือ: uv run --python .venv-dashboard/Scripts/python.exe -m streamlit run prototype/dashboard.py

Built for live demos (customer/partner view) — every number comes from real code, not mockups.
ออกแบบให้โชว์เดโมได้เลย (มุมมองลูกค้า/พาร์ทเนอร์) — ตัวเลขทุกตัวมาจาก code จริง ไม่ใช่ภาพ
"""
import os
import sys

# Make `import prototype.*` work no matter where Streamlit launches from
# (Render runs the script by full path, so repo root must be added to sys.path)
# ทำให้ import prototype.* ใช้ได้ไม่ว่ารันจากโฟลเดอร์ไหน (Render รันด้วย path เต็ม ต้องเพิ่ม repo root เข้า sys.path)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime, timezone, timedelta

import streamlit as st

from prototype.core.arbitrage import ArbitrageEngine
from prototype.core.config import Config
from prototype.core.revenue_split import RevenueSplit

st.set_page_config(page_title="ASEAN Grid — Live Dashboard", page_icon="⚡", layout="wide")

config = Config()
engine = ArbitrageEngine(config)
split = RevenueSplit(config)


@st.cache_data(ttl=60, show_spinner="สแกนตลาดช่องทาง... / Scanning channels...")
def scan_market():
    """Scan all channel prices — 60s cache, matching the Smart Yield Balancer (avoids rate limits).
    สแกนราคาทุกช่องทาง — cache 60 วิ ตรงกับ Smart Yield Balancer (กัน rate limit)"""
    return engine.scan_market()


@st.cache_data(ttl=60, show_spinner=False)
def best_channel():
    return engine.pick_best_channel()


# ── Header ─────────────────────────────────────────────────────────────
st.title("⚡ ASEAN Grid — Live Dashboard")
st.caption(
    f"7 ช่องทางรายได้ / 7 income channels · Smart Yield Balancer · Revenue Split 75/20/5 · "
    f"สแกนตลาดทุก 60 วิ / market scan every 60s (อัตล่าสุด / last update {datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M:%S')} ไทย/ICT)"
)

# ── Row 1: live channel prices / ราคาช่องทางสด ─────────────────────────
st.subheader("📊 ราคาช่องทางสด (USD/ชม.) / Live Channel Prices (USD/hr)")
quotes = scan_market()

if quotes:
    cols = st.columns(len(quotes))
    for col, q in zip(cols, quotes):
        status_icon = {"connected": "🟢", "pending": "🟡", "not_connected": "🔒"}.get(
            q.status, "⚪"
        )
        with col:
            st.metric(
                label=f"{status_icon} {q.channel}",
                value=f"${q.price_usd_per_hour:.3f}",
                delta=f"GPU {q.available_gpus:,} · {q.latency_ms}ms",
            )

    # detail table + chart / ตารางรายละเอียด + กราฟ
    table = [
        {
            "channel": q.channel,
            "status": q.status,
            "price_usd/hr": q.price_usd_per_hour,
            "gpus": q.available_gpus,
            "queue": q.queue_depth,
            "latency_ms": q.latency_ms,
            "reliability": q.reliability,
            "score": round(q.score, 3),
        }
        for q in quotes
    ]

    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.dataframe(table, width="stretch", hide_index=True)
    with c2:
        chart_data = [
            {"channel": q.channel, "price": q.price_usd_per_hour} for q in quotes
        ]
        st.bar_chart(chart_data, x="channel", y="price")

    # ── Row 2: best channel / ช่องทางที่ดีที่สุด ───────────────────────
    st.subheader("🏆 ช่องทางที่ดีที่สุดตอนนี้ / Best Channel Right Now")
    best = best_channel()
    if best:
        best_q = next((q for q in quotes if q.channel == best), None)
        st.success(
            f"**{best}**"
            + (f" — ${best_q.price_usd_per_hour:.3f}/ชม. /hr (score {best_q.score:.2f})" if best_q else "")
        )
    else:
        st.warning("ยังไม่มีช่องทางพร้อมรับงาน / No channel ready to work")
else:
    st.error("ไม่สามารถสแกนตลาดได้ — เช็คการเชื่อมต่ออินเทอร์เน็ต / Cannot scan market — check your internet connection")

# ── Row 3: Revenue Split 75/20/5 ───────────────────────────────────────
st.subheader("💰 Revenue Split 75/20/5 — ตัวอย่างการแบ่งรายได้ / Example Split")
amount = st.slider(
    "รายได้จากลูกค้า (USD/วัน) / Daily customer revenue (USD)",
    min_value=10,
    max_value=5000,
    value=1000,
    step=10,
)
result = split.split(amount)
s1, s2, s3, s4 = st.columns(4)
s1.metric("รวมรายได้ / Total", f"${result.total_usd:,.2f}")
s2.metric("ผู้ให้เครื่อง (75%) / Node owners (75%)", f"${result.node_usd:,.2f}")
s3.metric("ค่าดูแลระบบ (20%) / Platform (20%)", f"${result.platform_usd:,.2f}")
s4.metric("กองทุนนักพัฒนา (5%) / Dev pool (5%)", f"${result.developer_usd:,.2f}")

# ── Row 4: daily node-owner profit / ตัวอย่างกำไรรายวัน ────────────────
st.subheader("🖥️ ตัวอย่างกำไรเจ้าของเครื่อง (จ่ายรายวัน) / Node-Owner Daily Profit Example")
gpu_count = st.slider(
    "จำนวนเครื่อง (GPU เกมมิ่ง) / Number of machines (gaming GPUs)",
    min_value=1,
    max_value=50,
    value=10,
    step=1,
)
if quotes:
    avg_price = sum(q.price_usd_per_hour for q in quotes if q.status == "connected") / max(
        1, len([q for q in quotes if q.status == "connected"])
    )
    daily_usd = gpu_count * avg_price * 24 * config.NODE_SHARE
    daily_thb = split.daily_payout(daily_usd, thb_rate=35.0)
    st.info(
        f"**{gpu_count} เครื่อง / machines** × เฉลี่ย / avg **${avg_price:.3f}/ชม. /hr** × 24ชม. /hrs × 75% "
        f"= **${daily_usd:,.2f}/วัน /day ≈ {daily_thb['thb']:,.2f} บาท/วัน / THB/day** "
        f"(อัตรา / rate 35 THB/USD)"
    )

st.divider()
st.caption(
    "ASEAN Grid prototype — ตัวเลขจากช่องทางจริง / numbers from real channels (Vast.ai / RunPod online) + ค่าประมาณ / estimates "
    "· ดูรายละเอียดเพิ่ม / more detail: /market /market/best on FastAPI · blueprint: The_ASEAN_Grid_Blueprint_v7.md"
)

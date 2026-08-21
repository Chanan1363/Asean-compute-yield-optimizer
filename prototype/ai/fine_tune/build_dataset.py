# -*- coding: utf-8 -*-
"""
ASEAN Grid — Build Fine-tuning Dataset (ข้อมูลจริงจาก Vast.ai API + จำลองช่องทางอื่น)
สร้าง `dataset.jsonl` ตาม dataset_schema.md:
  features: timestamp, region, workload_type, channels[{channel,price,queue,latency,reliability}], electricity, hour
  label:    best_channel (กำไรสุทธิสูงสุด) + net_profit_usd_per_hour

รัน: python -m prototype.ai.fine_tune.build_dataset  (จาก root repo)
"""
import json
import os
import random
import time
import urllib.request
from datetime import datetime, timezone

# ราคาฐานของแต่ละช่องทาง (USD/hr) — vast_ai ดึงสดจาก API จริง ถ้าได้
BASE_PRICES = {
    "vast_ai": 0.42,
    "io_net": 0.38,
    "render": 0.30,
    "direct_ai": 0.55,
    "studios": 0.35,
    "akash": 0.36,
}
QUEUE_BASE = {"vast_ai": 3, "io_net": 5, "render": 2, "direct_ai": 0, "studios": 1, "akash": 4}
LATENCY = {"vast_ai": 35, "io_net": 40, "render": 45, "direct_ai": 25, "studios": 30, "akash": 60}
RELIABILITY = {"vast_ai": 0.97, "io_net": 0.95, "render": 0.96, "direct_ai": 0.99, "studios": 0.98, "akash": 0.90}
ELECTRICITY_BY_REGION = {"th": 0.15, "vn": 0.12, "ph": 0.18, "id": 0.16, "my": 0.14, "sg": 0.22}
REGIONS = list(ELECTRICITY_BY_REGION)
CHANNELS = list(BASE_PRICES)
FEE_SHARE = 0.05  # ค่าธรรมเนียมช่องทาง (prototype)


def fetch_vast_live_price() -> float | None:
    """ดึงราคาสดจาก Vast.ai API (เหมือน channels.VastAIChannel)"""
    try:
        req = urllib.request.Request(
            "https://console.vast.ai/api/v0/bundles/",
            headers={"User-Agent": "ASEAN-Grid-dataset-builder/0.1", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        offers = data.get("offers") or []
        prices = [o["dph_total"] for o in offers if (o.get("dph_total") or 0) > 0]
        return round(sum(prices) / len(prices), 4) if prices else None
    except Exception:
        return None


def net_profit(price: float, kwh: float, hour: int) -> float:
    """กำไรสุทธิต่อชั่วโมง = ราคา − ค่าไฟ (ช่วงเวลามีผล) − ค่าธรรมเนียม"""
    time_factor = 0.7 if 0 <= hour < 6 else (1.3 if 6 <= hour < 18 else 1.0)
    electricity = kwh * time_factor * 0.5          # ใช้ไฟ ~50% ของชั่วโมง (prototype)
    return price - electricity - price * FEE_SHARE


def make_row(region: str, hour: int, vast_live: float | None, rng: random.Random) -> dict:
    prices = dict(BASE_PRICES)
    if vast_live is not None:
        prices["vast_ai"] = vast_live
    # ผันผวน ±10% รอบฐาน (จำลองตลาดแต่ละช่วง)
    channels = []
    for ch in CHANNELS:
        p = prices[ch] * rng.uniform(0.9, 1.1)
        channels.append({
            "channel": ch,
            "price": round(p, 4),
            "queue": max(0, QUEUE_BASE[ch] + rng.randint(-1, 1)),
            "latency": LATENCY[ch],
            "reliability": RELIABILITY[ch],
        })
    kwh = ELECTRICITY_BY_REGION[region]
    best = max(channels, key=lambda c: net_profit(c["price"], kwh, hour))
    return {
        "features": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "region": region,
            "workload_type": "ai_inference",
            "channels": channels,
            "electricity_usd_per_kwh": kwh,
            "hour_of_day": hour,
        },
        "label": {
            "best_channel": best["channel"],
            "net_profit_usd_per_hour": round(
                net_profit(best["price"], kwh, hour), 4),
        },
    }


def main() -> None:
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.jsonl")
    rng = random.Random(42)  # reproducible

    print("[1/2] ดึงราคาสดจาก Vast.ai API ...")
    vast_live = fetch_vast_live_price()
    if vast_live is None:
        print("      API ไม่ตอบ → ใช้ราคาฐาน (0.42)")
    else:
        print(f"      ได้ราคาสด: ${vast_live}/ชม.")

    print("[2/2] สร้าง dataset (6 ภูมิภาค x 6 ช่วงเวลา x 2 รอบ) ...")
    rows = []
    for region in REGIONS:
        for hour in range(0, 24, 4):        # 0,4,8,...,20
            for _ in range(2):
                rows.append(make_row(region, hour, vast_live, rng))

    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"      เขียน {len(rows)} rows → {out_path}")


if __name__ == "__main__":
    main()

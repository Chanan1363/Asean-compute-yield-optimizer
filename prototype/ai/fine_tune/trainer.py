# -*- coding: utf-8 -*-
"""
ASEAN Grid — Fine-tuning Trainer (โมเดลแรก — เรียนรู้จาก dataset จริง)

Pipeline:
  1. อ่าน dataset.jsonl (ตาม dataset_schema.md)
  2. เรียนรู้: channel_bias (กำไรสุทธิเฉลี่ยต่อช่องทาง) + region factor
  3. สร้าง `DataDrivenStrategy` (AIStrategy) → ลงทะเบียน StrategyRegistry
  4. ใช้ได้ทันที: ArbitrageEngine(strategy_name="data-driven")

โมเดลนี้เป็น "เบสไลน์เรียนรู้จากข้อมูล" — ต่อยอดเป็น Gradient Boosting/Neural net
หรือ LLM fine-tune (LoRA) ได้ โดยไม่ต้องแตะแกนระบบ (ดู strategy_hooks.py)

รัน: python -m prototype.ai.fine_tune.trainer  (จาก root repo)
"""
import json
import os
from typing import Dict, List

from prototype.ai.strategy_hooks import AIStrategy, StrategyRegistry


def load_jsonl(path: str) -> List[Dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class DataDrivenStrategy(AIStrategy):
    """
    โมเดลแรก: เรียนรู้ค่าเฉลี่ยกำไรสุทธิต่อช่องทาง (channel bias) จาก dataset
    + ปรับด้วยค่าไฟรายประเทศ/รายช่วงเวลาตอนตัดสินใจ (เหมือน scheduler)
    """

    name = "data-driven"

    def __init__(self, channel_bias: Dict[str, float]):
        self.channel_bias = channel_bias

    def _electricity_factor(self, region: str, hour: int) -> float:
        base = 0.15
        kwh = {"th": 0.15, "vn": 0.12, "ph": 0.18, "id": 0.16,
               "my": 0.14, "sg": 0.22}.get(region, base)
        time_f = 0.7 if 0 <= hour < 6 else (1.3 if 6 <= hour < 18 else 1.0)
        return kwh * time_f * 0.5   # ใช้ไฟ ~50% ของชั่วโมง

    def predict_best_channel(self, features: Dict) -> str:
        """คะแนน = ราคา − ค่าไฟ(region,hour) − ธรรมเนียม + bias(เรียนรู้จากข้อมูล)"""
        quotes = features.get("quotes", [])
        if not quotes:
            return None
        region = features.get("region", "ASEAN")
        hour = features.get("hour_of_day", 12)
        elec = self._electricity_factor(region, hour)

        def score(q):
            fee = q["price"] * 0.05
            net = q["price"] - elec - fee
            return net + self.channel_bias.get(q["channel"], 0.0)

        return max(quotes, key=score)["channel"]


def train(path: str, strategy_name: str = "data-driven") -> str:
    """เทรนโมเดลจาก dataset → register → คืนข้อความสรุป"""
    rows = load_jsonl(path)
    if not rows:
        raise ValueError("Empty dataset")

    # 1) เรียนรู้: กำไรสุทธิเฉลี่ยต่อช่องทาง (channel bias)
    profit_sum: Dict[str, float] = {}
    profit_cnt: Dict[str, int] = {}
    for row in rows:
        label = row.get("label", {})
        ch = label.get("best_channel")
        net = label.get("net_profit_usd_per_hour", 0.0)
        if ch:
            profit_sum[ch] = profit_sum.get(ch, 0.0) + net
            profit_cnt[ch] = profit_cnt.get(ch, 0) + 1
    channel_bias = {ch: round(profit_sum[ch] / profit_cnt[ch], 4) for ch in profit_sum}

    # 2) ลงทะเบียนเข้า StrategyRegistry — ระบบใช้โมเดลนี้ได้ทันที
    StrategyRegistry.register(strategy_name, DataDrivenStrategy(channel_bias))

    # 3) ตรวจผล: อัตราแม่นยำบนชุดเทรน (in-sample — prototype)
    correct = 0
    for row in rows:
        feats = dict(row["features"])
        # map ฟีเจอร์ให้ตรงกับรูปแบบ ArbitrageEngine (quotes list)
        feats["quotes"] = feats.pop("channels")
        pred = StrategyRegistry.get(strategy_name).predict_best_channel(feats)
        if pred == row["label"]["best_channel"]:
            correct += 1
    acc = correct / len(rows)

    return (f"registered '{strategy_name}' with {len(rows)} rows | "
            f"bias={channel_bias} | in-sample acc={acc:.1%}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    print(train(os.path.join(here, "dataset.jsonl")))

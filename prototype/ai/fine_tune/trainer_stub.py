"""
ASEAN Grid — Fine-tuning Trainer Stub (จุดใส่ AI จูนนิ่ง)

Stub นี้แสดง pipeline การเทรนโมเดลสำหรับ AI Hook:
  1. อ่าน dataset (JSONL ตาม dataset_schema.md)
  2. เทรนโมเดล (TODO: ใส่ pipeline จริง — Unsloth/axolotl/HF Trainer)
  3. ลงทะเบียนเข้า StrategyRegistry

Dev ที่มีโมเดลจูนของตัวเอง: ไม่ต้องใช้ไฟล์นี้ก็ได้ —
implement AIStrategy แล้ว register ได้เลย (ดู strategy_hooks.py)
"""
import json
from typing import List, Dict


def load_jsonl(path: str) -> List[Dict]:
    """อ่าน dataset แบบ JSONL → list of {features, label}"""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def train(path: str, strategy_name: str = "my-tuned-model") -> str:
    """
    TODO: ใส่ pipeline เทรนจริงตรงนี้
    ตัวอย่างทิศทาง (เลือกตามทรัพยากร):
      - ฟีเจอร์น้อย (~10 cols) → Gradient Boosting / Random Forest ก็พอ
      - ต้องการ generalize ข้ามภูมิภาค → Neural net บน normalized features
      - ต้องการโมเดลภาษาช่วยตัดสินใจ → LLM fine-tune (LoRA) + function calling
    """
    rows = load_jsonl(path)
    if not rows:
        raise ValueError("Empty dataset")

    # TODO: train_model(rows) → save artifact → wrap ใน AIStrategy

    from prototype.ai.strategy_hooks import StrategyRegistry, AIStrategy

    class TunedStrategy(AIStrategy):
        name = strategy_name

        def predict_best_channel(self, features):
            # TODO: เรียกโมเดลจริง — prototype คืน channel แรกจาก features
            quotes = features.get("quotes", [])
            return quotes[0]["channel"] if quotes else None

    StrategyRegistry.register(strategy_name, TunedStrategy())
    return f"registered strategy '{strategy_name}' with {len(rows)} training rows"

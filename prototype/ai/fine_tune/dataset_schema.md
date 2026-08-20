# Dataset Schema — สำหรับ AI จูนนิ่ง (Fine-tuning)

เอกสารนี้กำหนด schema ของ training data สำหรับทุก AI Hook ในระบบ
Dev/AI ทีมสร้าง dataset ตามนี้ → เทรน → ลงทะเบียน → ระบบใช้โมเดลจริง

---

## 1. Channel Selection (เลือกช่องทางจ่ายสูงสุด) — `predict_best_channel`

**เป้า:** พยากรณ์ว่าช่องทางใดจ่ายสูงสุดสุทธิ (หลังหักค่าไฟ/ค่าธรรมเนียม)

```json
{
  "features": {
    "timestamp_utc": "2026-08-20T10:00:00Z",
    "region": "th",
    "workload_type": "ai_inference",
    "channels": [
      {"channel": "vast_ai", "price": 0.42, "queue": 3, "latency": 35, "reliability": 0.97},
      {"channel": "io_net",  "price": 0.38, "queue": 5, "latency": 40, "reliability": 0.95},
      {"channel": "render",  "price": 0.30, "queue": 2, "latency": 45, "reliability": 0.96},
      {"channel": "direct_ai", "price": 0.55, "queue": 0, "latency": 25, "reliability": 0.99},
      {"channel": "studios", "price": 0.35, "queue": 1, "latency": 30, "reliability": 0.98}
    ],
    "electricity_usd_per_kwh": 0.15,
    "hour_of_day": 10
  },
  "label": {"best_channel": "direct_ai", "net_profit_usd_per_hour": 0.53}
}
```

**กฎ label:** `best_channel` = ช่องทางที่ให้กำไรสุทธิสูงสุด (ราคา − ค่าไฟ − ค่าธรรมเนียมช่องทาง)

---

## 2. Node Trust (คะแนนความน่าเชื่อถือโหนด) — `score_node_trust`

**เป้า:** ให้คะแนน 0-1 — โมเดลเรียนรู้ว่าสัญญาณไหนบ่งชี้โหนดโกง/ไม่เสถียร

```json
{
  "features": {
    "node_id": "n-001",
    "uptime_7d_pct": 98.5,
    "avg_task_fail_7d": 0.4,
    "stake_usd": 120.0,
    "payout_disputes": 0,
    "latency_spike_count": 2,
    "region": "vn"
  },
  "label": {"trust_score": 0.97, "verified_fraud": false}
}
```

**กฎ label:** ใช้ข้อมูลจริงหลังระบบรัน (โหนดที่ถูกจับโกง = 0)

---

## 3. Demand Forecast (พยากรณ์ดีมานด์) — `forecast_demand`

**เป้า:** คาดการณ์ดีมานด์ล่วงหน้า → scheduler จัดงานช่วงราคาดี

```json
{
  "features": {
    "region": "th",
    "hour": 20,
    "day_of_week": 4,
    "holiday": false,
    "recent_demand_24h": 0.72,
    "channel_queues": [3, 5, 2, 0, 1]
  },
  "label": {"demand_next_6h": 0.81}
}
```

---

## วิธีใช้

1. เก็บ dataset เป็น JSONL (`{"features": ..., "label": ...}` ต่อบรรทัด)
2. เทรนด้วย `trainer_stub.py` (หรือ pipeline ของคุณ — HuggingFace/axolotl/Unsloth ฯลฯ)
3. implement `AIStrategy` ใน `strategy_hooks.py` → `StrategyRegistry.register("my-model", ...)`
4. สลับใช้: `ArbitrageEngine(strategy_name="my-model")`

**หมายเหตุ:** dataset จริงจะเกิดจาก logs ของระบบเมื่อรันจริง — prototype นี้ให้ schema ไว้ก่อน

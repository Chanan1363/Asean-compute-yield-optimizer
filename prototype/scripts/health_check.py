"""ASEAN Grid — Channel Health Check
ดูสถานะทุกช่องทาง + ราคาล่าสุดในคำสั่งเดียว
รัน: python prototype/scripts/health_check.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from prototype.core.channels import CHANNEL_REGISTRY  # noqa: E402


def main() -> int:
    print("=" * 52)
    print("  ASEAN GRID — CHANNEL HEALTH CHECK")
    print("=" * 52)
    all_ok = True
    for name, ch in CHANNEL_REGISTRY.items():
        try:
            q = ch.get_quote()
            if q is None:
                print(f"  {name:<12} OFFLINE (no quote)")
                all_ok = False
            else:
                status = q.status or "ok"
                print(f"  {name:<12} {status:<8} ${q.price_usd_per_hour:.4f}/hr"
                      f"  gpus={q.available_gpus}  queue={q.queue_depth}"
                      f"  latency={q.latency_ms}ms")
        except Exception as e:  # noqa: BLE001 — health check ต้องไม่ตาย
            print(f"  {name:<12} ERROR: {type(e).__name__}: {e}")
            all_ok = False
    print("=" * 52)
    print("  ALL CHANNELS OK ✅" if all_ok else "  SOME CHANNELS DEGRADED ⚠️")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

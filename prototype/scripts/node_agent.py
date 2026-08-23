"""ASEAN Grid — Node Agent v0 (Supply Side)
เกมเมอร์รันสคริปต์นี้ -> เครื่องโผล่ในระบบ (register + ส่งชีพจรทุก 60 วิ)
แบบ "ต่อเว็บ" ก่อน (ยังไม่ต้องโหลดติดตั้ง) — ใช้ urllib มาตรฐาน ไม่ต้องติดตั้งอะไร
รัน: python node_agent.py
"""
import json, time, platform, subprocess, urllib.request

API = "https://asean-compute-yield-optimizer.onrender.com"

def post(path, payload):
    req = urllib.request.Request(API + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def detect_gpu():
    """เช็ค GPU จริง (nvidia-smi) — ถ้าไม่มี ส่ง no_gpu"""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            name, util = [x.strip() for x in out.stdout.strip().split("\n")[0].split(",")]
            return name, float(util)
    except Exception:
        pass
    return "no_gpu", 0.0

def main():
    print("=== ASEAN Grid — Node Agent v0 ===")
    gpu, util = detect_gpu()
    name = platform.node() or "gamer-pc"
    try:
        r = post("/nodes/register", {"name": name, "gpu_model": gpu, "region": "th"})
    except Exception as e:
        print("เชื่อม API ไม่ได้:", e)
        print("เช็คว่า Render deploy ใหม่แล้วหรือยัง (รอ ~2-5 นาทีหลัง push)")
        return
    node_id = r["node_id"]
    print(f"✅ ลงทะเบียนสำเร็จ: node_id={node_id} | GPU={gpu} | เครื่อง={name}")
    t0 = time.time()
    print("ส่งชีพจรทุก 60 วิ... (Ctrl+C เพื่อหยุด)")
    while True:
        try:
            gpu, util = detect_gpu()
            post("/nodes/status", {"node_id": node_id, "gpu_util_pct": util,
                                   "cpu_load_pct": 0.0, "uptime_sec": int(time.time() - t0)})
            print(f"  [{time.strftime('%H:%M:%S')}] ส่งชีพจร OK — GPU {gpu} util {util}%")
        except Exception as e:
            print(f"  [{time.strftime('%H:%M:%S')}] ส่งชีพจรพลาด: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()

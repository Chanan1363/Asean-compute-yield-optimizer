"""ASEAN Grid — Node Agent v0.5 (Supply Side)
v0: ลงทะเบียน + ส่งชีพจร → v0.5: + รับงานจริง (poll /jobs/next → รัน demo task → ส่งผล)
แบบ "ต่อเว็บ" (ยังไม่ต้องโหลดติดตั้ง) — urllib มาตรฐาน ไม่ต้องติดตั้งอะไร
รัน: python node_agent.py
"""
import json, time, platform, subprocess, urllib.request, hashlib

API = "https://asean-compute-yield-optimizer.onrender.com"

def post(path, payload):
    req = urllib.request.Request(API + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
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

def run_demo_task(job):
    """งานจำลอง (v0.5): คำนวณ hash วนตามวินาทีที่สั่ง — พิสูจน์วงจรรับ-รัน-ส่งผล
    (v1: เปลี่ยน executor นี้เป็น Docker/DeMo งานจริง — interface เดิม ไม่รื้อ)"""
    payload = job.get("payload") or {}
    seconds = max(1.0, float(payload.get("seconds", 5)))
    h = hashlib.sha256(job["job_id"].encode()).hexdigest()
    t0 = time.time()
    for _ in range(max(2000, int(seconds * 4000))):
        h = hashlib.sha256(h.encode()).hexdigest()
    elapsed = round(time.time() - t0, 2)
    return {"message": "DEMO task complete", "job_id": job["job_id"],
            "hash": h[:16], "seconds": seconds, "elapsed_sec": elapsed}, elapsed

def main():
    print("=== ASEAN Grid — Node Agent v0.5 ===")
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
    last_hb = 0.0
    print("ส่งชีพจรทุก 60 วิ + ฟังงานทุก 15 วิ... (Ctrl+C เพื่อหยุด)")
    while True:
        now = time.time()
        # ── v0: ส่งชีพจร (ทุก 60 วิ) ──
        if now - last_hb >= 60:
            try:
                gpu, util = detect_gpu()
                post("/nodes/status", {"node_id": node_id, "gpu_util_pct": util,
                                       "cpu_load_pct": 0.0, "uptime_sec": int(now - t0)})
                print(f"  [{time.strftime('%H:%M:%S')}] ส่งชีพจร OK — GPU {gpu} util {util}%")
            except Exception as e:
                print(f"  [{time.strftime('%H:%M:%S')}] ส่งชีพจรพลาด: {e}")
            last_hb = now
        # ── v0.5: ขอรับงาน → รัน → ส่งผล ──
        try:
            r = post("/jobs/next", {"node_id": node_id})
            job = r.get("job")
            if job:
                print(f"📥 ได้งาน {job['job_id']} ({job['job_type']}) — เริ่มรัน...")
                post(f"/jobs/{job['job_id']}/start", {"node_id": node_id})
                result, elapsed = run_demo_task(job)
                post(f"/jobs/{job['job_id']}/result",
                     {"node_id": node_id, "result": result, "elapsed_sec": elapsed})
                print(f"✅ {job['job_id']} เสร็จ ({elapsed}s) — hash: {result['hash']}")
        except Exception as e:
            print(f"⚠️ ฟังงานพลาด: {e}")
        time.sleep(15)

if __name__ == "__main__":
    main()

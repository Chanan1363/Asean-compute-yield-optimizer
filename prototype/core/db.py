"""ASEAN Grid — Node + Job DB (Postgres / SQLite)
- ตั้ง DATABASE_URL (env) → ใช้ Postgres (ข้อมูลถาวร — Supabase/Neon)
- ไม่ตั้ง → ใช้ SQLite (fallback — ทดลองในเครื่อง)
หลัก no dead-end: interface เดียว เปลี่ยน backend ได้โดยไม่แตะโค้ดอื่น
"""
import json, time, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'nodes.db')
DATABASE_URL = os.environ.get("DATABASE_URL", "")

class _DB:
    """wrapper เล็ก: ทำให้ sqlite3 กับ psycopg2 ใช้ interface เดียวกัน
    (execute/fetchone/fetchall/commit/close — เหมือน sqlite3 เดิม)"""
    def __init__(self):
        if DATABASE_URL:
            # pg8000 = pure Python (ติดตั้งได้ทุก Python แม้ 3.14 — ไม่ต้อง compile)
            import ssl
            from urllib.parse import urlparse
            import pg8000
            u = urlparse(DATABASE_URL)
            kwargs = dict(user=u.username, password=u.password, host=u.hostname,
                          port=u.port or 5432, database=u.path.lstrip('/'))
            try:  # ลอง SSL verify (certifi) ก่อน
                try:
                    import certifi
                    ctx = ssl.create_default_context(cafile=certifi.where())
                except ImportError:
                    ctx = ssl.create_default_context()
                self.conn = pg8000.connect(**kwargs, ssl_context=ctx)
            except Exception:
                # fallback: ไม่ verify cert (กัน proxy/CA store แปลก) — เหมาะ prototype
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                self.conn = pg8000.connect(**kwargs, ssl_context=ctx)
            self._pg = True
        else:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            import sqlite3
            self.conn = sqlite3.connect(DB_PATH)
            self._pg = False
        self.cur = self.conn.cursor()

    def execute(self, sql, params=None):
        # SQLite ใช้ ? / Postgres ใช้ %s — แปลงอัตโนมัติ
        if self._pg:
            sql = sql.replace("?", "%s")
        self.cur.execute(sql, params or ())
        return self

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()

    def commit(self):
        self.conn.commit()
        return self

    def close(self):
        try:
            self.cur.close()
        except Exception:
            pass
        self.conn.close()

def _conn():
    """เชื่อมต่อ + สร้างตาราง (schema เดียวกันทั้ง 2 backend)"""
    c = _DB()
    c.execute("""CREATE TABLE IF NOT EXISTS nodes (
        node_id TEXT PRIMARY KEY,
        name TEXT, gpu_model TEXT, region TEXT,
        status TEXT, gpu_util_pct REAL, uptime_sec INTEGER,
        last_seen_ts REAL, history TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        job_type TEXT, gpu_model TEXT, gpu_count INTEGER, hours REAL,
        status TEXT, node_id TEXT,
        payload TEXT, result TEXT, elapsed_sec REAL,
        created_ts REAL, assigned_ts REAL, done_ts REAL)""")
    c.commit()
    return c

# ────────────────────────── NODES ──────────────────────────

def register(node_id, name, gpu_model, region):
    """ลงทะเบียนโหนด (upsert — กันซ้ำ)"""
    c = _conn()
    if c._pg:
        c.execute("INSERT INTO nodes (node_id, name, gpu_model, region, status, gpu_util_pct, uptime_sec, last_seen_ts, history) "
                  "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT (node_id) DO UPDATE SET "
                  "name=EXCLUDED.name, gpu_model=EXCLUDED.gpu_model, region=EXCLUDED.region, status='online'",
                  (node_id, name, gpu_model, region, 'online', 0.0, 0, None, '[]'))
    else:
        c.execute("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?,?,?,?)",
                  (node_id, name, gpu_model, region, 'online', 0.0, 0, None, '[]'))
    c.commit(); c.close()

def update_status(node_id, gpu_util_pct, uptime_sec):
    """อัปเดตชีพจร + ต่อ history (เก็บ 20 ค่าล่าสุด)"""
    c = _conn()
    row = c.execute("SELECT history FROM nodes WHERE node_id=?", (node_id,)).fetchone()
    if not row:
        c.close()
        return False
    hist = json.loads(row[0])
    hist.append(gpu_util_pct)
    hist = hist[-20:]
    c.execute("UPDATE nodes SET status='online', gpu_util_pct=?, uptime_sec=?, last_seen_ts=?, history=? WHERE node_id=?",
              (gpu_util_pct, uptime_sec, time.time(), json.dumps(hist), node_id))
    c.commit(); c.close()
    return True

def all_nodes():
    """โหนดทั้งหมด (แปลง history กลับเป็น list)"""
    c = _conn()
    rows = c.execute("SELECT * FROM nodes").fetchall()
    c.close()
    cols = ['node_id', 'name', 'gpu_model', 'region', 'status',
            'gpu_util_pct', 'uptime_sec', 'last_seen_ts', 'history']
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        try:
            d['history'] = json.loads(d['history'])
        except Exception:
            d['history'] = []
        out.append(d)
    return out

def exists(node_id):
    c = _conn()
    row = c.execute("SELECT 1 FROM nodes WHERE node_id=?", (node_id,)).fetchone()
    c.close()
    return row is not None

# ────────────────────────── JOBS ──────────────────────────

JOB_COLS = ['job_id', 'job_type', 'gpu_model', 'gpu_count', 'hours', 'status',
            'node_id', 'payload', 'result', 'elapsed_sec',
            'created_ts', 'assigned_ts', 'done_ts']

def _job_from_row(r):
    if not r:
        return None
    d = dict(zip(JOB_COLS, r))
    for k in ('payload', 'result'):
        try:
            d[k] = json.loads(d[k]) if d[k] else None
        except Exception:
            d[k] = None
    return d

def create_job(job_type, gpu_model, gpu_count, hours, payload=None):
    """สร้างงานใหม่ (queued) -> คืน job_id"""
    c = _conn()
    rows = c.execute("SELECT job_id FROM jobs").fetchall()
    n = max((int(r[0][1:]) for r in rows if r[0][1:].isdigit()), default=0) + 1
    job_id = f"j{n:03d}"
    c.execute("INSERT INTO jobs (job_id, job_type, gpu_model, gpu_count, hours, status, payload, created_ts) VALUES (?,?,?,?,?,?,?,?)",
              (job_id, job_type, gpu_model, gpu_count, hours, 'queued',
               json.dumps(payload or {}), time.time()))
    c.commit(); c.close()
    return job_id

def get_job(job_id):
    c = _conn()
    r = c.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    c.close()
    return _job_from_row(r)

def claim_next_job(node_id):
    """โหนดขอรับงาน: คืน job queued ตัวแรก (FIFO) + mark assigned ให้โหนดนี้
    (v0.5 scheduler แบบง่าย: โหนดที่ poll มาก่อน = ได้งานก่อน; v1 ต่อ trust/tariff)"""
    c = _conn()
    row = c.execute("SELECT job_id FROM jobs WHERE status='queued' ORDER BY created_ts LIMIT 1").fetchone()
    if not row:
        c.close()
        return None
    c.execute("UPDATE jobs SET status='assigned', node_id=?, assigned_ts=? WHERE job_id=?",
              (node_id, time.time(), row[0]))
    c.commit()
    job = _job_from_row(c.execute("SELECT * FROM jobs WHERE job_id=?", (row[0],)).fetchone())
    c.close()
    return job

def mark_running(job_id, node_id):
    """โหนดยืนยันเริ่มรัน (assigned -> running)"""
    c = _conn()
    c.execute("UPDATE jobs SET status='running' WHERE job_id=? AND node_id=?", (job_id, node_id))
    c.commit(); c.close()

def submit_result(job_id, node_id, result, elapsed_sec):
    """ส่งผลงาน (ต้องเป็นโหนดเจ้าของงาน) -> done"""
    c = _conn()
    row = c.execute("SELECT 1 FROM jobs WHERE job_id=? AND node_id=?", (job_id, node_id)).fetchone()
    if not row:
        c.close()
        return False
    c.execute("UPDATE jobs SET status='done', result=?, elapsed_sec=?, done_ts=? WHERE job_id=?",
              (json.dumps(result, ensure_ascii=False), elapsed_sec, time.time(), job_id))
    c.commit(); c.close()
    return True

def fail_job(job_id, node_id):
    """โหนดแจ้งงานล้มเหลว (optional — requeue_stale คุ้มครองค้างอยู่แล้ว)"""
    c = _conn()
    c.execute("UPDATE jobs SET status='failed' WHERE job_id=? AND node_id=?", (job_id, node_id))
    c.commit(); c.close()

def requeue_stale(timeout_sec=300):
    """no dead-end: งาน assigned/running ค้างเกิน 5 นาที -> กลับ queued (โหนดอื่นรับต่อ)"""
    c = _conn()
    cutoff = time.time() - timeout_sec
    c.execute("UPDATE jobs SET status='queued', node_id=NULL, assigned_ts=NULL "
              "WHERE status IN ('assigned','running') AND assigned_ts IS NOT NULL AND assigned_ts < ?",
              (cutoff,))
    c.commit(); c.close()

def all_jobs(limit=50):
    """งานทั้งหมด (ล่าสุดก่อน) — ลูกค้าดู / admin ดู"""
    c = _conn()
    rows = c.execute("SELECT * FROM jobs ORDER BY created_ts DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [_job_from_row(r) for r in rows]

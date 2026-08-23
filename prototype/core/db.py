"""ASEAN Grid — Node DB (SQLite)
เก็บโหนดถาวร (ไม่หายเมื่อ process restart / Render wake)
อนาคต: เปลี่ยน backend เป็น Postgres ได้ — แค่เปลี่ยน connection (interface เดิม)
"""
import sqlite3, json, time, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'nodes.db')

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS nodes (
        node_id TEXT PRIMARY KEY,
        name TEXT, gpu_model TEXT, region TEXT,
        status TEXT, gpu_util_pct REAL, uptime_sec INTEGER,
        last_seen_ts REAL, history TEXT)""")
    return c

def register(node_id, name, gpu_model, region):
    """ลงทะเบียนโหนด (INSERT OR REPLACE)"""
    c = _conn()
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

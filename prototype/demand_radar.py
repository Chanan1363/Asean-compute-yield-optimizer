"""
ASEAN Grid — Demand Radar v0.1 (prototype)
สแกนหาคนที่ "กำลังต้องการ GPU/compute" จากโลกจริง (Reddit + Hacker News)
เหมือนอัลกอริทึม FB: หาคนที่ Interest ตรงกับที่เราขาย แล้วยิงตรงถึงเขา

วิธีรัน: python prototype/demand_radar.py
"""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List

# ── คำที่บ่งบอก "กำลังต้องการ" (interest signals) ─────────────────────
BUY_INTENT = [
    "need gpu", "looking for gpu", "need a gpu", "want to rent", "rent gpu",
    "rent a gpu", "gpu rental", "cheap gpu", "affordable gpu", "budget gpu",
    "where to rent", "gpu for training", "gpu for inference", "need compute",
    "looking for compute", "affordable compute", "cheap compute",
    "gpu cloud", "rent compute", "need a cluster", "gpu prices too high",
    "can't afford", "too expensive", "h100 rental", "4090 rental",
]
CONTEXT_WORDS = ["ai", "ml", "model", "training", "inference", "llm", "fine-tune",
                 "render", "startup", "research", "experiment", "server", "workstation"]


def fetch_json(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def score_post(title: str, selftext: str = "") -> Dict[str, float]:
    """ให้คะแนนความต้องการ: ยิ่งตรง keyword ยิ่งสูง (0-100)"""
    text = f"{title} {selftext}".lower()
    score = 0.0
    hits = []
    for kw in BUY_INTENT:
        if kw in text:
            score += 15.0 if kw.startswith("rent") else 12.0
            hits.append(kw)
    ctx = sum(1 for w in CONTEXT_WORDS if w in text)
    score += min(ctx * 2.0, 10.0)          # บริบท AI/ML ช่วยยืนยัน
    # คำว่า "want/need/looking" ใน title = ตั้งใจแรง
    if re.search(r"\b(need|want|looking|where|how)\b", title.lower()):
        score += 5.0
    return {"score": round(min(score, 100), 1), "keywords": hits}


# ── 1. สแกน Reddit ───────────────────────────────────────────────────
SUBREDDITS = ["LocalLLaMA", "selfhosted", "MLQuestions", "StableDiffusion", "HomeServer"]


def scan_reddit(max_per_sub: int = 8) -> List[dict]:
    found = []
    for sub in SUBREDDITS:
        q = urllib.parse.quote("(GPU OR compute) AND (need OR looking OR rent OR cheap OR affordable)")
        url = f"https://old.reddit.com/r/{sub}/search.json?q={q}&restrict_sr=1&sort=new&limit={max_per_sub}"
        try:
            data = fetch_json(url)
            for child in data.get("data", {}).get("children", []):
                p = child.get("data", {})
                title = p.get("title", "")
                selftext = (p.get("selftext") or "")[:400]
                created = p.get("created_utc", 0)
                age_days = (time.time() - created) / 86400
                if age_days > 14:            # เอาเฉพาะ 14 วันล่าสุด
                    continue
                s = score_post(title, selftext)
                if s["score"] >= 15:          # กรองเฉพาะที่มีสัญญาณชัด
                    found.append({
                        "source": f"reddit/r/{sub}",
                        "title": title[:120],
                        "score": s["score"],
                        "keywords": s["keywords"][:3],
                        "age_days": round(age_days, 1),
                        "url": f"https://www.reddit.com{p.get('permalink','')}",
                    })
            time.sleep(1.5)                  # กัน rate-limit
        except Exception as e:
            print(f"  [skip] r/{sub}: {str(e)[:60]}")
    return found


# ── 2. สแกน Hacker News ──────────────────────────────────────────────
def scan_hackernews(max_items: int = 10) -> List[dict]:
    found = []
    # รอบ 1: ล่าสุด 45 วัน (สัญญาณสด — ยิงได้เลย)
    for query in ["rent GPU", "cheap GPU compute", "need compute AI", "GPU cloud affordable", "where rent GPU", "looking for GPU"]:
        q = urllib.parse.quote(query)
        url = f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage=8&numericFilters=created_at_i>{int(time.time())-45*86400}"
        try:
            data = fetch_json(url)
            for h in data.get("hits", []):
                title = h.get("title") or ""
                s = score_post(title)
                if s["score"] >= 15:
                    found.append({
                        "source": "hackernews",
                        "title": title[:120],
                        "score": s["score"],
                        "keywords": s["keywords"][:3],
                        "age_days": round((time.time() - h.get("created_at_i", 0)) / 86400, 1),
                        "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    })
        except Exception as e:
            print(f"  [skip] HN '{query}': {str(e)[:60]}")
    # รอบ 2: relevance สูงสุดทุกยุค (สัญญาณถาวร — ตลาด/บทวิเคราะห์)
    for query in ["rent GPU", "GPU rental market", "GPU shortage"]:
        q = urllib.parse.quote(query)
        url = f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage=6"
        try:
            data = fetch_json(url)
            for h in data.get("hits", []):
                title = h.get("title") or ""
                s = score_post(title)
                if s["score"] >= 15:
                    found.append({
                        "source": "hackernews (trend)",
                        "title": title[:120],
                        "score": s["score"],
                        "keywords": s["keywords"][:3],
                        "age_days": round((time.time() - h.get("created_at_i", 0)) / 86400, 1),
                        "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    })
        except Exception as e:
            print(f"  [skip] HN-trend '{query}': {str(e)[:60]}")
    return found


# ── 3. สแกน Lobste.rs (API เปิด สาย dev/selfhost) ────────────────────
def scan_lobsters(max_items: int = 15) -> List[dict]:
    found = []
    try:
        data = fetch_json("https://lobste.rs/newest.json", timeout=15)
        for s in data[:max_items]:
            title = s.get("title") or ""
            score = score_post(title)
            if score["score"] >= 15:
                found.append({
                    "source": "lobsters",
                    "title": title[:120],
                    "score": score["score"],
                    "keywords": score["keywords"][:3],
                    "age_days": 0.1,
                    "url": s.get("url") or f"https://lobste.rs{s.get('short_id_url','')}",
                })
    except Exception as e:
        print(f"  [skip] Lobsters: {str(e)[:60]}")
    return found


# ── main ─────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 64)
    print("  ASEAN GRID — DEMAND RADAR v0.1 (สแกนความต้องการ GPU จากโลกจริง)")
    print("  ค้นหาคนที่ 'กำลังต้องการ' — เหมือน FB algorithm หา interest")
    print("=" * 64)

    print("\n[1] สแกน Hacker News (rent GPU / cheap compute / need compute)...")
    hn = scan_hackernews()
    print(f"    เจอ {len(hn)} โพสต์ที่มีสัญญาณต้องการ")

    print("\n[2] สแกน Lobste.rs (dev/selfhost สายใหม่)...")
    lob = scan_lobsters()
    print(f"    เจอ {len(lob)} โพสต์ที่มีสัญญาณต้องการ")

    print("\n[3] สแกน Reddit... (API ถูกบล็อก — รอต่อ OAuth ใน v0.2)")
    reddit = []
    print(f"    เจอ {len(reddit)} โพสต์ที่มีสัญญาณต้องการ (ข้าม — 403/404)")

    all_hits = sorted(hn + lob + reddit, key=lambda x: -x["score"])
    print("\n" + "=" * 64)
    print(f"  ผลรวม: {len(all_hits)} สัญญาณดีมานด์ (คะแนน 15+ / 100)")
    print("=" * 64)
    for h in all_hits[:20]:
        print(f"\n  [{h['score']:>5}/100] {h['source']} ({h['age_days']} วันที่แล้ว)")
        print(f"    {h['title']}")
        print(f"    คำที่เจอ: {', '.join(h['keywords'])}")
        print(f"    {h['url']}")

    print("\n" + "=" * 64)
    print("  ต่อไป: ยิงตรงถึงคนเหล่านี้ (DM/email) — 'เรามี GPU ราคาถูกในอาเซียน'")
    print("=" * 64)


if __name__ == "__main__":
    main()

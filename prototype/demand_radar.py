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
    # ── กลุ่มเป้าหมาย Phase 1 (มหาวิทยาลัย/นักวิจัย/ธุรกิจ) ──
    "fine-tune", "fine tuning", "finetune", "finetuning", "fine tune",
    "research gpu", "gpu for research", "research compute", "university gpu",
    "student gpu", "academic compute", "lab gpu", "gpu for lab",
    "corporate ai", "business ai", "small model", "small-scale training",
    "gpu grant", "gpu budget", "research budget", "student budget",
]
CONTEXT_WORDS = ["ai", "ml", "model", "training", "inference", "llm", "fine-tune",
                 "render", "startup", "research", "researcher", "university",
                 "student", "academic", "corporate", "business", "experiment",
                 "server", "workstation", "lab", "laboratory", "thesis", "paper"]


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
    for query in ["rent GPU", "cheap GPU compute", "need compute AI", "GPU cloud affordable",
                  "where rent GPU", "looking for GPU", "fine-tune GPU", "fine tuning GPU",
                  "GPU for research", "university GPU", "student GPU", "academic compute",
                  "GPU for lab", "small model training", "research compute budget"]:
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


# ── 4. Area Sweep — กวาดพื้นที่หาลูกค้าเป้าหมายทั่วอาเซียน (OSM ฟรี) ──
# ใช้ Overpass API ตรงๆ (OpenStreetMap) — หาบริษัท IT/บริษัทรับจ้างเทรน AI/
# สถาบันวิจัย/มหาวิทยาลัย ในเมืองหลักอาเซียน — เหมือน Google Maps กวาดพื้นที่
# แต่ฟรี ไม่ต้องใช้ API key
ASEAN_CITIES = [
    # (เมือง, ประเทศ, lat, lon, รัศมี กม.)
    ("Bangkok", "Thailand", 13.7563, 100.5018, 12),
    ("Singapore", "Singapore", 1.3521, 103.8198, 10),
    ("Kuala Lumpur", "Malaysia", 3.1390, 101.6869, 12),
    ("Manila", "Philippines", 14.5995, 120.9842, 10),
    ("Ho Chi Minh City", "Vietnam", 10.8231, 106.6297, 10),
    ("Hanoi", "Vietnam", 21.0278, 105.8342, 10),
    ("Yangon", "Myanmar", 16.8409, 96.1735, 10),
    ("Vientiane", "Laos", 17.9757, 102.6331, 8),
    ("Jakarta", "Indonesia", -6.2088, 106.8456, 12),
]

# ประเภทสถานที่ที่อาจเป็นลูกค้า (บริษัทเทรน AI/สถาบันวิจัย/มหาวิทยาลัย)
SWEEP_TAGS = [
    ("office=it", "บริษัท IT/tech", 12.0),
    ("amenity=research_institute", "สถาบันวิจัย", 14.0),
    ("amenity=university", "มหาวิทยาลัย", 15.0),
]


def _overpass_query(bbox_s: float, bbox_w: float, bbox_n: float, bbox_e: float,
                    tag: str, limit: int = 12) -> list:
    """ยิง Overpass API — หา node/way ตาม tag ในกรอบพื้นที่ (มี mirror + retry)"""
    query = f"""
    [out:json][timeout:20];
    (node["{tag.split('=')[0]}"="{tag.split('=')[1]}"]({bbox_s},{bbox_w},{bbox_n},{bbox_e});
     way["{tag.split('=')[0]}"="{tag.split('=')[1]}"]({bbox_s},{bbox_w},{bbox_n},{bbox_e}););
    out center {limit};
    """
    mirrors = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]
    last_err = None
    for m in mirrors:
        try:
            data = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(m, data=data,
                                         headers={"User-Agent": "ASEAN-Grid-DemandRadar/0.2"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8")).get("elements", [])
        except Exception as e:
            last_err = e
            continue
    raise last_err if last_err else RuntimeError("overpass all mirrors failed")


# จุดสำคัญถาวร (anchor targets) — หน่วยงาน/สถานที่ที่รู้อยู่แล้วว่าเป็นเป้าหมาย
ANCHOR_TARGETS = [
    {
        "name": "กระทรวงการอุดมศึกษา วิทยาศาสตร์ วิจัยและนวัตกรรม (อว.) — ถนนศรีอยุธยา (ข้าง สน.พญาไท)",
        "city": "Bangkok, Thailand",
        "lat": 13.75941, "lon": 100.53018,
        "score": 16.0, "category": "หน่วยงานรัฐ/วิจัย",
        "url": "https://www.google.com/maps/search/?api=1&query=13.75941,100.53018",
    },
    {
        "name": "สวทช. / NSTDA — อุทยานวิทยาศาสตร์ประเทศไทย (คลองหลวง)",
        "city": "Pathum Thani, Thailand",
        "lat": 14.0775833, "lon": 100.6026353,
        "score": 17.0, "category": "หน่วยงานวิจัยแห่งชาติ",
        "url": "https://www.google.com/maps/search/?api=1&query=14.0775833,100.6026353",
    },
    {
        "name": "AIT — สถาบันเทคโนโลยีแห่งเอเชีย (คลองหลวง)",
        "city": "Pathum Thani, Thailand",
        "lat": 14.0803261, "lon": 100.611434,
        "score": 15.0, "category": "มหาวิทยาลัยนานาชาติ/วิจัย",
        "url": "https://www.google.com/maps/search/?api=1&query=14.0803261,100.611434",
    },
    {
        "name": "มหาวิทยาลัยธรรมศาสตร์ ศูนย์รังสิต",
        "city": "Pathum Thani, Thailand",
        "lat": 14.0727746, "lon": 100.6069099,
        "score": 15.0, "category": "มหาวิทยาลัย",
        "url": "https://www.google.com/maps/search/?api=1&query=14.0727746,100.6069099",
    },
]


def sweep_asean(limit_per_tag: int = 8) -> List[dict]:
    """กวาด 9 เมืองอาเซียน → หาบริษัท/สถาบันที่อาจต้องการ GPU ราคาถูก"""
    found = []
    # anchor targets ก่อน (รู้อยู่แล้วว่าเป็นเป้าหมาย)
    for a in ANCHOR_TARGETS:
        found.append({
            "source": f"anchor/{a['city']}",
            "title": f"[{a['category']}] {a['name']}",
            "score": a["score"],
            "keywords": [a["category"]],
            "age_days": 0.0,
            "url": a["url"],
            "category": a["category"],
        })
    for city, country, lat, lon, radius_km in ASEAN_CITIES:
        # แปลงรัศมี กม. → องศา (1 องศา ≈ 111 กม.)
        d = radius_km / 111.0
        bbox = (lat - d, lon - d, lat + d, lon + d)
        city_hits = 0
        for tag, label, base_score in SWEEP_TAGS:
            try:
                elems = _overpass_query(*bbox, tag, limit_per_tag)
                for el in elems[:limit_per_tag]:
                    name = el.get("tags", {}).get("name", "")
                    if not name:
                        continue
                    clat = el.get("lat") or el.get("center", {}).get("lat")
                    clon = el.get("lon") or el.get("center", {}).get("lon")
                    if clat is None:
                        continue
                    found.append({
                        "source": f"area/{city}, {country}",
                        "title": f"[{label}] {name[:90]}",
                        "score": base_score,
                        "keywords": [label],
                        "age_days": 0.0,
                        "url": f"https://www.google.com/maps/search/?api=1&query={clat:.5f},{clon:.5f}",
                        "category": label,
                    })
                    city_hits += 1
            except Exception as e:
                print(f"  [skip] {city}/{tag}: {str(e)[:50]}")
        print(f"    {city:<20} ({country}) → เจอ {city_hits} แห่ง")
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

    print("\n[4] กวาดพื้นที่อาเซียน 9 เมือง (Area Sweep): หาบริษัท IT/สถาบันวิจัย/มหาวิทยาลัย...")
    area = sweep_asean(limit_per_tag=6)
    print(f"    รวม: เจอ {len(area)} สถานที่เป้าหมายทั่วอาเซียน")

    all_hits = sorted(hn + lob + reddit + area, key=lambda x: -x["score"])
    # dedupe — เอา URL ซ้ำออก เหลือรายการเดียว (คะแนนสูงสุด)
    seen_urls = set()
    deduped = []
    for h in all_hits:
        u = h["url"]
        if u not in seen_urls:
            seen_urls.add(u)
            deduped.append(h)
    all_hits = deduped
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

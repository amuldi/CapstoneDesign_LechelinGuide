"""후보 매장 → 메뉴 분류 → 항목 언급 집계(룰 기반) → 데모용 JSON."""
import duckdb, pandas as pd, json, re, pathlib
import lexicon
import re as _re
ASPECT_KEYS = list(lexicon.ASPECTS)

OUT = pathlib.Path(__file__).parent.parent / "data"
con = duckdb.connect()
con.execute("CREATE VIEW gn AS SELECT * FROM '../data/gangnam_reviews.parquet'")
cand = pd.read_csv("../data/gangnam_candidates.csv")

# ---------- 1. 별점 변별력 확인 ----------
print("=== 후보 55곳 평균 별점 분포 ===")
print(f"최저 {cand.avg_rating.min():.2f} / 최고 {cand.avg_rating.max():.2f} "
      f"/ 중앙값 {cand.avg_rating.median():.2f} / 표준편차 {cand.avg_rating.std():.3f}")
print((cand.avg_rating.round(1).value_counts().sort_index()).to_string())

# ---------- 2. 메뉴 분류 ----------
MENU_RULES = [
  ("치킨",     r"치킨|통닭|닭강정"),
  ("피자",     r"피자"),
  ("국밥",     r"국밥|해장"),
  ("볶음밥",   r"볶음밥|김볶|라이스"),
  ("타코",     r"타코"),
  ("포케·샐러드", r"포케|샐러드|샐러디"),
  ("마라탕",   r"마라탕|마라"),
  ("족발·보쌈", r"족발|보쌈|구구족"),
  ("찌개·짜글이", r"찌개|짜글이"),
  ("아구찜·해물찜", r"아구찜|해물찜"),
  ("도넛",     r"도넛"),
]
def classify(name):
    for menu, pat in MENU_RULES:
        if re.search(pat, str(name)):
            return menu
    return None

cand["menu"] = cand["name"].map(classify)
grouped = cand.dropna(subset=["menu"])
print("\n=== 메뉴별 후보 수 ===")
print(grouped.groupby("menu").size().sort_values(ascending=False).to_string())

# ---------- 3. 항목 언급 집계 (룰 기반 1차) ----------
ASPECTS = {
  "맛":    r"맛있|맛없|맛은|맛이|맛도|풍미|간이|간은|비리|짜요|짭|싱겁|느끼|담백|고소",
  "양":    r"양이|양은|양도|양만|푸짐|넉넉|적어|많아|부족|배부|가득|실하",
  "가격":  r"가격|가성비|비싸|저렴|혜자|값|돈값|합리적|만원|할인",
  "서비스": r"친절|불친절|응대|사장님|서비스|요청사항|챙겨|신경\s*써|사장",
  "배달":  r"배달|배송|늦게|빨리|식어|새서|포장|흘러|기사|도착|따뜻",
}
NEG = (r"(?<!지 )없|안\s|않|못|아쉽|별로|실망|적어|부족|늦|식어|새서|흘러|비싸|불친절|"
       r"느리|짜요|싱겁|다신|최악|비려|눅눅|차갑|이상|불편|별루|구려|질겨")

def split_clauses(t):
    """리뷰를 절 단위로 쪼갭니다. 한 문장에 항목이 섞여 있으면 감성이 뒤섞입니다."""
    return [c for c in re.split(r"[.!?~\n]+|\s(?:근데|그런데|다만|하지만|však)\s", str(t)) if len(c) > 4]

con.register("cand", grouped)
rows = con.sql("""
SELECT c.menu, c.name, c.business_number, c.addr, c.platforms,
       c.reviews, c.text_reviews, c.avg_rating,
       g.platform, g.content, g.created_at, TRY_CAST(g.rating AS DOUBLE) AS rating
FROM gn g JOIN cand c
  ON g.business_number = c.business_number
 AND regexp_replace(g.shop_address, '\\s+', ' ', 'g') = c.addr
WHERE g.content IS NOT NULL AND length(trim(g.content)) >= 1
""").df()

EVENT = r"리뷰\s*이벤트|이벤트\s*참여|서비스\s*받|사장님\s*덕분에\s*리뷰|별점\s*5점\s*드려|리뷰\s*쓰고"
result = {}
for (menu, name), g in rows.groupby(["menu", "name"]):
    txt = g.content.fillna("")
    excl_event = txt.str.contains(EVENT, regex=True).sum()
    dup = len(txt) - txt.nunique()
    keep = g[~txt.str.contains(EVENT, regex=True)]

    # lexicon.py 규칙으로 항목별 극성 판정
    tally = {a: [0, 0] for a in ASPECT_KEYS}
    no_signal = 0
    cands = {a: [] for a in ASPECT_KEYS}      # 근거 후보
    for r in keep.itertuples():
        res = lexicon.analyze(r.content)
        if not res:
            no_signal += 1
            continue
        for a, pol in res.items():
            tally[a][0 if pol > 0 else 1] += 1
        # 근거 후보: 극성이 한쪽으로만 명확한 리뷰 (혼합은 대표로 부적합)
        if 18 <= len(r.content) <= 85:
            hasP = bool(_re.search(lexicon.POS, r.content))
            hasN = bool(_re.search(lexicon.NEG, r.content))
            hypo = bool(lexicon.HYPO.search(r.content))
            clean_pos = hasP and not hasN and not hypo
            clean_neg = hasN and not hasP and not hypo
            for a, pol in res.items():
                if pol > 0 and not clean_pos: continue
                if pol < 0 and not clean_neg: continue
                cands[a].append((r.content.strip().replace("\n", " "), r.platform,
                                 str(r.created_at)[:10].replace("-", "."), pol, len(res)))
    aspects = [{"name": a, "pos": tally[a][0], "neu": 0, "neg": tally[a][1]} for a in ASPECT_KEYS]

    # 언급 많은 상위 2개 항목에서 긍정 1 + 부정 1씩 — 장단점을 같이 보여줍니다
    ev, used = [], set()
    for a in sorted(ASPECT_KEYS, key=lambda a: -sum(tally[a]))[:3]:
        for want in (1, -1):
            pool = sorted([c for c in cands[a] if c[3] == want], key=lambda c: c[4])
            for c in pool:
                if c[0] in used: continue
                ev.append({"aspect": a, "tone": "pos" if want > 0 else "neg",
                           "platform": c[1], "date": c[2], "text": c[0][:95]})
                used.add(c[0]); break
        if len(ev) >= 4: break

    plats = (g.groupby("platform")
               .agg(reviews=("content", "size"), rating=("rating", "mean"))
               .reset_index().sort_values("reviews", ascending=False))
    result.setdefault(menu, []).append({
        "name": name, "addr": g.addr.iloc[0], "avg_rating": float(g.avg_rating.iloc[0]),
        "text_reviews": int(g.text_reviews.iloc[0]),
        "platforms": [{"name": {"BAEMIN":"배민","CPEATS":"쿠팡이츠","YOGIYO":"요기요","NAVER":"네이버"}.get(p.platform, p.platform),
                       "reviews": int(p.reviews),
                       "rating": round(float(p.rating), 2) if pd.notna(p.rating) else None}
                      for p in plats.itertuples()],
        "aspects": aspects, "evidence": ev,
        "excluded": [{"reason": "리뷰 이벤트 키워드 패턴 탐지", "count": int(excl_event)},
                     {"reason": "동일 문구 반복", "count": int(dup)},
                     {"reason": "항목 언급이 없는 리뷰", "count": int(no_signal)}],
        "five_pct": round(100 * (g.rating == 5).sum() / g.rating.notna().sum(), 1),
    })

# 메뉴별로 후보 전원을 내보냅니다. 정렬은 화면에서 사용자가 고른 항목 기준으로.
def rate(a):
    t = a["pos"] + a["neg"]
    return round(100 * a["pos"] / t, 1) if t else None

MENUS = []
for menu, stores in result.items():
    if len(stores) < 2: continue
    for s_ in stores:
        s_["scores"] = {a["name"]: rate(a) for a in s_["aspects"]}
        s_["mentions"] = {a["name"]: a["pos"] + a["neg"] for a in s_["aspects"]}
        tot = sum(a["pos"] + a["neg"] for a in s_["aspects"])
        s_["overall"] = round(100 * sum(a["pos"] for a in s_["aspects"]) / tot, 1) if tot else 0
    stores.sort(key=lambda x: -x["overall"])
    MENUS.append({
        "menu": menu,
        "candidates": [{
            "name": x["name"], "address": x["addr"], "asOf": "2026.09.30",
            "avgRating": x["avg_rating"], "fivePct": x["five_pct"],
            "textReviews": x["text_reviews"], "overall": x["overall"],
            "scores": x["scores"], "mentions": x["mentions"],
            "aspects": x["aspects"], "platforms": x["platforms"],
            "evidence": x["evidence"], "excluded": x["excluded"],
        } for x in stores],
    })

MENUS.sort(key=lambda m: -len(m["candidates"]))
(OUT / "demo_data.json").write_text(json.dumps(MENUS, ensure_ascii=False, indent=1))
print(f"\n=== 메뉴 {len(MENUS)}개 · 후보 {sum(len(m['candidates']) for m in MENUS)}곳 ===")
for m in MENUS:
    w = m["candidates"][0]
    print(f"{m['menu']:>10} {len(m['candidates'])}곳 → {w['name']} (종합 {w['overall']})")

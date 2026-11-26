"""규칙 · LLM · 혼합 방식을 사람 정답셋으로 비교합니다.

사용법
  1) 사람 라벨링: labeling/holdout_150.csv 의 맛/양/가격/서비스/배달 칸을
     "긍정" / "부정" / 빈칸(언급 없음) 으로 채워 holdout_labeled.csv 로 저장
  2) export ANTHROPIC_API_KEY=sk-ant-...
  3) python3 04_compare.py                 # 세 방식 전부
     python3 04_compare.py --only rule     # LLM 없이 규칙만 (키 불필요)

출력: 항목 분류 F1 / 감성 F1 / 호출 수 / 소요 시간 / 추정 비용
"""
import argparse, json, re, sys, time, pathlib, csv
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lexicon

ASPECTS = ["맛", "양", "가격", "서비스", "배달"]
ROOT = pathlib.Path(__file__).parent.parent
MODEL = "claude-opus-5"          # 비용 비교하려면 claude-haiku-4-5 로 바꿔 한 번 더 실행
PRICE = {"claude-opus-5": (5.0, 25.0), "claude-haiku-4-5": (1.0, 5.0)}  # $/MTok (in, out)

PROMPT = """음식 배달 리뷰에서 언급된 항목과 감성을 판정해라.

항목: 맛, 양, 가격, 서비스, 배달
감성: positive, negative
- 언급이 없는 항목은 넣지 않는다.
- 한 리뷰에 여러 항목이 있으면 각각 판정한다.
- "맛있지만 배달이 늦다" → 맛 positive, 배달 negative
- "적지 않게 주셨다" 같은 이중부정은 positive
- 긍정·부정이 섞여 판단이 어려우면 그 항목을 생략한다

JSON 배열로만 답하라. 설명 금지.
[{"i":0,"items":[{"aspect":"맛","sentiment":"positive","evidence":"너무 맛있어요"}]}]

리뷰:
"""


# ---------- A. 규칙 기반 ----------
def run_rule(reviews):
    t0 = time.time()
    out = [lexicon.analyze(r) for r in reviews]
    return out, {"calls": 0, "sec": time.time() - t0, "cost": 0.0}


# ---------- B. LLM ----------
def run_llm(reviews, batch=20):
    import anthropic
    client = anthropic.Anthropic()
    t0, calls, tin, tout = time.time(), 0, 0, 0
    out = [{} for _ in reviews]

    for s in range(0, len(reviews), batch):
        chunk = reviews[s:s + batch]
        body = "\n".join(f"{i}. {t}" for i, t in enumerate(chunk))
        r = client.messages.create(
            model=MODEL, max_tokens=4000,
            output_config={"effort": "low"},       # 분류 작업이라 낮은 effort로 충분
            messages=[{"role": "user", "content": PROMPT + body}],
        )
        calls += 1
        tin += r.usage.input_tokens
        tout += r.usage.output_tokens
        txt = next(b.text for b in r.content if b.type == "text")
        try:
            parsed = json.loads(txt[txt.index("["):txt.rindex("]") + 1])
        except Exception as e:
            print(f"  파싱 실패 (배치 {s}): {e}")
            continue
        for row in parsed:
            i = s + row.get("i", 0)
            if i < len(out):
                out[i] = {it["aspect"]: (1 if it["sentiment"] == "positive" else -1)
                          for it in row.get("items", []) if it.get("aspect") in ASPECTS}
        print(f"  {min(s+batch, len(reviews))}/{len(reviews)}", end="\r")

    pin, pout = PRICE.get(MODEL, (0, 0))
    cost = tin / 1e6 * pin + tout / 1e6 * pout
    return out, {"calls": calls, "sec": time.time() - t0, "cost": cost,
                 "tokens": f"{tin:,} in / {tout:,} out"}


# ---------- C. 혼합 ----------
def is_hard(text):
    """규칙이 흔들리는 문장만 LLM으로 보냅니다."""
    cls = lexicon.clauses(text)
    if not cls:
        return True
    for c in cls:
        hasP = bool(re.search(lexicon.POS, c))
        hasN = bool(re.search(lexicon.NEG, c))
        if hasP and hasN:                       # 한 절에 긍·부정 공존
            return True
    if lexicon.HYPO.search(text):               # 가정·우려 표현
        return True
    if lexicon.DOUBLE.search(text):             # 이중부정
        return True
    if not lexicon.analyze(text):               # 규칙이 아무것도 못 잡음
        return True
    return False


def run_hybrid(reviews):
    hard = [i for i, t in enumerate(reviews) if is_hard(t)]
    easy = [i for i in range(len(reviews)) if i not in set(hard)]
    print(f"  규칙 처리 {len(easy)}건 · LLM 처리 {len(hard)}건 ({100*len(hard)/len(reviews):.0f}%)")

    out = [{} for _ in reviews]
    for i in easy:
        out[i] = lexicon.analyze(reviews[i])
    meta = {"calls": 0, "sec": 0.0, "cost": 0.0}
    if hard:
        got, meta = run_llm([reviews[i] for i in hard])
        for k, i in enumerate(hard):
            out[i] = got[k]
    meta["routed"] = f"규칙 {len(easy)} / LLM {len(hard)}"
    return out, meta


# ---------- 평가 ----------
def score(pred, gold):
    """항목 탐지 F1과 감성까지 맞춘 F1을 따로 계산합니다."""
    aT = aP = aG = sT = 0
    for p, g in zip(pred, gold):
        for a in ASPECTS:
            if a in p: aP += 1
            if a in g: aG += 1
            if a in p and a in g:
                aT += 1
                if p[a] == g[a]:
                    sT += 1
    f1 = lambda t, p, g: 0 if not (p and g) else 2*(t/p)*(t/g)/((t/p)+(t/g)) if (t/p)+(t/g) else 0
    return {"항목F1": f1(aT, aP, aG), "감성F1": f1(sT, aP, aG),
            "정답수": aG, "예측수": aP, "항목일치": aT, "감성일치": sT}


def load(path):
    reviews, gold = [], []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            reviews.append(row["리뷰"])
            gold.append({a: (1 if row.get(a, "").strip() == "긍정" else -1)
                         for a in ASPECTS if row.get(a, "").strip() in ("긍정", "부정")})
    return reviews, gold


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "labeling" / "holdout_labeled.csv"))
    ap.add_argument("--only", choices=["rule", "llm", "hybrid"])
    args = ap.parse_args()

    if not pathlib.Path(args.data).exists():
        sys.exit(f"사람 라벨 파일이 없습니다: {args.data}\n"
                 f"holdout_150.csv 를 채워서 holdout_labeled.csv 로 저장하세요.")

    reviews, gold = load(args.data)
    print(f"사람 정답셋 {len(reviews)}건 · 항목 라벨 {sum(len(g) for g in gold)}개\n")

    runs = {"규칙": run_rule, "LLM": run_llm, "혼합": run_hybrid}
    if args.only:
        runs = {k: v for k, v in runs.items()
                if k == {"rule": "규칙", "llm": "LLM", "hybrid": "혼합"}[args.only]}

    rows = []
    for name, fn in runs.items():
        print(f"[{name}]")
        pred, meta = fn(reviews)
        s = score(pred, gold)
        rows.append((name, s, meta))
        print(f"  항목F1 {s['항목F1']:.3f} · 감성F1 {s['감성F1']:.3f} · "
              f"호출 {meta['calls']} · {meta['sec']:.1f}초 · ${meta['cost']:.3f}\n")

    print(f"{'방식':<6}{'항목F1':>9}{'감성F1':>9}{'호출':>7}{'초':>8}{'비용($)':>10}")
    print("-" * 50)
    for name, s, m in rows:
        print(f"{name:<6}{s['항목F1']:>9.3f}{s['감성F1']:>9.3f}{m['calls']:>7}{m['sec']:>8.1f}{m['cost']:>10.3f}")
    json.dump([{"방식": n, **s, **{k: v for k, v in m.items() if k != 'tokens'}} for n, s, m in rows],
              open(ROOT / "data" / "compare_result.json", "w"), ensure_ascii=False, indent=1)
    print(f"\n저장: data/compare_result.json")

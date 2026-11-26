"""Claude가 붙인 정답 라벨 200건 + 규칙 기반 정확도 측정.

⚠️ 주의: 이 라벨은 사람이 아니라 LLM(Claude)이 붙였습니다.
발표에서는 "LLM 라벨 기준"이라고 명시해야 합니다.
사람 교차검증은 labeling_sheet.csv의 정답_ 열을 채워서 하세요.
"""
import pandas as pd, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import lexicon

# index: "항목극성" 쉼표 구분. P=긍정, N=부정. 언급 없으면 생략.
GOLD = {
0:"맛P",1:"맛P",2:"맛P",3:"맛P,양P",4:"맛P,양P",5:"맛P",6:"맛P,양N",7:"맛P",8:"맛P",9:"맛P",
10:"맛P",11:"맛P",12:"맛P",13:"맛P",14:"맛P",15:"맛P,양P",16:"맛P,양P",17:"맛P",18:"맛P,양P",19:"맛P",
20:"맛P",21:"맛P",22:"맛P,양P",23:"맛P,양P",24:"맛P",25:"서비스P",26:"맛P,배달P",27:"맛P",28:"맛P,양N",29:"맛P",
30:"맛P",31:"맛P,양P,서비스P",32:"맛P",33:"맛N",34:"맛P,양P,서비스P",35:"맛P,가격P",36:"맛P",37:"맛N",38:"맛N,서비스N",39:"맛P,배달P,서비스P",
40:"맛P,양P",41:"맛P",42:"맛P",43:"맛P,양P",44:"맛P",45:"맛P,서비스P",46:"맛P",47:"맛P,양P,가격P",48:"양P",49:"맛P,배달P",
50:"맛P",51:"맛P",52:"맛P",53:"맛P",54:"맛P",55:"맛P",56:"맛N",57:"맛P",58:"맛P",59:"맛P",
60:"맛P,양P,가격P",61:"맛P,양P",62:"맛P",63:"맛P",64:"맛P",65:"맛P",66:"맛P,양P",67:"맛P,양P",68:"맛P",69:"맛P",
70:"맛P",71:"맛P",72:"맛P,배달P",73:"맛P",74:"맛P",75:"맛P",76:"맛P",77:"맛P",78:"맛P,양P",79:"맛P",
80:"맛P",81:"서비스N",82:"맛P",83:"맛P",84:"맛P,양P",85:"맛P",86:"양P",87:"맛P,양P,배달P",88:"맛P,양P",89:"양P",
90:"맛P",91:"맛P,서비스P",92:"맛P,양P",93:"맛P,양P",94:"맛P,양P",95:"맛P,양N",96:"맛P",97:"맛P",98:"맛P",99:"맛P",
100:"맛P,양P",101:"맛P,배달P",102:"맛P",103:"양N,가격P",104:"맛P",105:"맛P,양P",106:"맛P",107:"맛P,양P,배달P",108:"맛P,서비스N",109:"서비스N",
110:"맛P",111:"맛P",112:"맛P",113:"맛P",114:"맛P",115:"맛P",116:"맛P",117:"맛P",118:"맛P",119:"양P,가격P",
120:"맛P",121:"맛P",122:"맛P",123:"맛P",124:"맛P",125:"맛P",126:"맛P",127:"맛P,배달N",128:"맛P,서비스N",129:"맛P,양N",
130:"맛P",131:"맛P,양P",132:"맛P",133:"배달P",134:"맛P",135:"맛P",136:"맛P",137:"맛P,배달P",138:"맛N",139:"맛P",
140:"맛P,양P",141:"양P",142:"맛P,서비스N",143:"맛P",144:"맛P,양P",145:"맛N",146:"맛N,가격N",147:"맛P",148:"",149:"맛P",
150:"맛P,배달N",151:"맛P",152:"맛P",153:"맛P",154:"맛P",155:"맛P,양P",156:"맛P",157:"맛N",158:"맛P",159:"맛P,양P",
160:"맛P",161:"맛P",162:"맛P,양P,서비스P",163:"맛P",164:"맛P",165:"",166:"맛P",167:"맛P",168:"맛P,배달P",169:"맛P",
170:"맛N",171:"맛P",172:"맛N",173:"맛P",174:"맛P,양P",175:"맛P,양P",176:"맛P",177:"맛P,양P",178:"맛P,양P",179:"맛P,배달P,서비스P",
180:"맛P",181:"맛P",182:"맛P,배달P",183:"맛P",184:"맛P,양P,서비스P",185:"맛P,배달P",186:"맛P,양N",187:"맛P,양P",188:"맛P",189:"맛P,양P",
190:"서비스N",191:"양P",192:"맛P,양P",193:"맛P,양P",194:"맛P,서비스N",195:"맛P",196:"맛P",197:"맛P,양P",198:"배달P",199:"맛P,양P",
}

def parse(s):
    out = {}
    for tok in filter(None, str(s).split(",")):
        out[tok[:-1]] = 1 if tok[-1] == "P" else -1
    return out

ASP = list(lexicon.ASPECTS)
df = pd.read_csv(pathlib.Path(__file__).parent / "labeling_sheet.csv")

rows, conf = [], {a: {"tp":0,"fp":0,"fn":0,"pol_err":0} for a in ASP}
for i, r in df.iterrows():
    gold, pred = parse(GOLD.get(i, "")), lexicon.analyze(r["리뷰"])
    for a in ASP:
        g, p = gold.get(a), pred.get(a)
        if g and p:
            if g == p: conf[a]["tp"] += 1
            else:      conf[a]["pol_err"] += 1      # 항목은 맞췄는데 극성 틀림
        elif g and not p: conf[a]["fn"] += 1        # 놓침
        elif p and not g: conf[a]["fp"] += 1        # 없는 걸 잡음
    rows.append({"리뷰": r["리뷰"],
                 **{f"정답_{a}": {1:"긍정",-1:"부정"}.get(gold.get(a), "") for a in ASP},
                 **{f"규칙_{a}": {1:"긍정",-1:"부정"}.get(pred.get(a), "") for a in ASP}})

pd.DataFrame(rows).to_csv(pathlib.Path(__file__).parent / "labeled_by_claude.csv",
                          index=False, encoding="utf-8-sig")

print(f"{'항목':<6}{'정답':>5}{'정밀도':>8}{'재현율':>8}{'F1':>8}{'극성오류':>8}")
print("-" * 45)
tp=fp=fn=pe=0
for a in ASP:
    c = conf[a]
    gold_n = c["tp"] + c["pol_err"] + c["fn"]
    prec = c["tp"] / (c["tp"] + c["pol_err"] + c["fp"]) if (c["tp"]+c["pol_err"]+c["fp"]) else 0
    rec  = c["tp"] / gold_n if gold_n else 0
    f1   = 2*prec*rec/(prec+rec) if prec+rec else 0
    tp += c["tp"]; fp += c["fp"]; fn += c["fn"]; pe += c["pol_err"]
    print(f"{a:<6}{gold_n:>5}{prec:>8.2f}{rec:>8.2f}{f1:>8.2f}{c['pol_err']:>8}")

P = tp/(tp+pe+fp) if tp+pe+fp else 0
R = tp/(tp+pe+fn) if tp+pe+fn else 0
print("-" * 45)
print(f"{'전체':<6}{tp+pe+fn:>5}{P:>8.2f}{R:>8.2f}{2*P*R/(P+R) if P+R else 0:>8.2f}{pe:>8}")
print(f"\n정답 라벨 총 {tp+pe+fn}개 · 정확히 맞춤 {tp} · 극성오류 {pe} · 놓침 {fn} · 오탐 {fp}")

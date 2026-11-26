# -*- coding: utf-8 -*-
"""4조 캡스톤 중간발표(2026-10-28) PPTX 생성 — 르슐랭 가이드 방향.

build.py(르몽 강남구 방향)와 같은 폴더의 형제 스크립트입니다. 그쪽을 덮어쓰지 않습니다.
색은 르몽 가이드의 다크 네이비를 복제하지 않고, 프로토타입 UI와 같은 밝은 톤을 씁니다
(화면 캡처가 밝은 UI라 다크 배경에서 겉돕니다).

숫자는 전부 저장소 실측값입니다.
  data/seed_real.json meta — 식당 285 · 영상 296 · 댓글 42,526 · 방문명시 2,929
                             집계 1,355 · 점수 158 · 배지 23
화면은 .report-assets/shots/ 의 실제 프로토타입 스크린샷입니다.
"""
import pathlib
import sys
from pptx import Presentation
from pptx.util import Inches as In, Pt, Emu
from pptx.dml.color import RGBColor as C
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image as PILImage

HERE = pathlib.Path(__file__).parent
SHOTS = HERE / "assets"                       # 프로토타입 실제 캡처
OUT = HERE / "4조_중간발표_르슐랭가이드.pptx"

F = "Apple SD Gothic Neo"
BG     = C(0xF7, 0xF6, 0xF2)
INK    = C(0x1C, 0x1F, 0x1D)
MUTED  = C(0x72, 0x76, 0x70)
FAINT  = C(0x9A, 0x9D, 0x97)
LINE   = C(0xDE, 0xDB, 0xD3)
GREEN  = C(0x2E, 0x6B, 0x4E)
GREENL = C(0xE6, 0xEE, 0xE8)
TEAL   = C(0x16, 0x85, 0x7A)
AMBER  = C(0xB5, 0x72, 0x0E)
AMBERL = C(0xF6, 0xEE, 0xDE)
GRAYL  = C(0xEC, 0xEB, 0xE6)

W, H = In(13.333), In(7.5)
M = In(0.78)                      # 좌우 여백
prs = Presentation()
prs.slide_width, prs.slide_height = W, H


# ─────────────────────────────────────────────── 기본 도구

def set_font(run, name=None):
    """python-pptx는 latin만 설정합니다. 한글은 ea(동아시아) 글꼴을 따로 지정해야
    PowerPoint에서 대체 글꼴로 밀리지 않습니다. build.py 와 같은 방식입니다."""
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {}); rPr.append(el)
        el.set("typeface", name or F)


def slide(notes=""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid(); bg.fill.fore_color.rgb = BG; bg.line.fill.background()
    bg.shadow.inherit = False
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def txt(s, x, y, w, h, runs, size=13, color=INK, bold=False, align=PP_ALIGN.LEFT,
        line=1.35, space_after=6, anchor=MSO_ANCHOR.TOP):
    """runs: 문자열이거나 [(텍스트, {옵션})] 목록. 문단은 리스트의 리스트."""
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) and runs and isinstance(runs[0], list) else [runs]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.line_spacing = line
        para.space_after = Pt(space_after)
        items = p if isinstance(p, list) else [(p, {})]
        for t, o in items:
            r = para.add_run(); r.text = t
            f = r.font
            f.name = F
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.color.rgb = o.get("color", color)
            set_font(r)
    return tb


def rule(s, x, y, w, color=LINE, h=Emu(9525)):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    r.fill.solid(); r.fill.fore_color.rgb = color
    r.line.fill.background(); r.shadow.inherit = False
    return r


def head(s, kicker, title, claim=None):
    """페이지 머리 — 작은 라벨 / 제목 / 이 장의 주장 한 줄."""
    txt(s, M, In(0.52), W - 2 * M, In(0.26),
        [(kicker, {"size": 10.5, "bold": True, "color": GREEN})])
    txt(s, M, In(0.82), W - 2 * M, In(0.5),
        [(title, {"size": 27, "bold": True, "color": INK})])
    y = In(1.42)
    if claim:
        txt(s, M, y, W - 2 * M, In(0.34), [(claim, {"size": 14.5, "color": MUTED})])
        y = In(1.86)
    rule(s, M, y, W - 2 * M)
    return y + In(0.30)


def page(s, n):
    txt(s, W - M - In(1.2), H - In(0.56), In(1.2), In(0.24),
        [(f"{n} / 10", {"size": 9, "color": FAINT})], align=PP_ALIGN.RIGHT)


def box(s, x, y, w, h, fill=None, border=LINE, radius=0.06):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                             x, y, w, h)
    if radius:
        shp.adjustments[0] = radius
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if border is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = border; shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def chip(s, x, y, label, fg, bg, w=None, size=9.5):
    w = w or In(0.1 + 0.105 * len(label))
    h = In(0.26)
    box(s, x, y, w, h, fill=bg, border=None, radius=0.5)
    txt(s, x, y + In(0.045), w, In(0.2), [(label, {"size": size, "bold": True, "color": fg})],
        align=PP_ALIGN.CENTER)
    return x + w


def shot(s, name, x, y, max_w, max_h, caption=None):
    """비율을 지키면서 상자 안에 꽉 채워 넣습니다."""
    p = SHOTS / name
    iw, ih = PILImage.open(p).size
    sc = min(max_w / iw, max_h / ih)
    w, h = int(iw * sc), int(ih * sc)
    cx = x + int((max_w - w) / 2)
    s.shapes.add_picture(str(p), cx, y, w, h)
    fr = box(s, cx, y, w, h, fill=None, border=LINE, radius=0)
    fr.line.width = Pt(0.75)
    if caption:
        txt(s, x, y + h + In(0.11), max_w, In(0.5),
            [(caption, {"size": 9.5, "color": FAINT})], align=PP_ALIGN.CENTER, line=1.3)
    return y + h


def arrow(s, x, y, w=In(0.26)):
    a = s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, x, y, w, In(0.2))
    a.rotation = 90
    a.fill.solid(); a.fill.fore_color.rgb = C(0xC2, 0xC6, 0xC0)
    a.line.fill.background(); a.shadow.inherit = False


# ─────────────────────────────────────────────── 1. 표지

s = slide(
 "[0:00–0:30 · 30초]\n"
 "안녕하십니까, 4조입니다. 저희가 만드는 것은 '르슐랭 가이드'입니다.\n"
 "한 문장으로 말씀드리면 — 낯선 동네에서, 내가 보던 맛집 유튜버가 다녀간 가까운 식당을 찾고, "
 "원본 영상과 실제로 다녀온 사람들의 말을 보고 갈 곳을 고르는 서비스입니다.\n"
 "발표는 제가 하고, 질의응답은 팀원 전원이 맡습니다.\n"
 "※ 발표 전 확인: 팀원 이름 채우기, 직함은 쓰지 않고 '산출물 담당'으로만 표기.")
rule(s, M, In(2.05), In(1.1), GREEN, Emu(38100))
txt(s, M, In(2.3), In(9.6), In(0.4),
    [("캡스톤디자인 중간발표 · 2026.10.28 · 4조", {"size": 12.5, "color": MUTED})])
txt(s, M, In(2.78), In(10.5), In(1.1),
    [("르슐랭 가이드", {"size": 48, "bold": True, "color": INK}),
     ("  (가칭)", {"size": 17, "color": FAINT})])
txt(s, M, In(3.95), In(9.3), In(1.3),
    [[("낯선 동네에서 내가 보던 맛집 유튜버가 다녀간 가까운 식당을 찾고,",
       {"size": 19, "color": INK})],
     [("원본 영상과 다녀온 사람들의 반응을 보고 갈 곳을 고르는 웹 서비스",
       {"size": 19, "color": INK})]],
    line=1.45)
rule(s, M, In(5.5), In(11.0))
txt(s, M, In(5.72), In(5.6), In(0.9),
    [[("발표  ", {"size": 11, "color": FAINT}), ("[팀장 이름]", {"size": 12.5, "color": INK})],
     [("질의응답  ", {"size": 11, "color": FAINT}),
      ("팀원 전원  [이름] · [이름] · [이름]", {"size": 12.5, "color": INK})]],
    space_after=5)
txt(s, M + In(6.4), In(5.72), In(4.6), In(0.9),
    [("직함을 나누지 않았습니다. 산출물 단위로 설명 담당을 정했습니다.",
      {"size": 10.5, "color": FAINT})], line=1.4)
page(s, 1)

# ─────────────────────────────────────────────── 2. 사용 장면

s = slide(
 "[0:30–1:10 · 40초]\n"
 "먼저 이 서비스를 쓰게 되는 순간입니다.\n"
 "출장으로 왔든 여행으로 왔든, 처음 온 동네에서 끼니를 앞두고 휴대폰을 꺼냅니다. "
 "이때 떠올리는 건 '여기 맛집'이 아니라 '내가 보던 그 채널, 이 근처도 갔었나?'입니다.\n"
 "영상을 본 기억은 있는데, 그게 어느 동네였는지가 기억 속에만 있습니다.\n"
 "오른쪽은 지금 저희 프로토타입의 모바일 화면입니다. 실제로 수집한 285곳이 올라가 있습니다.\n"
 "※ 여행 전용 서비스가 아니라는 점을 여기서 한 번 못 박을 것.")
y = head(s, "01  사용 장면", "낯선 동네에서 묻는 질문은 하나다",
         "여행이든 출장이든, 약속이든 — 지역이 낯설다는 조건만 같으면 같은 질문을 한다")
txt(s, M, y + In(0.08), In(6.3), In(1.4),
    [[("“이 근처에,”", {"size": 23, "bold": True, "color": INK})],
     [("“내가 보던 유튜버가 간 집 있나?”", {"size": 23, "bold": True, "color": INK})]],
    line=1.3, space_after=2)
txt(s, M, y + In(1.52), In(6.0), In(2.3),
    [[("영상을 본 기억은 남아 있습니다. 어느 동네였는지가 기억 속에만 있습니다.",
       {"size": 13.5, "color": INK})],
     [("채널을 거슬러 올라가 제목을 뒤지다 포기하고, 결국 그 자리에서 "
       "평점 높은 집을 아무거나 고릅니다.", {"size": 13.5, "color": MUTED})]],
    line=1.6, space_after=10)
bx = box(s, M, y + In(2.75), In(6.0), In(0.78), fill=GREENL, border=None, radius=0.1)
txt(s, M + In(0.28), y + In(2.95), In(5.5), In(0.5),
    [("출장·여행·약속 — 상황은 달라도 묻는 것은 같습니다. 이 서비스는 "
      "여행객 전용이 아닙니다.", {"size": 12, "color": GREEN})], line=1.4)
shot(s, "r9-mobile.png", M + In(6.6), y - In(0.05), In(5.1), In(4.5),
     "르슐랭 가이드 프로토타입 · 모바일 화면 (실제 수집 데이터 285곳)")
page(s, 2)

# ─────────────────────────────────────────────── 3. 페르소나

s = slide(
 "[1:10–2:00 · 50초]\n"
 "대표 사용자는 이렇게 설정했습니다. 가상 인물이고, 설계를 위한 설정입니다. "
 "인터뷰 결과가 아니라는 점을 분명히 말씀드립니다.\n"
 "29세 직장인, 월 두세 번 처음 가는 지역으로 출장을 갑니다. 평소 정육왕·또간집 같은 영상을 "
 "즐겨 보고, 낯선 동네에서 혼자 한 끼를 해결합니다.\n"
 "이 사람이 원하는 건 '그 지역의 맛집 순위'가 아니라 '내가 믿고 보던 사람이 이미 검증한 집'입니다.\n"
 "오른쪽 빈칸은 아직 조사하지 않은 항목입니다. 최종발표까지 실제 사용자 점검으로 채우겠습니다.\n"
 "※ 인터뷰 인원·비율을 묻는 질문이 오면: 아직 하지 않았고 11월 3주차에 5명 과업 테스트 예정이라고 답할 것.")
y = head(s, "02  대표 페르소나", "내가 믿고 보던 사람이 이미 검증한 집",
         "지역의 1등이 아니라, 내가 아는 사람이 다녀간 집을 찾는 사용자")
card = box(s, M, y, In(6.5), In(3.85), fill=C(0xFF, 0xFF, 0xFF), radius=0.045)
chip(s, M + In(0.34), y + In(0.3), "가상 페르소나 · 설계용 설정", AMBER, AMBERL, w=In(2.3))
txt(s, M + In(0.34), y + In(0.72), In(5.8), In(0.42),
    [[("김현우", {"size": 23, "bold": True, "color": INK}),
      ("  (가명)", {"size": 13, "color": FAINT})]])
txt(s, M + In(0.34), y + In(1.08), In(5.8), In(0.26),
    [("29세 · 지역 출장이 잦은 직장인", {"size": 12.5, "color": MUTED})])
rule(s, M + In(0.34), y + In(1.38), In(5.8))
rows = [("상황", "월 2~3회 처음 가는 지역에서 혼자 점심·저녁을 해결한다"),
        ("평소", "맛집 영상을 즐겨 보고, 가고 싶은 집을 머릿속에만 담아 둔다"),
        ("현재", "현장에서 채널을 뒤지다 포기하고 지도 앱 평점으로 고른다"),
        ("원하는 것", "처음 온 동네에서 실패하지 않는 한 끼")]
ry = y + In(1.6)
for k, v in rows:
    txt(s, M + In(0.34), ry, In(1.1), In(0.3), [(k, {"size": 11, "color": FAINT})])
    txt(s, M + In(1.5), ry, In(4.7), In(0.5), [(v, {"size": 13, "color": INK})], line=1.35)
    ry += In(0.54)
box(s, M + In(7.0), y, In(4.7), In(3.85), fill=None, border=LINE, radius=0.045)
txt(s, M + In(7.34), y + In(0.32), In(4.0), In(0.3),
    [("아직 조사하지 않은 것", {"size": 12, "bold": True, "color": INK})])
txt(s, M + In(7.34), y + In(0.78), In(4.0), In(2.4),
    [[("인터뷰 인원", {"size": 11.5, "color": MUTED}), ("   [실제 조사 후 입력]", {"size": 11.5, "color": FAINT})],
     [("응답 비율", {"size": 11.5, "color": MUTED}), ("   [실제 조사 후 입력]", {"size": 11.5, "color": FAINT})],
     [("사용자 발언", {"size": 11.5, "color": MUTED}), ("   [실제 조사 후 입력]", {"size": 11.5, "color": FAINT})]],
    line=1.5, space_after=10)
rule(s, M + In(7.34), y + In(2.55), In(4.0))
txt(s, M + In(7.34), y + In(2.75), In(4.0), In(0.9),
    [("이 페르소나는 팀이 세운 가설입니다. 11월 3주차 사용자 점검(5명)으로 "
      "검증하고, 어긋나면 고치겠습니다.", {"size": 11, "color": MUTED})], line=1.45)
page(s, 3)

# ─────────────────────────────────────────────── 4. Pain-point

s = slide(
 "[2:00–3:00 · 60초]\n"
 "문제는 정확히 두 가지입니다.\n"
 "첫째, 영상은 채널 시간순으로 쌓입니다. 내 위치 기준으로는 절대 모이지 않습니다. "
 "'강릉'을 검색해도 내가 보던 채널이 강릉에서 뭘 먹었는지는 나오지 않습니다.\n"
 "둘째, 영상은 촬영 당시의 인상입니다. 2년 전 영상일 수도 있고, 그 사이 사장이 바뀌었을 수도 있습니다. "
 "지금 가도 되는지는 영상이 알려주지 않습니다.\n"
 "그래서 지금은 아래처럼 다섯 단계를 식당 한 곳마다 반복합니다.\n"
 "대안에 대해: 영상 속 장소를 지도에 모아 보여주는 서비스는 이미 있습니다. 저희가 다르다고 보는 지점은 "
 "'영상 이후의 반응'이 같은 화면에서 이어지지 않는다는 점이고, 이건 저희가 확인한 범위에서의 판단입니다.\n"
 "※ 특정 서비스 이름을 먼저 꺼내지 말 것. 질문이 오면 비교 메모대로 답할 것.")
y = head(s, "03  Pain-point", "찾는 것도 번거롭고, 찾아도 판단이 안 된다")
for i, (num, t, d) in enumerate([
    ("문제 1", "내 위치 기준으로 모이지 않는다",
     "영상은 채널 시간순으로 쌓입니다. '지금 이 지역'을 기준으로 "
     "내가 보던 채널이 다녀간 집을 모아 보는 축이 없습니다."),
    ("문제 2", "영상만으로는 지금 가도 되는지 모른다",
     "영상은 촬영 시점의 인상입니다. 공개 이후 실제로 다녀온 사람들이 "
     "뭐라고 했는지는 영상 옆에 없습니다.")]):
    x = M + i * In(6.05)
    b = box(s, x, y, In(5.6), In(2.05), fill=C(0xFF, 0xFF, 0xFF), radius=0.05)
    txt(s, x + In(0.32), y + In(0.26), In(1.2), In(0.26),
        [(num, {"size": 10.5, "bold": True, "color": GREEN})])
    txt(s, x + In(0.32), y + In(0.6), In(5.0), In(0.4),
        [(t, {"size": 17, "bold": True, "color": INK})])
    txt(s, x + In(0.32), y + In(1.12), In(5.0), In(0.8),
        [(d, {"size": 12.5, "color": MUTED})], line=1.5)
ty = y + In(2.7)
txt(s, M, ty, In(5.0), In(0.3),
    [("지금 사용자가 식당 한 곳마다 반복하는 과정", {"size": 12, "bold": True, "color": INK})])
steps = ["영상 기억", "채널 뒤지기", "상호 추정", "지도 앱 검색", "리뷰 따로 검색"]
sx = M
for i, st in enumerate(steps):
    b = box(s, sx, ty + In(0.46), In(1.9), In(0.56), fill=GRAYL, border=None, radius=0.12)
    txt(s, sx, ty + In(0.62), In(1.9), In(0.3), [(st, {"size": 12, "color": INK})],
        align=PP_ALIGN.CENTER)
    sx += In(1.9)
    if i < len(steps) - 1:
        txt(s, sx, ty + In(0.62), In(0.34), In(0.3),
            [("→", {"size": 13, "color": FAINT})], align=PP_ALIGN.CENTER)
        sx += In(0.34)
box(s, M, ty + In(1.28), In(11.77), In(0.72), fill=AMBERL, border=None, radius=0.1)
txt(s, M + In(0.3), ty + In(1.46), In(11.2), In(0.4),
    [[("대안의 한계  ", {"size": 11, "bold": True, "color": AMBER}),
      ("영상 속 장소를 지도에서 찾는 대안은 있습니다. 다만 방문을 판단할 "
       "'영상 이후의 반응'은 그 화면에서 이어지지 않아 따로 확인해야 합니다 "
       "— 저희가 확인한 범위에서의 판단입니다.", {"size": 11.5, "color": INK})]], line=1.4)
page(s, 4)

# ─────────────────────────────────────────────── 5. 서비스 정의와 기능

s = slide(
 "[3:00–4:10 · 70초]\n"
 "그래서 저희 서비스는 이 한 문장입니다 — 유튜버가 다녀간 식당을 내가 있는 지역에서 찾고, "
 "원본 영상과 다녀온 사람들의 말까지 한 화면에서 보는 서비스.\n"
 "앞의 두 문제에 기능을 하나씩 붙였습니다.\n"
 "문제 1에는 지역과 유튜버로 좁히는 지도·목록, 그리고 원본 영상 바로 열기입니다.\n"
 "문제 2에는 그 영상 댓글 중 '다녀왔다'고 밝힌 것만 골라 항목별로 묶고, "
 "쓴소리가 있는 순으로도 볼 수 있게 했습니다. 오른쪽이 그 화면입니다. "
 "실제 댓글 원문이 그대로 보입니다.\n"
 "르슐랭 배지는 제목이 아니라 보조 표시입니다. 285곳 중 23곳, 8%에만 붙어 있습니다.\n"
 "※ '방문 인증'이라는 말을 쓰지 말 것. 텍스트 분류다.")
y = head(s, "04  서비스 정의", "영상에서 끝나지 않고, 가는 데까지 잇는다")
txt(s, M, y, In(7.1), In(1.1),
    [("유튜버가 다녀간 식당을 내가 있는 지역에서 찾고,\n"
      "원본 영상과 다녀온 사람들의 말까지 한 화면에서 보는 서비스",
      {"size": 19, "bold": True, "color": INK})], line=1.45)
fy = y + In(1.3)
for i, (p, feat, det) in enumerate([
    ("문제 1 →", "지역 · 유튜버로 좁히는 지도와 목록",
     "현재 위치 또는 지역을 고르고 채널로 거른다. 식당 카드에서 원본 영상을 바로 연다."),
    ("문제 2 →", "다녀온 사람의 말만 모은 방문자 반응",
     "그 영상 댓글 중 방문 경험을 밝힌 것만 골라 맛·양·가격·서비스·대기·분위기로 묶고, "
     "원문을 그대로 보여준다.")]):
    b = box(s, M, fy + i * In(1.4), In(7.1), In(1.3), fill=C(0xFF, 0xFF, 0xFF), radius=0.06)
    txt(s, M + In(0.3), fy + i * In(1.4) + In(0.2), In(1.1), In(0.26),
        [(p, {"size": 10.5, "bold": True, "color": GREEN})])
    txt(s, M + In(1.35), fy + i * In(1.4) + In(0.17), In(5.5), In(0.3),
        [(feat, {"size": 14.5, "bold": True, "color": INK})])
    txt(s, M + In(1.35), fy + i * In(1.4) + In(0.52), In(5.5), In(0.72),
        [(det, {"size": 11.5, "color": MUTED})], line=1.4)
box(s, M, fy + In(2.95), In(7.1), In(0.66), fill=GREENL, border=None, radius=0.11)
txt(s, M + In(0.3), fy + In(3.11), In(6.6), In(0.4),
    [[("르슐랭 배지  ", {"size": 11, "bold": True, "color": GREEN}),
      ("근거가 충분한 극소수에만 붙는 보조 표시 — 285곳 중 23곳(8%)",
       {"size": 11.5, "color": INK})]], line=1.35)
shot(s, "r4-detail.png", M + In(7.5), y, In(4.27), In(4.3),
     "식당 상세 패널 — 실제 유튜브 댓글 원문")
page(s, 5)

# ─────────────────────────────────────────────── 6. IA / 사용자 흐름

s = slide(
 "[4:10–4:50 · 40초]\n"
 "구조는 단순합니다. 지역 또는 현재 위치와 유튜버를 고르면, 지도와 목록이 같은 조건을 공유합니다. "
 "식당을 고르면 카드가 열리고, 그 안에 원본 영상과 방문자 반응이 있고, 마지막이 길찾기입니다.\n"
 "화면 전환 없이 왼쪽 목록과 오른쪽 지도가 한 화면에서 같이 움직입니다.\n"
 "두 가지를 모든 화면에 붙여 두었습니다. 하나는 '근거 있는 곳만' 토글이고, "
 "다른 하나는 '분석 방법과 한계'입니다. 데이터가 모자란 곳은 빈칸으로 두고 추정하지 않습니다.\n"
 "르슐랭 배지는 이 흐름의 입구가 아니라, 카드 위에 붙는 작은 표시입니다.")
y = head(s, "05  정보 구조", "한 화면에서 끝나는 다섯 걸음")
nodes = [("지역 · 현재 위치\n+ 유튜버 선택", "검색 · 채널 · 지역 칩"),
         ("식당 지도 / 목록", "같은 조건을 공유"),
         ("식당 카드", "상호 · 주소 · 업종"),
         ("원본 영상 ·\n방문자 반응", "영상 링크 · 항목 · 원문"),
         ("길찾기", "지도 앱으로 연결")]
bw, gap = In(2.08), In(0.34)
x = M
for i, (t, d) in enumerate(nodes):
    last = i == len(nodes) - 1
    b = box(s, x, y + In(0.35), bw, In(1.15),
            fill=GREENL if last else C(0xFF, 0xFF, 0xFF),
            border=None if last else LINE, radius=0.08)
    txt(s, x + In(0.12), y + In(0.55), bw - In(0.24), In(0.6),
        [(t, {"size": 12.5, "bold": True, "color": GREEN if last else INK})],
        align=PP_ALIGN.CENTER, line=1.3)
    txt(s, x + In(0.12), y + In(1.6), bw - In(0.24), In(0.42),
        [(d, {"size": 10, "color": FAINT})], align=PP_ALIGN.CENTER, line=1.3)
    x += bw
    if i < len(nodes) - 1:
        txt(s, x, y + In(0.8), gap, In(0.3), [("→", {"size": 15, "color": C(0xB8, 0xBC, 0xB6)})],
            align=PP_ALIGN.CENTER)
        x += gap
ay = y + In(2.6)
rule(s, M, ay, In(11.77))
for i, (t, d) in enumerate([
    ("모든 화면에 붙어 있는 것", "① '근거 있는 곳만' 토글 — 285곳 → 158곳\n"
                     "② '분석 방법과 한계' — 숫자의 출처를 사용자가 직접 연다"),
    ("르슐랭 배지의 자리", "흐름의 입구가 아니라 식당 카드 위의 작은 표시입니다.\n"
                 "근거 상위 23곳에만 붙고, 나머지 262곳에는 없습니다."),
    ("빈칸을 채우지 않습니다", "댓글이 부족한 127곳은 '근거 부족'으로 비워 둡니다.\n"
                    "비율을 재분배하거나 추정값을 넣지 않습니다.")]):
    x = M + i * In(4.0)
    txt(s, x, ay + In(0.26), In(3.7), In(0.3), [(t, {"size": 12.5, "bold": True, "color": INK})])
    txt(s, x, ay + In(0.62), In(3.7), In(1.0), [(d, {"size": 11, "color": MUTED})], line=1.5)
page(s, 6)

# ─────────────────────────────────────────────── 7. 화면 1 — 탐색

s = slide(
 "[4:50–5:50 · 60초]\n"
 "지금부터 실제 화면입니다. 클릭되는 프로토타입이고, 지금 보시는 데이터는 전부 실제로 수집한 것입니다.\n"
 "왼쪽 위가 채널입니다 — 쯔양, 히밥, 정육왕. 밑의 숫자가 그 채널이 다녀간 식당 수입니다.\n"
 "지도의 원은 묶인 식당 수입니다. 줌을 당기면 풀리고, 시군구 경계와 이름이 나옵니다.\n"
 "이 지도는 지도 API가 아닙니다. 통계청 2013 행정경계를 직접 그렸습니다. "
 "상용 지도 키는 아직 발급받지 않아서, 그 전까지 동작하도록 만든 것입니다.\n"
 "왼쪽 아래 '근거 있는 곳만'을 켜면 285곳이 158곳으로 줄어듭니다. 근거가 모자란 곳을 숨기는 겁니다.\n"
 "※ 시연이 막히면 이 스크린샷으로 그대로 설명할 것. '시연 완료'라고 말하지 말 것.")
y = head(s, "06  화면 1 · 탐색", "누구의 · 어디의 식당인지 3초 안에")
shot(s, "r1-all.png", M, y - In(0.06), In(8.35), In(4.45))
px = M + In(8.65)
txt(s, px, y + In(0.05), In(3.1), In(0.3),
    [("이 화면에서 하는 선택", {"size": 12.5, "bold": True, "color": INK})])
items = [("채널 고르기", "쯔양 1 · 히밥 5 · 정육왕 279"),
         ("지역 고르기", "시군구 칩 · 검색 자동완성"),
         ("지도 ↔ 목록", "같은 조건을 공유"),
         ("근거 있는 곳만", "285곳 → 158곳")]
iy = y + In(0.40)
for k, v in items:
    txt(s, px, iy, In(3.1), In(0.26), [(k, {"size": 12, "bold": True, "color": GREEN})])
    txt(s, px, iy + In(0.26), In(3.1), In(0.3), [(v, {"size": 10.5, "color": MUTED})])
    iy += In(0.66)
rule(s, px, iy + In(0.05), In(3.1))
txt(s, px, iy + In(0.26), In(3.2), In(1.6),
    [[("실제 수집 데이터", {"size": 11.5, "bold": True, "color": INK})],
     [("식당 285곳 · 영상 296편 · 115개 시군구", {"size": 11, "color": MUTED})],
     [("지도는 통계청 2013 경계를 직접 렌더. 상용 지도 키는 미발급.",
       {"size": 10.5, "color": AMBER})]],
    line=1.45, space_after=7)
txt(s, M, H - In(0.62), In(8.35), In(0.3),
    [("클릭형 프로토타입 화면 · 2026.10.27 자동 검증 통과", {"size": 9.5, "color": FAINT})])
page(s, 7)

# ─────────────────────────────────────────────── 8. 화면 2 — 상세

s = slide(
 "[5:50–7:00 · 70초]\n"
 "식당을 고르면 이 카드가 열립니다. 순서가 곧 우선순위입니다.\n"
 "맨 위가 소개한 유튜버와 영상입니다. 제목과 공개일이 실제 값이고, 누르면 그 영상으로 갑니다.\n"
 "그 아래가 핵심입니다. 이 영상 댓글 400개 중 방문 경험을 밝힌 것이 65개, "
 "그중 항목이 잡힌 36개를 집계했습니다. 숫자를 숨기지 않고 셋 다 보여줍니다.\n"
 "항목별 막대가 나오고, 밑에 실제 댓글 원문이 그대로 붙습니다. 저희가 요약한 문장이 아닙니다.\n"
 "그리고 맨 아래 길찾기입니다. 여기서 실제 방문으로 이어집니다.\n"
 "한 가지 분명히 할 것은, 이 '다녀왔다'는 텍스트 분류 결과이지 방문 인증이 아닙니다. "
 "그래서 화면에도 '방문 명시'라고 적었습니다.\n"
 "※ 긍정률을 자랑하지 말 것. 맛 항목은 95%가 긍정이라 변별력이 없다. 중요한 건 반응의 양과 쓴소리 유무.")
y = head(s, "07  화면 2 · 식당 상세", "영상 다음의 한 걸음까지 한 화면에")
shot(s, "r3-detail.png", M, y - In(0.06), In(8.35), In(4.45))
px = M + In(8.65)
order = [("1", "소개한 유튜버 · 원본 영상", "제목 · 공개일 · 실제 링크"),
         ("2", "댓글 400 → 65 → 36", "전체 · 방문 명시 · 집계됨"),
         ("3", "항목별 방문자 반응", "맛 · 양 · 가격 · 서비스"),
         ("4", "실제 댓글 원문", "요약하지 않고 그대로"),
         ("5", "길찾기", "지도 앱으로 연결")]
iy = y + In(0.05)
for n, k, v in order:
    c = box(s, px, iy + In(0.02), In(0.26), In(0.26), fill=GREEN, border=None, radius=0.5)
    txt(s, px, iy + In(0.055), In(0.26), In(0.22),
        [(n, {"size": 9.5, "bold": True, "color": C(0xFF, 0xFF, 0xFF)})], align=PP_ALIGN.CENTER)
    txt(s, px + In(0.4), iy, In(2.8), In(0.26), [(k, {"size": 11.5, "bold": True, "color": INK})])
    txt(s, px + In(0.4), iy + In(0.26), In(2.8), In(0.26), [(v, {"size": 10, "color": FAINT})])
    iy += In(0.66)
box(s, px, iy + In(0.1), In(3.2), In(1.0), fill=AMBERL, border=None, radius=0.1)
txt(s, px + In(0.22), iy + In(0.26), In(2.8), In(0.8),
    [("댓글의 “다녀왔다”는 텍스트 분류 결과입니다. 방문 인증이 아닙니다.",
      {"size": 10.5, "color": AMBER})], line=1.45)
txt(s, M, H - In(0.62), In(8.35), In(0.3),
    [("클릭형 프로토타입 화면 · 인용문은 실제 유튜브 댓글 원문", {"size": 9.5, "color": FAINT})])
page(s, 8)

# ─────────────────────────────────────────────── 9. 데이터 · AI 설계와 현재 상태

s = slide(
 "[7:00–8:10 · 70초]\n"
 "데이터가 어디서 오는지입니다. 다섯 단계입니다.\n"
 "유튜버가 영상 설명란에 붙인 네이버·구글 지도 링크를 펼쳐 상호·주소·좌표를 얻습니다. "
 "같은 가게가 두 번 들어오면 70m 안에서 이름이 닮으면 합칩니다.\n"
 "그 영상 댓글을 YouTube Data API로 받아, 방문 경험을 밝힌 것만 고르고, 항목별로 분류합니다.\n"
 "숫자로 말씀드리면 댓글 42,526개 중 방문을 밝힌 게 2,929개, 실제 집계에 쓴 게 1,355개입니다. "
 "그래서 점수가 나온 건 158곳이고, 127곳은 근거 부족으로 비워 뒀습니다.\n"
 "르몽 데이터 얘기를 꼭 드려야 합니다. 당초 르몽 리뷰를 붙일 계획이었는데, 실제로 맞춰 보니 "
 "617곳 중 2곳, 0.3%만 겹쳤습니다. 르몽은 98.5%가 배달 리뷰고 유튜버가 가는 노포는 배달을 안 하니까 "
 "구조적으로 겹칠 수가 없었습니다. 그래서 식당 리뷰로는 쓰지 않기로 했고, "
 "대신 르몽 리뷰로 만든 항목별 감성 사전을 방문형으로 고쳐서 유튜브 댓글에 적용했습니다. "
 "식당을 이은 게 아니라 분석기만 옮긴 겁니다.\n"
 "※ 피벗 과정을 길게 설명하지 말 것. 숫자 하나로 끝내고 넘어갈 것.")
y = head(s, "08  데이터 · 분석", "숫자가 어디서 왔는지 사용자가 직접 열어 본다")
steps = [("영상 설명란\n지도 링크 펼치기", "실구현"),
         ("상호 · 주소 · 좌표\n확정 (70m 중복 병합)", "실구현"),
         ("영상 댓글 수집\nYouTube Data API v3", "실구현"),
         ("방문 명시 댓글만\n선별", "검증 예정"),
         ("항목별 감성\n6개 항목", "검증 예정")]
bw, gap = In(2.18), In(0.22)
x = M
for i, (t, st) in enumerate(steps):
    b = box(s, x, y, bw, In(1.18), fill=C(0xFF, 0xFF, 0xFF), radius=0.07)
    txt(s, x + In(0.1), y + In(0.2), bw - In(0.2), In(0.6),
        [(t, {"size": 11.5, "bold": True, "color": INK})], align=PP_ALIGN.CENTER, line=1.3)
    fg, bgc = (GREEN, GREENL) if st == "실구현" else (MUTED, GRAYL)
    cw = In(0.74)
    chip(s, x + (bw - cw) / 2, y + In(0.82), st, fg, bgc, w=cw, size=9)
    x += bw
    if i < len(steps) - 1:
        txt(s, x, y + In(0.45), gap, In(0.3), [("→", {"size": 13, "color": C(0xC0, 0xC4, 0xBE)})],
            align=PP_ALIGN.CENTER)
        x += gap
ny = y + In(1.45)
nums = [("42,526", "수집 댓글"), ("2,929", "방문 명시"), ("1,355", "집계에 사용"),
        ("158곳", "점수 산출"), ("127곳", "근거 부족 · 빈칸"), ("23곳", "배지 부여")]
nw = In(1.9)
for i, (v, k) in enumerate(nums):
    x = M + i * In(1.97)
    txt(s, x, ny, nw, In(0.4), [(v, {"size": 21, "bold": True, "color": GREEN})])
    txt(s, x, ny + In(0.42), nw, In(0.26), [(k, {"size": 10.5, "color": MUTED})])
rule(s, M, ny + In(1.02), In(11.77))
ly = ny + In(1.32)
box(s, M, ly, In(7.3), In(1.52), fill=AMBERL, border=None, radius=0.07)
txt(s, M + In(0.3), ly + In(0.22), In(6.7), In(1.2),
    [[("르몽 리뷰 데이터는 식당 리뷰로 쓰지 않았습니다",
       {"size": 13, "bold": True, "color": AMBER})],
     [("유튜버 방문 식당 617곳을 르몽 매장 32,449곳과 맞춰 보니 2곳(0.3%)만 겹쳤습니다. "
       "르몽은 전체의 98.5%가 배달 플랫폼 리뷰라 노포는 들어올 수 없습니다. "
       "대신 르몽 리뷰로 만든 항목별 감성 사전을 방문형으로 고쳐 유튜브 댓글에 적용했습니다 "
       "— 식당을 이은 게 아니라 분석기를 옮긴 것입니다.", {"size": 11, "color": INK})]],
    line=1.45, space_after=5)
box(s, M + In(7.6), ly, In(4.17), In(1.52), fill=None, border=LINE, radius=0.07)
txt(s, M + In(7.9), ly + In(0.22), In(3.6), In(1.2),
    [[("아직 안 된 것", {"size": 13, "bold": True, "color": INK})],
     [("· 지도 키 미발급 — 경계를 직접 렌더해 대체", {"size": 10.5, "color": MUTED})],
     [("· 성시경 214곳은 좌표가 없어 미탑재", {"size": 10.5, "color": MUTED})],
     [("· 방문 분류 정확도 사람 검수 전", {"size": 10.5, "color": MUTED})]],
    line=1.4, space_after=3)
page(s, 9)

# ─────────────────────────────────────────────── 10. 계획 + 피드백 요청

s = slide(
 "[8:10–8:50 · 40초]\n"
 "최종발표까지 한 달입니다. 세 덩어리로 나눴습니다.\n"
 "11월 첫째 주는 데이터를 넓힙니다 — 지오코딩 키를 받아 성시경 214곳을 지도에 올리고 채널을 늘립니다.\n"
 "둘째 주는 사람이 검수합니다. 방문 분류가 맞는지 표본 300개를 직접 읽고 정확도를 재겠습니다. "
 "지금 이 숫자가 맞다고 말할 근거가 아직 없기 때문입니다.\n"
 "셋째 주는 실사용자 5명에게 과업을 주고 막히는 데를 고칩니다.\n"
 "마지막으로 두 가지를 여쭙고 싶습니다. "
 "첫째, 저희가 잡은 이 상황과 문제가 충분히 구체적입니까. "
 "둘째, 방문자 반응이 식당을 고르는 데 실제로 필요한 정보입니까.\n"
 "감사합니다.")
y = head(s, "09  남은 계획", "11.25 최종발표까지 — 넓히고, 검수하고, 써 보게 한다")
plans = [("11.01 – 11.08", "데이터 연결 · 지도 작동",
          "지오코딩 키 확보 → 성시경 214곳 좌표 보강\n채널 추가 수집 · 댓글 표본 점검"),
         ("11.09 – 11.16", "분석 · 사람 검수",
          "방문 분류 표본 300개 직접 검수 · 정확도 측정\n영상–식당 연결 오류 점검 · 배지 기준 재검토"),
         ("11.17 – 11.25", "사용자 점검 · 안정화",
          "실사용자 5명 과업 테스트\n발표 시연 경로 고정 · 녹화 백업")]
for i, (d, t, b) in enumerate(plans):
    x = M + i * In(4.0)
    bx = box(s, x, y, In(3.7), In(1.85), fill=C(0xFF, 0xFF, 0xFF), radius=0.05)
    rule(s, x, y, In(3.7), GREEN, Emu(28575))
    txt(s, x + In(0.26), y + In(0.26), In(3.2), In(0.26),
        [(d, {"size": 10.5, "bold": True, "color": GREEN})])
    txt(s, x + In(0.26), y + In(0.58), In(3.2), In(0.3),
        [(t, {"size": 14.5, "bold": True, "color": INK})])
    txt(s, x + In(0.26), y + In(1.0), In(3.2), In(0.7),
        [(b, {"size": 11, "color": MUTED})], line=1.45)
qy = y + In(2.55)
box(s, M, qy, In(11.77), In(1.9), fill=GREENL, border=None, radius=0.06)
txt(s, M + In(0.4), qy + In(0.32), In(11.0), In(0.3),
    [("심사위원께 확인받고 싶은 것", {"size": 12, "bold": True, "color": GREEN})])
txt(s, M + In(0.4), qy + In(0.8), In(5.2), In(0.9),
    [[("1", {"size": 11, "bold": True, "color": GREEN})],
     [("이 상황과 문제가 충분히 구체적입니까?", {"size": 16, "bold": True, "color": INK})]],
    line=1.3, space_after=3)
txt(s, M + In(6.1), qy + In(0.8), In(5.4), In(0.9),
    [[("2", {"size": 11, "bold": True, "color": GREEN})],
     [("방문자 반응이 식당 선택에 필요한 정보입니까?", {"size": 16, "bold": True, "color": INK})]],
    line=1.3, space_after=3)
page(s, 10)

prs.save(str(OUT))


# ─────────────────────────────────────────────── 자동 검사

def check(path):
    """① 화면 밖으로 나간 도형 ② 상자 높이보다 길어 보이는 글 ③ 빠진 발표자 노트."""
    d = Presentation(str(path))
    bad = 0
    for i, sl in enumerate(d.slides, 1):
        msgs = []
        for sh in sl.shapes:
            if sh.left is None:
                continue
            if sh.left < -9525 or sh.top < -9525 or \
               sh.left + sh.width > d.slide_width + 9525 or \
               sh.top + sh.height > d.slide_height + 9525:
                msgs.append(f"화면 밖: {sh.shape_type} {sh.name}")
            if not sh.has_text_frame:
                continue
            # 글자 수로 줄 수를 어림잡아 상자 높이와 비교합니다 (한글 1자 ≈ 글자크기)
            need = 0.0
            paras = sh.text_frame.paragraphs
            for pi, para in enumerate(paras):
                t = "".join(r.text for r in para.runs)
                if not t:
                    continue
                pt = max((r.font.size.pt for r in para.runs if r.font.size), default=12)
                per = max(1, int((sh.width / 12700) / (pt * 0.92)))
                lines = max(1, -(-len(t) // per))
                need += lines * pt * (para.line_spacing or 1.0)
                if pi < len(paras) - 1 and para.space_after:
                    need += para.space_after.pt
            if need * 12700 > sh.height * 1.18:
                msgs.append(f"넘침 의심: “{sh.text_frame.text[:18]}…” "
                            f"{need/72:.2f}in > {sh.height/914400:.2f}in")
        if not sl.has_notes_slide or not sl.notes_slide.notes_text_frame.text.strip():
            msgs.append("발표자 노트 없음")
        if msgs:
            bad += len(msgs)
            print(f"  s{i}: " + " / ".join(msgs))
    return bad


print("저장:", OUT)
print("슬라이드:", len(prs.slides.__iter__.__self__._sldIdLst), "· 검사 결과")
print("  문제 없음" if check(OUT) == 0 else "  ↑ 확인 필요")

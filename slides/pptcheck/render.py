# -*- coding: utf-8 -*-
"""PPTX를 PNG로 그려서 눈으로 확인하는 도구.

이 맥에 LibreOffice가 없고 Keynote 자동화 권한도 막혀 있어서, 발표 자료가 실제로
어떻게 보이는지 확인할 방법이 없었습니다. 그래서 python-pptx 로 도형을 읽고
PIL 로 직접 그립니다. 글꼴은 PPT에 지정된 것과 같은 Apple SD Gothic Neo 를 쓰므로
줄바꿈과 넘침은 PowerPoint 와 비슷하게 나옵니다.

완벽한 렌더러가 아닙니다. 그림자·그라디언트·표·차트는 그리지 않습니다.
도형 상자, 그림, 글자 배치를 확인하는 용도입니다.

  python3 pptcheck/render.py slides/4조_중간발표_르슐랭가이드.pptx [출력폴더]
"""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu

TTC = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FACE = {False: 0, True: 6}            # Regular / Bold
WIDTH = 1400                          # 기존 preview/*.png 와 같은 폭
_cache = {}


def font(size_pt, bold, scale):
    key = (round(size_pt * scale), bold)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(TTC, max(1, key[0]), index=FACE[bold])
    return _cache[key]


def rgb(color, default=(0, 0, 0)):
    try:
        if color and color.type is not None and color.rgb is not None:
            return tuple(bytes.fromhex(str(color.rgb)))
    except Exception:
        pass
    return default


def fill_of(shape):
    try:
        f = shape.fill
        if f.type is not None and f.type == 1:          # solid
            return rgb(f.fore_color, None)
    except Exception:
        pass
    return None


def line_of(shape):
    try:
        ln = shape.line
        if ln.fill.type == 1:
            w = int((ln.width or Emu(9525)) / 12700)
            return rgb(ln.color, (0, 0, 0)), max(1, w)
    except Exception:
        pass
    return None


def wrap(runs, box_w, draw, scale):
    """런(글자 조각) 목록을 상자 폭에 맞춰 줄로 자릅니다. 한 줄 = [(글자, 폰트, 색)]."""
    lines, cur, cur_w = [], [], 0
    for text, f, col in runs:
        for ch in text:
            if ch in "\n\v":          # run.text 의 \n 은 PPT에서 줄바꿈(<a:br/>)입니다
                lines.append(cur); cur, cur_w = [], 0
                continue
            w = draw.textlength(ch, font=f)
            if cur and cur_w + w > box_w and ch != " ":
                lines.append(cur); cur, cur_w = [], 0
            cur.append((ch, f, col)); cur_w += w
    if cur:
        lines.append(cur)
    return lines or [[]]


def draw_text(draw, shape, scale):
    tf = shape.text_frame
    x0 = shape.left / 12700 * scale
    y = shape.top / 12700 * scale
    box_w = shape.width / 12700 * scale
    paras = tf.paragraphs
    for pi, para in enumerate(paras):
        runs = []
        for r in para.runs:
            pt = r.font.size.pt if r.font.size else 12
            runs.append((r.text, font(pt, bool(r.font.bold), scale),
                         rgb(r.font.color, (0, 0, 0))))
        if not runs:
            y += 12 * scale
            continue
        big = max(r.font.size.pt for r in para.runs if r.font.size) if \
            any(r.font.size for r in para.runs) else 12
        lh = big * (para.line_spacing or 1.0) * scale
        for ln in wrap(runs, box_w, draw, scale):
            w = sum(draw.textlength(c, font=f) for c, f, _ in ln)
            if para.alignment == PP_ALIGN.CENTER:
                x = x0 + (box_w - w) / 2
            elif para.alignment == PP_ALIGN.RIGHT:
                x = x0 + box_w - w
            else:
                x = x0
            base = y + (lh - big * scale) / 2
            for c, f, col in ln:
                draw.text((x, base), c, font=f, fill=col)
                x += draw.textlength(c, font=f)
            y += lh
        if pi < len(paras) - 1 and para.space_after:
            y += para.space_after.pt * scale


def render(pptx, outdir):
    prs = Presentation(str(pptx))
    scale = WIDTH / (prs.slide_width / 12700)
    H = int(prs.slide_height / 12700 * scale)
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    made = []
    for i, sl in enumerate(prs.slides, 1):
        img = Image.new("RGB", (WIDTH, H), "white")
        d = ImageDraw.Draw(img)
        for sh in sl.shapes:
            if sh.left is None:
                continue
            x, y = sh.left / 12700 * scale, sh.top / 12700 * scale
            w, h = sh.width / 12700 * scale, sh.height / 12700 * scale
            rect = [x, y, x + w, y + h]
            if sh.shape_type == 13:                      # 그림
                im = Image.open(sh.image.blob and __import__("io").BytesIO(sh.image.blob))
                img.paste(im.convert("RGB").resize((max(1, int(w)), max(1, int(h)))),
                          (int(x), int(y)))
                continue
            f, ln = fill_of(sh), line_of(sh)
            if f or ln:
                radius = 10 if "Rounded" in str(sh.shape_type) else 0
                if radius:
                    d.rounded_rectangle(rect, radius=radius, fill=f,
                                        outline=ln[0] if ln else None, width=ln[1] if ln else 1)
                else:
                    d.rectangle(rect, fill=f, outline=ln[0] if ln else None,
                                width=ln[1] if ln else 1)
            if sh.has_text_frame and sh.text_frame.text.strip():
                draw_text(d, sh, scale)
        p = outdir / f"s{i:02d}.png"
        img.save(p); made.append(p)
    print(f"{len(made)}장 → {outdir}")
    return made


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else \
        str(pathlib.Path(__file__).parent.parent / "4조_중간발표_르슐랭가이드.pptx")
    out = sys.argv[2] if len(sys.argv) > 2 else str(pathlib.Path(__file__).parent / "out")
    render(src, out)

"""index.html → 공유용 단독 HTML. 배포할 때마다 실행하세요."""
import pathlib
src = pathlib.Path(__file__).parent / "index.html"
dst = pathlib.Path(__file__).parent / "돌려봄_데모.html"
body = src.read_text()
dst.write_text(f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="강남구 배달 리뷰 209,871건 분석 · 캡스톤 4조">
<style>
  html{{color-scheme:light dark}}
  body{{margin:0;font:14px system-ui,sans-serif}}
  img{{max-width:100%}}
  [hidden]{{display:none!important}}
</style>
{body}
</body>
</html>
""")
print(f"{dst.name}  {dst.stat().st_size//1024}KB")

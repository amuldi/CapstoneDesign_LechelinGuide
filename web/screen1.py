"""index.html의 첫 화면을 조건 선택형으로 교체합니다. 상세 화면은 그대로 둡니다."""
import pathlib, re, json

p = pathlib.Path(__file__).parent / "index.html"
h = p.read_text()

# ---------- CSS ----------
old_css = re.search(r"/\* ===== 화면 1 · 원판 ===== \*/.*?(?=/\* ===== 화면 2)", h, re.S).group(0)
new_css = '''/* ===== 화면 1 · 조건 선택 ===== */
#pick{padding:26px 0 0}
#pick h1{margin:0; font-size:28px; font-weight:700; letter-spacing:-.022em; line-height:1.28; text-wrap:balance}
#pick .lead{margin:10px 0 0; font-size:13.5px; color:var(--ink-2); line-height:1.6}

.step{margin-top:26px}
.step > .q{display:flex; justify-content:space-between; align-items:baseline; margin-bottom:9px}
.step .q b{font-size:13.5px; font-weight:600}
.step .q span{font-size:11.5px; color:var(--ink-3)}
.chips{display:flex; flex-wrap:wrap; gap:6px}
.mchip{
  display:inline-flex; align-items:baseline; gap:5px; padding:7px 12px;
  border:1px solid var(--line-strong); border-radius:16px; background:var(--surface);
  font-size:13px; color:var(--ink-2); transition:background .12s,border-color .12s,color .12s;
}
.mchip i{font-style:normal; font-family:"IBM Plex Mono",monospace; font-size:10.5px; color:var(--ink-3)}
.mchip[aria-pressed="true"]{background:var(--accent); border-color:var(--accent); color:var(--on-accent); font-weight:600}
.mchip[aria-pressed="true"] i{color:var(--on-accent); opacity:.7}

/* 후보 3곳 비교 */
.result{margin-top:28px; padding-top:22px; border-top:1px solid var(--line)}
.result h2{margin:0; font-size:15px; font-weight:600}
.result .note{margin:3px 0 0; font-size:12px; color:var(--ink-3); line-height:1.5}
.cands{display:flex; flex-direction:column; gap:1px; margin-top:16px; background:var(--line); border:1px solid var(--line); border-radius:7px; overflow:hidden}
.cand{display:flex; align-items:center; gap:11px; padding:13px; background:var(--surface)}
.cand.top{background:var(--accent-soft)}
.cand .no{width:16px; flex:none; font-family:"IBM Plex Mono",monospace; font-size:12px; font-weight:600; color:var(--ink-3)}
.cand.top .no{color:var(--accent-ink)}
.cand .info{flex:1; min-width:0}
.cand .nm{font-size:13.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.cand.top .nm{font-weight:600; color:var(--accent-ink)}
.cand .sub2{margin-top:2px; font-size:11px; color:var(--ink-3)}
.cand .bar{width:66px; flex:none; height:7px; background:var(--track); border-radius:4px; overflow:hidden}
.cand .bar i{display:block; height:100%; background:var(--ink-3); border-radius:0 4px 4px 0}
.cand.top .bar i{background:var(--accent)}
.cand .sc{width:38px; flex:none; text-align:right; font-size:14px; font-weight:600; font-family:"IBM Plex Mono",monospace}

.acts2{display:flex; gap:9px; margin-top:16px}
.acts2 button{flex:1; padding:14px 10px; border-radius:8px; font-size:14.5px; font-weight:600; letter-spacing:-.01em}
.btn-primary{background:var(--accent); color:var(--on-accent); border:0}
.btn-primary:hover{opacity:.9}
.btn-ghost{background:none; color:var(--ink-2); border:1px solid var(--line-strong)}
.btn-ghost:hover{color:var(--ink); border-color:var(--ink-3)}
.thin{margin-top:13px; font-size:11.5px; color:var(--warn); line-height:1.5}

/* 원판 */
.wheelwrap{margin-top:24px; padding-top:22px; border-top:1px solid var(--line); text-align:center}
.wheelwrap h2{margin:0 0 4px; font-size:15px; font-weight:600}
.wheelwrap .note{margin:0 0 4px; font-size:12px; color:var(--ink-3)}
.wheelbox{position:relative; width:min(320px,80vw); margin:18px auto 0}
#wheel{display:block; width:100%; height:auto}
.rim{fill:none; stroke:var(--line-strong); stroke-width:3}
.peg{fill:var(--surface); stroke:var(--line-strong); stroke-width:1}
.hub{fill:var(--surface); stroke:var(--line-strong); stroke-width:1.5}
.hubtext{fill:var(--ink-3); font-size:11px; font-weight:600; letter-spacing:.06em}
.needle{fill:var(--ink); stroke:var(--bg); stroke-width:1.5; stroke-linejoin:round}
.slice{stroke:var(--bg); stroke-width:2}
.s0{fill:var(--w1)} .s1{fill:var(--w2)} .s2{fill:var(--w3)}
.s3{fill:var(--w4)} .s4{fill:var(--w5)} .s5{fill:var(--w6)}
.slice-label{font-weight:600; letter-spacing:-.02em}
.l0,.l1,.l2{fill:var(--wink)}
.l3,.l4,.l5{fill:var(--wink-alt)}
.spin{
  width:100%; max-width:320px; margin:18px auto 0; display:block; padding:15px 20px;
  background:var(--accent); color:var(--on-accent); border:0; border-radius:8px;
  font-size:15.5px; font-weight:600; transition:opacity .15s;
}
.spin:hover{opacity:.9}
.spin:disabled{opacity:.45; cursor:default}

.gate{margin:26px 0 0; padding:16px 18px; background:var(--surface); border:1px solid var(--line); border-radius:8px}
.gate h2{margin:0 0 4px; font-size:13.5px; font-weight:600}
.gate p{margin:0 0 12px; font-size:12.5px; color:var(--ink-2); line-height:1.55}
.gate ul{margin:0; padding:0; list-style:none; display:flex; flex-direction:column; gap:7px}
.gate li{display:flex; gap:9px; align-items:flex-start; font-size:12.5px; color:var(--ink-2); line-height:1.5}
.gate li::before{content:"\\2713"; flex:none; color:var(--accent); font-weight:700; font-size:12px; line-height:1.55}
.gate .count{display:flex; justify-content:space-between; align-items:baseline; margin-top:13px; padding-top:12px; border-top:1px solid var(--line)}
.gate .count span{font-size:12.5px; color:var(--ink-3)}
.gate .count b{font-size:15px; font-weight:600}

'''
h = h.replace(old_css, new_css)

# 항목 신뢰도 뱃지
h = h.replace(".ament{width:62px;",
 '.tag{flex:none; font-size:10.5px; padding:1px 6px; border-radius:3px; background:var(--warn-soft); color:var(--warn); font-weight:600}\n'
 ".ament{width:58px;")

# ---------- HTML ----------
old_html = re.search(r'  <!-- ===== 화면 1 · 원판 ===== -->.*?(?=  <!-- ===== 화면 2)', h, re.S).group(0)
new_html = '''  <!-- ===== 화면 1 · 조건 선택 ===== -->
  <div id="pick">
    <h1>둘 다 4.9점인데,<br>어디가 더 나을까요?</h1>
    <p class="lead" id="lead"></p>

    <div class="step">
      <div class="q"><b>어떤 메뉴를 찾나요?</b><span>숫자 = 비교한 매장 수</span></div>
      <div class="chips" id="menuChips"></div>
    </div>

    <div class="step">
      <div class="q"><b>무엇이 가장 중요한가요?</b><span>이 기준으로 줄을 세웁니다</span></div>
      <div class="chips" id="aspectChips"></div>
    </div>

    <div class="result">
      <h2 id="resTitle"></h2>
      <p class="note" id="resNote"></p>
      <div class="cands" id="cands"></div>
      <p class="thin" id="thinWarn" hidden></p>
      <div class="acts2">
        <button type="button" class="btn-primary" id="goTop">1위 분석 보기</button>
        <button type="button" class="btn-ghost" id="goWheel">셋 중 뽑기</button>
      </div>
    </div>

    <div class="wheelwrap" id="wheelWrap" hidden>
      <h2>그래도 못 고르겠다면</h2>
      <p class="note">위 세 곳 중에서만 뽑습니다. 분석을 통과한 후보들입니다.</p>
      <div class="wheelbox">
        <svg id="wheel" viewBox="0 0 300 300" role="img" aria-label="후보 원판">
          <g id="wheelRot"></g>
          <circle class="rim" cx="150" cy="150" r="140"></circle>
          <circle class="hub" cx="150" cy="150" r="34"></circle>
          <text class="hubtext" id="hubRegion" x="150" y="155" text-anchor="middle"></text>
          <g id="needle"><path class="needle" d="M150,41 L139,13 Q150,2 161,13 Z"></path></g>
        </svg>
      </div>
      <button class="spin" id="spinBtn">원판 돌리기</button>
    </div>

    <div class="gate">
      <h2>후보가 되는 조건</h2>
      <p>원판에 올라가기 전에 아래를 통과한 매장만 비교 대상이 됩니다.</p>
      <ul>
        <li>2개 이상 플랫폼에 리뷰가 있는 매장</li>
        <li>분석 가능한 텍스트 리뷰 200건 이상</li>
        <li>리뷰 이벤트 키워드 패턴·중복 문구 리뷰 제외</li>
        <li>해당 항목 언급 30건 이상 (표본이 적으면 순위에서 제외)</li>
      </ul>
      <div class="count">
        <span>강남구에서 비교한 매장</span>
        <b class="num" id="gateCount"></b>
      </div>
    </div>
  </div>

'''
h = h.replace(old_html, new_html)
p.write_text(h)
print("screen1 html/css replaced")

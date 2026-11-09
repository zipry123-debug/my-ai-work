"""proposal-zine.html(원본, 수정 안 함)에 인터랙션·모션을 덧붙여 proposal-zine-interactive.html을 만든다.
레이아웃·색·질감·텍스트는 그대로 두고, 화면 전용 장(페르소나 탭)만 추가한다. 인쇄에서는 원본 4·5장이 대신 나온다."""
from pathlib import Path

D = Path(__file__).parent
s = (D / "proposal-zine.html").read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:70])
    s = s.replace(a, b)


rep("<title>ZEROID 진 제안서</title>", "<title>ZEROID 진 제안서 인터랙티브</title>")
# JS가 꺼져 있으면 no-js 그대로 → 원본 4·5장이 보이고 화면 전용 장은 숨김
rep('<html lang="ko">', '<html lang="ko" class="no-js">')
rep('<meta name="claude:viewport-fit-sides" content="cover">',
    '<meta name="claude:viewport-fit-sides" content="cover">\n'
    '<script>document.documentElement.classList.replace("no-js","js")</script>\n'
    '<script src="https://cdn.tailwindcss.com/3.4.17"></script>\n'
    '<script>tailwind.config={corePlugins:{preflight:false}}</script>')

# ---------- 화면 전용: 페르소나 탭 장 ----------
TAB_SLIDE = """<!-- ========== 화면 전용: 페르소나 탭 ========== -->
<div class="frame screen-only"><section class="slide" aria-label="페르소나 탭">
  <img class="p" src="tex/x_daily_sun.png" alt="" style="left:1760px;top:-40px;height:480px;transform:rotate(12deg)">
  <img class="p" src="tex/x_cream_mist.png" alt="" style="left:-70px;top:520px;height:560px;transform:rotate(-10deg)">
  <div class="pc" style="left:20px;top:0px;transform:rotate(-1.5deg)"><img class="bgp" src="tex/p4_ink.png" alt="">
    <h2 class="t kor on-ink" style="left:112px;top:74px;font-size:58px">고민 → <span class="riso">성수 팝업</span> → 무신사 재구매</h2></div>
  <div class="ransom" data-ransom="01 페르소나" data-seed="55" style="left:1240px;top:40px;font-size:48px;transform:rotate(3deg)"></div>
  <div class="ptabs" role="tablist" aria-label="페르소나 선택" id="ptabs"></div>
  <div class="pstack" id="pstack"></div>
  <div class="tag tear" style="left:150px;top:1036px;transform:rotate(-.4deg);font-size:18px;padding:4px 14px 6px">A~D는 올리브영 리뷰 패턴으로 만든 가상 인물 · E는 리뷰 근거가 없는 확장 가설 · 탭을 누르거나 ←/→로 바꿔 보세요</div>
</section></div>

"""
rep('<!-- ========== 4. 페르소나 A~C ========== -->\n<div class="frame">',
    TAB_SLIDE + '<!-- ========== 4. 페르소나 A~C ========== -->\n<div class="frame print-only">')
rep('<!-- ========== 5. 페르소나 D·E ========== -->\n<div class="frame">',
    '<!-- ========== 5. 페르소나 D·E ========== -->\n<div class="frame print-only">')

# ---------- ① 형광펜: 결론 문장 강조를 긋는 효과로 ----------
s = s.replace('<b style="background:var(--fluo)">', '<b class="hl">')
s = s.replace('<span style="background:var(--fluo);padding:0 10px;margin-right:10px">제안</span>',
              '<span class="hl" style="padding:0 10px;margin-right:10px">제안</span>')
# 카운트업 대상(최종값은 HTML에 그대로 둠)
rep('<b class="big" style="font-size:110px;color:var(--ink)">4.9만</b>', '<b class="big" style="font-size:110px;color:var(--ink)"><span data-count="4.9" data-dec="1">4.9</span>만</b>')
rep('<b class="big" style="font-size:150px;color:var(--ink)">4.9<small', '<b class="big" style="font-size:150px;color:var(--ink)"><span data-count="4.9" data-dec="1">4.9</span><small')
rep('<b class="big" style="font-size:150px">525<small', '<b class="big" style="font-size:150px"><span data-count="525">525</span><small')

# ---------- ③ 팝업 존 플립 카드 ----------
ZB = {
    "0": ("모든 방문객", "–", "약 4분", "피부 고민 3문항으로 내 상황에 맞는 체험 1곳을 안내합니다. 진단·측정은 하지 않습니다."),
    "1": ("A 장벽 회복러", "포밍 클렌저 · 인텐시브 크림", "약 8분", "거품 세안 시연을 보고 크림을 손등에 발라 봅니다."),
    "2": ("B 마감 주간 트러블러", "카밍 앰플 · 레드 컨트롤 크림", "약 8분", "앰플과 크림 2단계를 차례로 발라 보고 루틴 카드를 받습니다."),
    "3": ("C 메이크업 베이스 민감러", "수딩 크림 · 데일리 선크림", "약 8분", "크림과 선크림을 바른 뒤 사용감을 비교합니다. 쿠션 협업은 별도 협의."),
    "4": ("D 투어러 · E 러너(가설)", "크림 미스트 · 데일리 선크림", "약 8분", "분사감과 손등 사용감 체험. 샘플은 준비 수량 안에서."),
    "5": ("모든 방문객", "한정 패키지(크림+미스트+파우치)", "약 3분", "한정 구성 구매 시 파우치, QR로 무신사뷰티 온라인 연결."),
}
import re as _re
a = s.index('aria-label="팝업 공간 구성"'); b = s.index("</section>", a)
blk = s[a:b]
TAPE = ["tape0", "tape2", "tape1", "tape3", "tape2", "tape0"]


def flip(m):
    cls, style, inner = m.group(1) or "", m.group(2) or "", m.group(3)
    zn = _re.search(r'<b class="zn">(\d)</b>', inner).group(1)
    who, prod, mins, desc = ZB[zn]
    small = "font-size:26px" in inner
    title = _re.search(r"<h4[^>]*>(.*?)</h4>", inner).group(1)
    back = (f'<b class="zn" style="font-size:{40 if small else 52}px">{zn}</b>'
            f'<dl class="zd{" sm" if small else ""}"><dt>대상</dt><dd>{who}</dd><dt>제품</dt><dd>{prod}</dd><dt>시간</dt><dd>{mins}</dd></dl>'
            + ("" if small else f'<p style="font-size:19px;line-height:1.4">{desc}</p>'))
    t = TAPE[int(zn)]
    return (f'<button type="button" class="zflip" aria-pressed="false" aria-label="ZONE {zn} {title} — 눌러서 상세 보기"'
            f'{(" style=" + chr(34) + style + chr(34)) if style else ""}>'
            f'<img class="ztape" src="tex/{t}.png" alt="">'
            f'<span class="zin"><span class="face front zbox{cls}">{inner}<em class="zhint">눌러서 뒤집기 ↻</em></span>'
            f'<span class="face back zbox{cls}">{back}</span></span></button>')


blk2, n = _re.subn(r'<div class="zbox( end)?"(?: style="([^"]*)")?>(<b class="zn">.*?)</div>', flip, blk, flags=_re.S)
assert n == 6, n
s = s[:a] + blk2 + s[b:]

# ---------- ④ 시뮬레이션: 도장 토글 + 수치 연결 ----------
rep('<div class="ransom" data-ransom="04 기준안" data-seed="103" style="left:1400px;top:60px;font-size:50px;transform:rotate(3deg)"></div>',
    '''<div class="sim-ctrl screen-only" role="group" aria-label="입점 시뮬레이션 조건">
    <div class="sc-row" role="radiogroup" aria-label="시나리오">
      <button type="button" class="st-btn" role="radio" aria-checked="false" data-s="low">보수</button>
      <button type="button" class="st-btn" role="radio" aria-checked="true" data-s="base">기준</button>
      <button type="button" class="st-btn" role="radio" aria-checked="false" data-s="high">확장</button>
    </div>
    <button type="button" class="mode-btn" aria-pressed="true" id="modeBtn"><span class="mk">ON</span>온라인 동시 운영</button>
    <span class="sc-note">예상치 · 가정 기준</span>
  </div>
  <div class="ransom print-only" data-ransom="04 기준안" data-seed="103" style="left:1400px;top:60px;font-size:50px;transform:rotate(3deg)"></div>''')
for a_, b_ in [('3,675<small class="kor" style="font-size:40px">만 원</small></b><p style="font-size:19px">방문 7,000 × 전환 15% × 35,000원</p>',
                '<span id="kRev">3,675</span><small class="kor" style="font-size:40px">만 원</small></b><p style="font-size:19px" id="kRevD">방문 7,000 × 전환 15% × 35,000원</p>'),
               ('1,050<small class="kor" style="font-size:40px">명</small></b><p style="font-size:19px">1인 1건 가정</p>',
                '<span id="kBuy">1,050</span><small class="kor" style="font-size:40px">명</small></b><p style="font-size:19px">1인 1건 가정</p>'),
               ('525<small class="kor" style="font-size:40px">명</small></b><p style="font-size:19px">현장 구매자 중 50%</p>',
                '<span id="kOnl">525</span><small class="kor" style="font-size:40px" id="kOnlU">명</small></b><p style="font-size:19px" id="kOnlD">현장 구매자 중 50%</p>'),
               ('158<small class="kor" style="font-size:40px">명</small></b><p style="font-size:19px">첫 온라인 구매자 중 30%</p>',
                '<span id="kRep">158</span><small class="kor" style="font-size:40px" id="kRepU">명</small></b><p style="font-size:19px" id="kRepD">첫 온라인 구매자 중 30%</p>'),
               ('<b style="text-align:right">7,000</b>', '<b style="text-align:right" id="fVis">7,000</b>'),
               ('<i style="height:30px;background:var(--ink);width:15%"></i><b style="text-align:right">1,050</b>',
                '<i style="height:30px;background:var(--ink);width:15%" id="bBuy"></i><b style="text-align:right" id="fBuy">1,050</b>'),
               ('<i style="height:30px;background:var(--ink);width:7.5%"></i><b style="text-align:right">525</b>',
                '<i style="height:30px;background:var(--ink);width:7.5%" id="bOnl"></i><b style="text-align:right" id="fOnl">525</b>'),
               ('<i style="height:30px;background:var(--cobalt);width:2.25%;min-width:6px"></i><b style="text-align:right;color:var(--cobalt)">158</b>',
                '<i style="height:30px;background:var(--cobalt);width:2.25%;min-width:6px" id="bRep"></i><b style="text-align:right;color:var(--cobalt)" id="fRep">158</b>')]:
    rep(a_, b_)
rep('<span class="tag" style="position:static;align-self:flex-start;background:var(--cobalt);color:var(--white);font-weight:900;font-size:21px">팝업 + 온라인 동시</span>',
    '<span class="tag" id="fTag" style="position:static;align-self:flex-start;background:var(--cobalt);color:var(--white);font-weight:900;font-size:21px">팝업 + 온라인 동시 · 기준</span>')
rep('<div class="pc" style="left:20px;top:180px;transform:rotate(.6deg)"><img class="bgp" src="tex/p10_sheet.png" alt="">',
    '<div class="pc" style="left:20px;top:180px;transform:rotate(.6deg)" id="kSheet"><img class="bgp" src="tex/p10_sheet.png" alt="">\n'
    '    <div class="slam screen-only" id="slam" aria-hidden="true"><span id="slamT">기준안</span></div>')

# ---------- 인쇄·JS 꺼짐용: 존 상세 표 + 시나리오 표 ----------
rows = "".join(f"<tr><td><b>ZONE {k}</b></td><td>{v[0]}</td><td>{v[1]}</td><td>{v[2]}</td><td>{v[3]}</td></tr>" for k, v in ZB.items())
SC = [("보수", 5000, 10, 40, 20), ("기준", 7000, 15, 50, 30), ("확장", 9000, 20, 60, 35)]


def f0(x):
    return f"{round(x):,}"


srows = ""
for nm, vis, cv, on, rp in SC:
    buy = vis * cv / 100; onl = buy * on / 100; rep_ = onl * rp / 100
    srows += f"<tr><td><b>{nm}</b></td><td>{vis:,}명 · {cv}% · {on}% · {rp}%</td><td>{f0(buy*35000/10000)}만 원</td><td>{f0(buy)}명</td><td>{f0(onl)}명</td><td>{f0(rep_)}명</td><td>측정 불가</td></tr>"
PRINT = f"""
<!-- ========== 인쇄·JS 꺼짐용: 존 상세 / 시나리오 표 ========== -->
<div class="frame print-only"><section class="slide" aria-label="팝업 존 상세">
  <div class="pc" style="left:20px;top:10px;transform:rotate(-1deg)"><img class="bgp" src="tex/p8_ink.png" alt="">
    <h2 class="t kor on-ink" style="left:112px;top:74px;font-size:60px">팝업 존 카드 뒷면: 존별 상세</h2></div>
  <div class="pc" style="left:40px;top:200px;transform:rotate(.4deg)"><img class="bgp" src="tex/pr_sheet1.png" alt="">
    <div class="in" style="padding:60px 66px"><table class="ptbl"><thead><tr><th>존</th><th>대상</th><th>체험 제품</th><th>시간</th><th>내용</th></tr></thead><tbody>{rows}</tbody></table>
    <p style="font-size:18px;color:#55555a">개념 배치 · 약 15평 가정 · 실제 면적·피난 동선 확인 후 확정</p></div></div>
</section></div>
<div class="frame print-only"><section class="slide" aria-label="시뮬레이션 시나리오 표">
  <div class="pc" style="left:20px;top:10px;transform:rotate(1deg)"><img class="bgp" src="tex/p10_ink.png" alt="">
    <h2 class="t kor on-ink" style="left:112px;top:74px;font-size:60px">입점 시뮬레이션: 시나리오 전체</h2></div>
  <div class="pc" style="left:40px;top:200px;transform:rotate(-.4deg)"><img class="bgp" src="tex/pr_sheet2.png" alt="">
    <div class="in" style="padding:60px 66px"><table class="ptbl"><thead><tr><th>시나리오</th><th>방문 · 구매전환 · 온라인 전환 · 재구매</th><th>2주 현장 매출</th><th>현장 구매자</th><th>첫 온라인 구매자</th><th>90일 재구매</th><th>팝업만 운영 시 재구매</th></tr></thead><tbody>{srows}</tbody></table>
    <p style="font-size:19px;line-height:1.5">객단가 35,000원 · 1인 1건 가정. 팝업만 운영하면 온라인 주문 이력이 없어 첫 온라인 구매·재구매를 측정할 수 없습니다.</p>
    <p style="font-size:18px;color:#55555a">예상치 · 가정 기준 · 실적 아님 · 시나리오 수치는 웹 제안서의 보수/기준/확장 가정</p></div></div>
</section></div>
"""
rep("<!-- ========== 11. 일정 ========== -->", PRINT + "\n<!-- ========== 11. 일정 ========== -->")

CSS = r"""
/* ===== 인터랙티브: 화면/인쇄 전환 ===== */
.js .print-only{display:none}
.no-js .screen-only{display:none}
/* 페르소나 탭: 종이 인덱스 탭 + 카드가 위에서 덮이는 전환 */
.ptabs{position:absolute;left:150px;top:176px;width:1600px;height:110px}
.ptab{position:absolute;bottom:0;z-index:1;width:290px;height:96px;border:0;cursor:pointer;font-family:var(--sans);color:var(--ink);
  background:#DDD3BF;padding:16px 22px 0;text-align:left;display:flex;gap:14px;align-items:flex-start;
  clip-path:polygon(5% 4%,12% 0,88% 1%,95% 5%,100% 100%,0 100%);transition:transform .22s cubic-bezier(.3,.7,.3,1.4),background .22s}
.ptab .lt{flex:none;width:52px;height:52px;border-radius:50%;background:var(--cobalt);color:var(--white);display:flex;align-items:center;justify-content:center;
  font-family:var(--latin);font-size:34px;line-height:1}
.ptab.hyp .lt{background:var(--paper);color:var(--ink);outline:3px dashed var(--ink);outline-offset:-5px}
.ptab .nm{font-size:22px;font-weight:900;line-height:1.2;padding-top:4px}
.ptab .nm small{display:block;font-size:18px;font-weight:700;color:#55555a}
.ptab:hover{transform:translateY(-6px)}
.ptab[aria-selected="true"]{background:var(--white);transform:translateY(-14px);z-index:4}
.ptab.hyp[aria-selected="true"]{background:var(--paper)}
.ptab:focus-visible{outline:4px solid var(--fluo);outline-offset:2px}
.pstack{position:absolute;left:140px;top:240px;width:1640px;height:800px;z-index:2}
.pcard{position:absolute;inset:0;transform-origin:30% 0}
.pcard>.bgp{position:absolute;left:0;top:0;width:1640px;height:800px}
.pcard>.in{position:absolute;inset:40px;padding:56px 64px 46px;display:grid;grid-template-columns:500px 1fr;gap:20px 56px}
.pcard .tp{position:absolute;top:22px}
.pcard.drop{animation:pdrop .46s cubic-bezier(.2,.85,.3,1.08) both}
.pcard.drop .tp{animation:slap .18s .36s cubic-bezier(.3,.7,.4,1) both}
.pcard.under{animation:punder .3s ease-in both}
@keyframes pdrop{0%{transform:translate(-36px,-120px) rotate(-7deg)}70%{transform:translate(0,6px) rotate(calc(var(--r) + .6deg))}100%{transform:rotate(var(--r))}}
@keyframes punder{to{transform:translateY(8px) rotate(calc(var(--r) - .4deg))}}
@keyframes slap{0%{transform:scale(1.6) rotate(var(--tr))}100%{transform:scale(1) rotate(var(--tr))}}
.pj{display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:1fr 1fr;gap:18px;flex:1;counter-reset:st}
.pj div{border-left:6px solid var(--ink);padding:10px 12px 12px 18px;counter-increment:st;position:relative}
.pj div::before{content:counter(st);display:block;font-family:var(--latin);font-size:54px;line-height:1;color:#cfc8b8;margin-bottom:6px}
.pj div.pop::before{color:var(--fluo)}
.pj div.pop{border-color:var(--fluo);background:#F6EFE0}
.pj small{display:block;font-size:18px;font-weight:700;color:#55555a}
.pj b{display:block;font-size:30px;line-height:1.25;font-weight:900;margin-top:2px}
.pprod{display:flex;gap:8px;align-items:flex-end;height:270px}
.pprod img{height:100%;width:auto}
/* ① 타이포: 랜섬 조각이 툭툭 붙음 · 형광펜 */
.js .ransom.wait span{transform:scale(1.7) rotate(var(--rr,0deg));opacity:0}
.ransom.go span{animation:stick .26s cubic-bezier(.25,.8,.35,1.15) both}
@keyframes stick{0%{transform:scale(1.7) rotate(var(--rr,0deg));opacity:0}60%{opacity:1}100%{transform:var(--fin);opacity:1}}
.hl{background:linear-gradient(transparent 8%,var(--fluo) 8%,var(--fluo) 92%,transparent 92%) no-repeat 0 0/100% 100%}
.js .hl.wait{background-size:0% 100%}
.hl.go{transition:background-size .5s cubic-bezier(.4,.1,.3,1)}
/* ③ 존 플립 카드 */
.zflip{position:relative;display:block;border:0;padding:0;margin:0;background:none;font:inherit;color:inherit;text-align:left;cursor:pointer;perspective:1400px;
  transition:transform .22s cubic-bezier(.3,.7,.3,1.3),filter .22s;filter:drop-shadow(2px 3px 2px rgba(20,16,10,.18))}
.zflip .zin{position:relative;display:block;width:100%;height:100%;transform-style:preserve-3d;transition:transform .52s cubic-bezier(.45,.05,.3,1)}
.zflip .face{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden}
.zflip .back{transform:rotateY(180deg);background:#F6EFE0}
.zflip[aria-pressed="true"] .zin{transform:rotateY(180deg)}
.zflip .ztape{position:absolute;top:-16px;left:50%;width:120px;height:auto;z-index:2;transform:translateX(-50%) rotate(-4deg);transition:transform .22s}
.zhint{position:absolute;right:12px;bottom:8px;font-style:normal;font-size:18px;font-weight:700;color:var(--cobalt)}
.zd{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:2px 0 0;font-size:20px;line-height:1.35}
.zd dt{font-weight:900;color:#55555a}.zd dd{margin:0;font-weight:700}
.zd.sm{font-size:18px;gap:2px 8px}
@media (hover:hover){.zflip:hover{transform:translateY(-8px) rotate(-.6deg);filter:drop-shadow(8px 16px 10px rgba(20,16,10,.28))}
  .zflip:hover .ztape{transform:translateX(-50%) rotate(-4deg) scaleX(1.12) scaleY(.92)}}
.zflip:focus-visible{outline:4px solid var(--fluo);outline-offset:4px}
/* ④ 시뮬레이션 도장 토글 */
.sim-ctrl{position:absolute;left:1180px;top:22px;display:flex;align-items:center;gap:16px;z-index:5}
.sc-row{display:flex;gap:10px}
.st-btn{width:104px;height:104px;border-radius:50%;border:5px solid var(--ink);background:var(--white);color:var(--ink);font-family:var(--poster);font-size:30px;cursor:pointer;
  box-shadow:3px 5px 8px rgba(20,16,10,.3);transition:transform .2s}
.st-btn[aria-checked="true"]{background:var(--cobalt);border-color:var(--cobalt);color:var(--white);transform:rotate(-8deg)}
.mode-btn{display:flex;align-items:center;gap:10px;border:0;background:var(--white);font-family:var(--sans);font-size:22px;font-weight:900;color:var(--ink);padding:14px 18px;cursor:pointer;
  box-shadow:3px 5px 8px rgba(20,16,10,.3);clip-path:polygon(0 6%,4% 0,50% 4%,96% 0,100% 8%,98% 50%,100% 94%,94% 100%,50% 96%,4% 100%,0 92%,2% 50%)}
.mode-btn .mk{display:inline-flex;width:62px;height:62px;border-radius:50%;align-items:center;justify-content:center;border:4px solid var(--fluo);color:var(--fluo);font-family:var(--latin);font-size:24px;transform:rotate(-12deg)}
.mode-btn[aria-pressed="false"] .mk{border-color:#7a7a80;color:#7a7a80;transform:rotate(10deg)}
.st-btn:focus-visible,.mode-btn:focus-visible{outline:4px solid var(--fluo);outline-offset:3px}
.sc-note{position:absolute;right:-6px;top:118px;font-size:18px;font-weight:700;background:var(--white);padding:2px 10px;white-space:nowrap}
.slam{position:absolute;right:120px;top:-26px;z-index:6;width:200px;height:200px;border-radius:50%;border:8px solid var(--fluo);color:var(--fluo);display:flex;align-items:center;justify-content:center;
  font-family:var(--poster);font-size:44px;transform:rotate(-14deg);pointer-events:none;opacity:0}
.slam.on{opacity:.9;animation:slam .32s cubic-bezier(.2,.9,.35,1.1) both}
@keyframes slam{0%{transform:scale(2.2) rotate(-24deg);opacity:0}55%{transform:scale(.94) rotate(-13deg);opacity:.95}100%{transform:scale(1) rotate(-14deg);opacity:.9}}
.thud{animation:thud .2s ease-out}
@keyframes thud{0%{translate:0 0}40%{translate:0 5px}100%{translate:0 0}}
#kSheet .big span,#kOnlU,#kRepU{transition:color .2s}
.na{color:#9a958a!important}
/* 인쇄용 표 */
.ptbl{width:100%;border-collapse:collapse;font-size:22px;line-height:1.4}
.ptbl th{text-align:left;font-size:19px;color:#55555a;border-bottom:3px solid var(--ink);padding:8px 10px}
.ptbl td{border-bottom:1px solid #cfc8b8;padding:12px 10px;vertical-align:top}
@media (prefers-reduced-motion: reduce){.pcard.drop,.pcard.drop .tp,.pcard.under,.ransom.go span,.slam.on,.thud{animation:none}
  .ptab,.zflip,.zflip .zin,.zflip .ztape,.hl.go,.st-btn{transition:none}}
@media print{.js .ransom.wait span{transform:var(--fin);opacity:1}.js .hl.wait{background-size:100% 100%}.slam,.sim-ctrl,.zhint{display:none!important}
  .zflip .zin{transform:none!important}.zflip .back{display:none}}
@media print{.screen-only{display:none!important}.print-only{display:block!important}}
"""
rep("</style>", CSS + "\n</style>")

JS = r"""
// ===== 페르소나 탭 (화면 전용 장) =====
(function(){
  var tabs=document.getElementById("ptabs"), stack=document.getElementById("pstack"); if(!tabs)return;
  var P=[
    {k:"a",L:"A",n:"장벽 회복러",who:"29세 · 성수동 IT 마케터 · 건성·민감 · 홈 각질 관리를 자주 함",prods:["foaming_cleanser","intensive_cream","daily_sun"],stat:"74%",sd:"포밍 클렌저 ‘자극 없이 순해요’ 응답 (올리브영 구매자 설문)",
     j:[["고민","토 11:00","집에서 각질 관리"],["고민 심화","토 23:00","당김과 열감"],["성수 팝업","일 15:00","배리어 리커버리 라운지"],["제로이드 루틴","일 23:00","거품 세안 + 크림"],["만족","월 08:00","다음 날 사용감 확인"],["무신사뷰티","소진 시점","사용량에 맞춰 재구매"]]},
    {k:"b",L:"B",n:"마감 주간 트러블러",who:"24세 · 프리랜서 디자이너 · 복합성 · 마감마다 턱 트러블",prods:["calming_ampoule","red_control"],stat:"18%",sd:"도움순 리뷰 샘플의 트러블·붉은기 키워드 언급 · 재구매율과 구분",
     j:[["고민","월 · 마감 주간","야근과 수면 부족"],["고민 심화","수","강한 제품 역효과"],["성수 팝업","토 14:00","레드 SOS 바"],["제로이드 루틴","토 23:00","핌프로브 2-step"],["만족","다음 주 금","클라이언트 미팅"],["무신사뷰티","사용 후 판단","맞는 루틴만 재구매"]]},
    {k:"c",L:"C",n:"메이크업 베이스 민감러",who:"26세 · 패션 브랜드 MD · 수분 부족 지성 · 크림 유목민",prods:["soothing_cream","daily_sun"],stat:"15%",sd:"도움순 리뷰 샘플의 산뜻·안 끈적 언급 · 메이크업 적합성은 체험으로 확인",
     j:[["고민","평일 07:30","들뜨는 아침 화장"],["고민 심화","평일 13:00","점심 이후 밀림"],["성수 팝업","토 16:00","베이스 테스트 미러"],["제로이드 루틴","월 07:30","수딩 크림 → 선크림"],["만족","월 19:00","성수 저녁 약속"],["무신사뷰티","다음 쇼핑","메이크업 구매 때 함께 탐색"]]},
    {k:"d",L:"D",n:"성수 투어러 · 환절기 건조러",who:"23세 · 대학생 · 건성 · 주말마다 팝업 투어",prods:["cream_mist","cream_mask"],stat:"21%",sd:"도움순 리뷰 샘플의 건조·환절기 언급 · 굿즈 구매 유도 효과는 미확인",
     j:[["고민","토 14:00","성수 팝업 투어"],["고민 심화","토 16:00","화장 위 각질"],["성수 팝업","토 16:30","미스트 스테이션"],["제로이드 루틴","토 18:00","투어 중 수시로"],["만족","토 22:00","집에서 크림 마스크"],["무신사뷰티","체험 후 판단","사용감 확인 뒤 본품 탐색"]]},
    {k:"e",L:"E",n:"주말 러너 · 야외활동러",hyp:1,who:"27세 · 직장인 · 건성·민감 · 주말 아침 한강 러닝과 러닝 크루 활동",prods:["daily_sun","cream_mist","intensive_cream"],stat:"가설",sd:"러닝·야외활동 관련 리뷰 근거 없음 · 팝업 입구 질문(주로 하는 활동)으로 비중을 처음 측정한 뒤 타깃 여부 결정",
     j:[["고민","토 07:00","바람·햇빛 속 10km"],["고민 심화","토 09:00","러닝 후 당김·화끈거림"],["성수 팝업","토 13:00","미스트 스테이션 · 선크림 비교"],["제로이드 루틴","다음 러닝","선크림 → 러닝 후 미스트·크림"],["만족","일 08:00","러닝 크루에 공유"],["무신사뷰티","사용 후 판단","러닝 기어와 함께 장바구니"]]}
  ];
  function tex(n){return (window.TEXMAP&&TEXMAP[n])||"tex/"+n}
  var ROT=[-.8,.6,-.5,.9,-.7], TAPES=["tape0","tape1","tape2","tape3","tape0"], cur=-1;
  function esc(t){return String(t).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
  P.forEach(function(p,i){
    var b=document.createElement("button");
    b.type="button";b.className="ptab"+(p.hyp?" hyp":"");b.id="ptab-"+p.k;b.setAttribute("role","tab");
    b.setAttribute("aria-controls","ppanel");b.setAttribute("aria-selected","false");b.tabIndex=-1;
    b.style.left=(i*318)+"px";
    b.innerHTML='<span class="lt">'+p.L+'</span><span class="nm">'+esc(p.n.split(" · ")[0])+(p.hyp?'<small>확장 가설</small>':'<small>'+esc(p.who.split(" · ")[0])+'</small>')+'</span>';
    b.addEventListener("click",function(){show(i,true)});
    b.addEventListener("keydown",function(e){
      var d={ArrowRight:1,ArrowLeft:-1}[e.key], j=e.key==="Home"?0:e.key==="End"?P.length-1:d!=null?(i+d+P.length)%P.length:-1;
      if(j<0)return; e.preventDefault(); e.stopPropagation(); show(j,true); tabs.children[j].focus();
    });
    tabs.appendChild(b);
  });
  function card(p,i){
    var el=document.createElement("article"); el.className="pcard"; el.id="ppanel"; el.setAttribute("role","tabpanel");
    el.setAttribute("aria-labelledby","ptab-"+p.k); el.style.setProperty("--r",ROT[i]+"deg"); el.style.transform="rotate("+ROT[i]+"deg)";
    var tr=(i%2?7:-9)+"deg";
    el.innerHTML='<img class="bgp" src="'+tex("t_card_"+p.k+".png")+'" alt="">'+
      '<img class="tp" src="'+tex(TAPES[i]+".png")+'" alt="" style="left:'+(240+i*40)+'px;--tr:'+tr+';transform:rotate('+tr+')">'+
      '<div class="in"'+(p.hyp?' style="outline:4px dashed var(--ink);outline-offset:-18px"':'')+'>'+
        '<div style="display:flex;flex-direction:column;gap:14px;min-width:0">'+
          '<div style="display:flex;gap:20px;align-items:center"><b class="big" style="font-size:200px;line-height:.8;'+(p.hyp?'color:var(--ink)':'')+'">'+p.L+'</b>'+
          '<div><b class="kor" style="display:block;font-size:46px;line-height:1.1">'+esc(p.n)+'</b>'+(p.hyp?'<span style="display:inline-block;margin-top:8px;font-size:19px;font-weight:900;border:2px dashed var(--ink);padding:2px 10px">확장 가설</span>':'')+'</div></div>'+
          '<p style="font-size:21px;color:#55555a;line-height:1.45">'+esc(p.who)+'</p>'+
          '<div class="pprod">'+p.prods.map(function(k){return '<img src="'+tex("w_"+k+".png")+'" alt="">'}).join("")+'</div></div>'+
        '<div style="display:flex;flex-direction:column;gap:20px;min-width:0">'+
          '<div class="pj">'+p.j.map(function(s){return '<div'+(s[0]==="성수 팝업"?' class="pop"':'')+'><small>'+esc(s[0])+' · '+esc(s[1])+'</small><b>'+esc(s[2])+'</b></div>'}).join("")+'</div>'+
          '<div style="margin-top:auto;display:flex;gap:22px;align-items:baseline;border-top:4px solid var(--ink);padding-top:16px">'+
            '<b class="'+(p.hyp?'kor':'big')+'" style="font-size:'+(p.hyp?'80px':'120px')+';flex:none;'+(p.hyp?'':'')+'">'+esc(p.stat)+'</b>'+
            '<p style="font-size:22px;line-height:1.45;font-weight:500">'+esc(p.sd)+'</p></div></div></div>';
    return el;
  }
  function show(i,anim){
    if(i===cur)return;
    [].forEach.call(tabs.children,function(t,j){t.setAttribute("aria-selected",j===i?"true":"false");t.tabIndex=j===i?0:-1});
    var old=stack.querySelector(".pcard:last-child"), el=card(P[i],i);
    if(old){old.removeAttribute("id");old.removeAttribute("role");old.setAttribute("aria-hidden","true");}
    var reduce=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
    if(anim&&!reduce){ if(old)old.classList.add("under"); el.classList.add("drop"); }
    stack.appendChild(el);
    [].slice.call(stack.children).forEach(function(c){ if(c!==el&&c!==old)c.remove(); });
    if(old)setTimeout(function(){ if(old.parentNode)old.remove(); }, anim&&!reduce?480:0);
    cur=i;
  }
  show(0,false);
})();

var REDUCE=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
function fmt(n,d){return Number(n).toLocaleString("ko-KR",{minimumFractionDigits:d||0,maximumFractionDigits:d||0})}
function countUp(el,to,dec,from){
  var tok=(el._cu||0)+1; el._cu=tok;
  if(REDUCE){el.textContent=fmt(to,dec);return}
  var t0=Date.now(),f=from||0;
  (function step(){ if(el._cu!==tok)return; var k=Math.min(1,(Date.now()-t0)/560);k=1-Math.pow(1-k,3);
    el.textContent=fmt(f+(to-f)*k,dec); if(k<1)setTimeout(step,16); })();
}

// ===== ① 화면에 들어올 때 한 번만: 랜섬 조각 붙이기 · 카운트업 · 형광펜 =====
(function(){
  if(REDUCE||!("IntersectionObserver" in window))return;
  var rs=[].slice.call(document.querySelectorAll(".ransom")), hs=[].slice.call(document.querySelectorAll(".hl")), cs=[].slice.call(document.querySelectorAll("[data-count]"));
  rs.forEach(function(r){[].forEach.call(r.children,function(sp,i){var tf=sp.style.transform||"none";sp.style.setProperty("--fin",tf);sp.style.setProperty("--rr",(i%2?14:-12)+"deg");sp.style.animationDelay=(i*55)+"ms"});r.classList.add("wait")});
  hs.forEach(function(h){h.classList.add("wait")});
  var io=new IntersectionObserver(function(es){es.forEach(function(e){
    if(!e.isIntersecting)return; io.unobserve(e.target); var el=e.target;
    if(el.classList.contains("ransom")){el.classList.add("go");el.classList.remove("wait")}
    else if(el.classList.contains("hl")){el.classList.add("go");requestAnimationFrame(function(){el.classList.remove("wait")})}
    else countUp(el,+el.dataset.count,+(el.dataset.dec||0));
  })},{threshold:.6});
  rs.concat(hs,cs).forEach(function(x){io.observe(x)});
})();

// ===== ③ 존 카드: 누르면 뒤집기(키보드 Enter/Space는 button 기본 동작) =====
document.querySelectorAll(".zflip").forEach(function(b){
  b.addEventListener("click",function(){b.setAttribute("aria-pressed",b.getAttribute("aria-pressed")==="true"?"false":"true")});
});

// ===== ④ 입점 시뮬레이션: 도장 토글 =====
(function(){
  var ctrl=document.querySelector(".sim-ctrl"); if(!ctrl)return;
  var SC={low:{t:"보수안",vis:5000,cv:10,on:40,rp:20},base:{t:"기준안",vis:7000,cv:15,on:50,rp:30},high:{t:"확장안",vis:9000,cv:20,on:60,rp:35}};
  var st={s:"base",both:true}, prev={rev:3675,buy:1050,onl:525,rep:158};
  function $(id){return document.getElementById(id)}
  function stamp(txt){
    var sl=$("slam"),sh=$("kSheet"); $("slamT").textContent=txt;
    if(REDUCE){sl.classList.add("on");return}
    sl.classList.remove("on");void sl.offsetWidth;sl.classList.add("on");
    sh.classList.remove("thud");void sh.offsetWidth;sh.classList.add("thud");
  }
  function apply(){
    var v=SC[st.s], buy=v.vis*v.cv/100, onl=buy*v.on/100, rep=onl*v.rp/100, rev=Math.round(buy*35000/10000);
    countUp($("kRev"),rev,0,prev.rev); countUp($("kBuy"),buy,0,prev.buy);
    $("kRevD").textContent="방문 "+fmt(v.vis)+" × 전환 "+v.cv+"% × 35,000원";
    $("fVis").textContent=fmt(v.vis); $("fBuy").textContent=fmt(buy); $("bBuy").style.width=v.cv+"%";
    if(st.both){
      $("kOnl").classList.remove("na");$("kRep").classList.remove("na");
      countUp($("kOnl"),onl,0,prev.onl); countUp($("kRep"),rep,0,prev.rep);
      $("kOnlU").textContent="명";$("kRepU").textContent="명";
      $("kOnlD").textContent="현장 구매자 중 "+v.on+"%"; $("kRepD").textContent="첫 온라인 구매자 중 "+v.rp+"%";
      $("fOnl").textContent=fmt(onl); $("fRep").textContent=fmt(rep);
      $("bOnl").style.width=(v.cv*v.on/100)+"%"; $("bRep").style.width=(v.cv*v.on*v.rp/10000)+"%"; $("bRep").style.minWidth="6px";
    }else{
      $("kOnl")._cu=($("kOnl")._cu||0)+1;$("kRep")._cu=($("kRep")._cu||0)+1;$("kOnl").textContent="–";$("kRep").textContent="–";$("kOnl").classList.add("na");$("kRep").classList.add("na");
      $("kOnlU").textContent="";$("kRepU").textContent="";
      $("kOnlD").textContent="측정 불가 · 온라인 판매 없음"; $("kRepD").textContent="측정 불가 · 주문 이력 없음";
      $("fOnl").textContent="–"; $("fRep").textContent="–"; $("bOnl").style.width="0%"; $("bRep").style.width="0%"; $("bRep").style.minWidth="0";
    }
    $("fTag").textContent=(st.both?"팝업 + 온라인 동시 · ":"팝업만 · ")+v.t.replace("안","");
    prev={rev:rev,buy:buy,onl:st.both?onl:0,rep:st.both?rep:0};
  }
  ctrl.querySelectorAll(".st-btn").forEach(function(b,i,all){
    b.addEventListener("click",function(){
      if(st.s===b.dataset.s)return; st.s=b.dataset.s;
      all.forEach(function(x){x.setAttribute("aria-checked",x===b?"true":"false");x.tabIndex=x===b?0:-1});
      apply(); stamp(st.both?SC[st.s].t:"팝업만");
    });
    b.tabIndex=b.getAttribute("aria-checked")==="true"?0:-1;
    b.addEventListener("keydown",function(e){var d={ArrowRight:1,ArrowLeft:-1}[e.key];if(!d)return;e.preventDefault();e.stopPropagation();var n=all[(i+d+all.length)%all.length];n.focus();n.click()});
  });
  $("modeBtn").addEventListener("click",function(){
    st.both=!st.both; this.setAttribute("aria-pressed",st.both?"true":"false"); this.querySelector(".mk").textContent=st.both?"ON":"OFF";
    apply(); stamp(st.both?"동시 운영":"측정 불가");
  });
})();
"""
rep("</script>\n</body>", JS + "\n</script>\n</body>")
out = D / "proposal-zine-interactive.html"
out.write_text(s, encoding="utf-8")
print("ok", round(out.stat().st_size / 1024), "KB")

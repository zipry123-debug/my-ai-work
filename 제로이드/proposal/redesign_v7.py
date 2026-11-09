"""무드 리디자인(v7): ① 히어로 콜라주 ② 페르소나 탭(A~D + E 러닝족 가설) ③ 효능 인포그래픽(카운트업·MLE 도식)
④ 팝업 존 구성도(클릭 상세) ⑤ 기대효과 대시보드(시나리오 슬라이더). 근거 섹션은 뒤쪽 부록(접기)으로."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
p = D / "index.html"
shutil.copy2(p, D / "index_before_v7.html")
s = p.read_text(encoding="utf-8")


def cut(start, end):
    """start 표식부터 end 표식 직전까지 잘라 돌려준다."""
    a = s.index(start)
    b = s.index(end, a)
    return s[a:b]


def sub1(block, old, new):
    assert block.count(old) == 1, (block.count(old), old[:70])
    return block.replace(old, new)


# ---------- 기존 블록 추출 ----------
WHY = cut("<!-- WHY -->", "<!-- STRENGTH -->")
STRENGTH = cut("<!-- STRENGTH -->", "<!-- DATA -->")
DATA = cut("<!-- DATA -->", "<!-- PERSONA -->")
PERSONA = cut("<!-- PERSONA -->", "<!-- POPUP -->")
POPUP = cut("<!-- POPUP -->", "<!-- RISK -->")
RISK = cut("<!-- RISK -->", "<!-- NEXT -->")
NEXT = cut("<!-- NEXT -->", "<!-- QA -->")
QA = cut("<!-- QA -->", "<!-- ONE PAGE -->")
ONE = cut("<!-- ONE PAGE -->", "<footer>")

# ---------- ① 히어로 ----------
HERO = """<header class="hero">
  <div class="hero-copy">
    <div class="meta"><span>입점 제안서 · 무신사뷰티 성수 팝업스토어</span><span>2026. 10</span><span>제로이드 영업 MD</span></div>
    <span class="kicker">ZEROID BARRIER FIT · SEONGSU</span>
    <h1>옷은 핏으로,<br>크림은 <em>장벽</em>으로<br>고릅니다.</h1>
    <p class="sub">무신사 고객이 옷의 핏을 입어 보고 고르듯, 성수 팝업에서 ‘내 장벽에 맞는 크림’을 발라 보고 고르게 하겠습니다.</p>
    <div class="cta"><a class="btn solid" href="#popup">팝업 구성 보기</a><a class="btn" href="#impact">기대효과 보기</a></div>
    <p class="ask"><b>제안</b> ① 성수 팝업·온라인 동시 테스트 &nbsp;② 성과 확인 후 온라인 상시 운영 확대</p>
  </div>
  <div class="collage" aria-hidden="true">
    <figure class="t1"><img src="img/intensive_cream.jpg" alt=""><figcaption>인텐시브 크림</figcaption></figure>
    <div class="t2 blk"><span>2 WEEKS</span><b>성수<br>팝업</b></div>
    <figure class="t3"><img src="img/soothing_cream.jpg" alt=""><figcaption>수딩 크림</figcaption></figure>
    <div class="t4 ring"><b>장벽 핏<br>찾기</b></div>
    <figure class="t5"><img src="img/cream_mist.jpg" alt=""><figcaption>크림 미스트</figcaption></figure>
    <figure class="t6"><img src="img/red_control.jpg" alt=""><figcaption>레드 컨트롤</figcaption></figure>
    <div class="t7 stat"><b>4.9만</b><span>리뷰로 검증</span></div>
    <figure class="t8"><img src="img/daily_sun.jpg" alt=""><figcaption>데일리 선크림</figcaption></figure>
  </div>
  <div class="hero-stats">
    <div><b class="num"><span data-count="1600">1,600</span><small>만 개</small></b><span>누적 판매량 · 2013~2024.03</span></div>
    <div><b class="num"><span data-count="4.9" data-dec="1">4.9</span><small>만 건</small></b><span>올리브영 리뷰 · 17개 제품</span></div>
    <div><b class="num"><span data-count="4.7" data-dec="1">4.7</span><small>점 이상</small></b><span>올리브영 평점 · 17개 제품 전부</span></div>
    <div><b class="num"><span data-count="0">0</span><small>개</small></b><span>무신사 내 제로이드 판매 상품</span></div>
  </div>
</header>
"""
s = re.sub(r'<header class="cover">.*?</header>\n', lambda m: HERO, s, count=1, flags=re.S)

# ---------- ② 페르소나 탭 ----------
P = PERSONA
P = sub1(P, '<b>05</b><span>누가, 언제 쓰나</span>', '<b>01</b><span>누가, 언제 쓰나</span>')
P = sub1(P, '<h2>제로이드가 필요한 4개의 순간</h2>', '<h2>제로이드가 필요한 5개의 순간</h2>')
P = sub1(P, '아래 4명은 리뷰 패턴으로 만든 가상 인물이며,', 'A~D는 리뷰 패턴으로 만든 가상 인물, E는 리뷰 근거가 없는 확장 가설이며,')
TABS = """
  <div class="ptabs" role="tablist" aria-label="페르소나 선택">
    <button role="tab" data-p="pa" class="pa" aria-selected="true"><b>A</b><span>장벽 회복러</span></button>
    <button role="tab" data-p="pb" class="pb" aria-selected="false"><b>B</b><span>마감 주간 트러블러</span></button>
    <button role="tab" data-p="pc" class="pc-" aria-selected="false"><b>C</b><span>메이크업 베이스 민감러</span></button>
    <button role="tab" data-p="pd" class="pe" aria-selected="false"><b>D</b><span>성수 투어러</span></button>
    <button role="tab" data-p="px" class="px" aria-selected="false"><b>E</b><span>주말 러너 <em>가설</em></span></button>
  </div>
"""
P = sub1(P, "\n\n  <!-- A -->", TABS + "\n  <!-- A -->")
PERSONA_E = """
  <!-- E (확장 가설) -->
  <article class="persona px" id="px">
    <div class="p-head">
      <span class="L">E</span>
      <h3>주말 러너 · 야외활동러 <em class="hyp">확장 가설</em></h3>
      <div class="prods"><img src="img/daily_sun.jpg" alt="데일리 선크림"><img src="img/cream_mist.jpg" alt="크림 미스트"><img src="img/intensive_cream.jpg" alt="인텐시브 크림"></div>
      <p class="who">27세 · 직장인 · 건성·민감 · 주말 아침 한강 러닝과 러닝 크루 활동</p>
    </div>
    <div class="journey-wrap">
      <div class="journey">
        <div class="step" data-mood="0"><span class="ic"><svg class="i"><use href="#i-sun"/></svg></span><span class="stage">고민</span><span class="t">토 07:00</span><h4>바람·햇빛 속 10km</h4></div>
        <div class="step" data-mood="-2"><span class="ic"><svg class="i"><use href="#i-flame"/></svg></span><span class="stage">고민 심화</span><span class="t">토 09:00</span><h4>러닝 후 당김·화끈거림</h4></div>
        <div class="step pop" data-mood="1"><span class="ic"><svg class="i"><use href="#i-store"/></svg></span><span class="stage">성수 팝업</span><span class="t">토 13:00</span><h4>미스트 스테이션 · 선크림 비교</h4></div>
        <div class="step sol" data-mood="1"><span class="ic"><svg class="i"><use href="#i-mist"/></svg></span><span class="stage">제로이드 루틴</span><span class="t">다음 러닝</span><h4>선크림 → 러닝 후 미스트·크림</h4></div>
        <div class="step" data-mood="2"><span class="ic"><svg class="i"><use href="#i-heart"/></svg></span><span class="stage">만족</span><span class="t">일 08:00</span><h4>러닝 크루에 공유</h4></div>
        <div class="step online" data-mood="2"><span class="ic"><svg class="i"><use href="#i-cart"/></svg></span><span class="stage">무신사뷰티</span><span class="t">사용 후 판단</span><h4>러닝 기어와 함께 장바구니</h4></div>
      </div>
    </div>
    <div class="voice">
      <div class="why"><b class="num">가설</b><p>러닝·야외활동 관련 리뷰 근거 없음. 팝업 입구 질문(주로 하는 활동)으로 비중을 처음 측정한 뒤 타깃 여부 결정</p></div>
    </div>
  </article>
"""
P = P.rstrip()
assert P.endswith("</section>")
P = P[: -len("</section>")] + PERSONA_E + "</section>\n\n"

# ---------- ③ 효능 인포그래픽 ----------
ST = STRENGTH
ST = sub1(ST, '<b>03</b><span>왜 제로이드인가</span>', '<b>02</b><span>왜 제로이드인가</span>')
for old, val, dec, unit in [("2.5배", "2.5", "1", "배"), ("54%", "54", "0", "%"), ("89.36%", "89.36", "2", "%"), ("111%", "111", "0", "%")]:
    ST = sub1(ST, f'<b class="num">{old}</b>', f'<b class="num"><span data-count="{val}" data-dec="{dec}">{old[:-len(unit)]}</span>{unit}</b>')
MLE = """  <div class="mle">
    <div class="mle-fig" role="img" aria-label="각질층 구조 도식: 장벽이 무너진 상태는 지질 사이에 틈이 있고, 지질 구조가 채워진 상태는 틈이 메워져 있음">
      <div class="wall broken"><span class="cap">장벽이 무너진 피부</span><div class="bricks"><i></i><i></i><i class="gap"></i><i></i><i></i><i class="gap"></i><i></i><i></i><i></i><i class="gap"></i><i></i><i></i></div><span class="arrow out">수분이 빠져나감</span></div>
      <div class="vs">→</div>
      <div class="wall fixed"><span class="cap">지질 구조를 채운 피부</span><div class="bricks"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><span class="arrow in">수분을 머금음</span></div>
    </div>
    <div class="mle-txt"><span class="k">MLE® 장벽 기술</span><h3>각질세포는 벽돌, 지질은 시멘트.<br>제로이드는 <em>시멘트</em>를 닮게 만듭니다.</h3><p>피부 지질과 닮은 구조로 장벽을 채우는 것이 제로이드 전 라인의 출발점입니다. 도식은 이해를 돕기 위한 개념 그림입니다.</p></div>
  </div>
"""
ST = sub1(ST, '  <div class="tech">', MLE + '  <div class="tech">')

# ---------- ④ 팝업 존 구성도 ----------
PO = POPUP
PO = sub1(PO, '<b>06</b><span>어떻게 운영하나</span>', '<b>03</b><span>어떻게 운영하나</span>')
FLOOR = """  <div class="floor-wrap">
    <div class="floor" role="group" aria-label="팝업 공간 구성도, 존을 누르면 상세가 보입니다">
      <button class="fz z0" data-z="0" aria-pressed="true"><span class="zn">0</span><b>배리어 체크</b><em>입구</em></button>
      <button class="fz z1 pa" data-z="1" aria-pressed="false"><span class="zn">1</span><b>배리어 리커버리 라운지</b><em>A</em></button>
      <button class="fz z2 pb" data-z="2" aria-pressed="false"><span class="zn">2</span><b>레드 SOS 바</b><em>B</em></button>
      <button class="fz z3 pc-" data-z="3" aria-pressed="false"><span class="zn">3</span><b>베이스 테스트 미러</b><em>C</em></button>
      <button class="fz z4 pe" data-z="4" aria-pressed="false"><span class="zn">4</span><b>미스트 스테이션</b><em>D · E</em></button>
      <button class="fz z5" data-z="5" aria-pressed="false"><span class="zn">5</span><b>구매 · 온라인 연결</b><em>출구</em></button>
      <div class="photo"><b>포토월</b><span>A~E 루틴</span></div>
      <span class="door in">입구 ↑</span><span class="door out">출구 ↓</span>
    </div>
    <aside class="zpanel" aria-live="polite">
      <span class="zp-n">ZONE 0 · 입구</span>
      <h4 class="zp-t">배리어 체크</h4>
      <p class="zp-d">피부 고민 3문항으로 내 상황에 맞는 체험 1곳을 안내합니다. 진단·측정은 하지 않습니다.</p>
      <dl><dt>대상</dt><dd class="zp-w">모든 방문객</dd><dt>체험 제품</dt><dd class="zp-p">–</dd><dt>머무는 시간</dt><dd class="zp-m">약 4분 (공통 안내)</dd></dl>
    </aside>
  </div>
  <p class="src">개념 배치도 · 약 15평 가정 · 실제 면적·피난 동선 확인 후 확정 · 동선: 입구 → 공통 안내 → 선택 체험 1곳(8분) → 구매·온라인 연결</p>
"""
PO = re.sub(r'  <div class="plan" aria-label="팝업 공간 배치도">.*?\n  </div>\n', lambda m: FLOOR, PO, count=1, flags=re.S)
PO = sub1(PO, '<span>6개 기능의 개념 배치 · 실제 면적·피난 동선 확인 후 확정</span>', '<span>존을 눌러 체험 내용을 확인하세요</span>')
PO = sub1(PO, "<b>A~D 루틴 포토월</b><p>퍼소나 4색 포토월", "<b>A~E 루틴 포토월</b><p>페르소나 5색 포토월")

# ---------- ⑤ 기대효과 대시보드 ----------
NX = NEXT
NX = sub1(NX, '<section id="next">', '<section id="impact">')
NX = sub1(NX, '<b>08</b><span>그래서 뭐가 달라지나</span>', '<b>04</b><span>그래서 뭐가 달라지나</span>')
NX = sub1(NX, '<h2>함께 볼 지표와 다음 단계</h2>', '<h2>입점 기대효과 대시보드</h2>\n    <p class="sub">슬라이더로 가정을 바꾸면 결과가 바로 다시 계산됩니다</p>')
DASH = """  <div class="dash">
    <div class="dash-kpi">
      <div><span>2주 현장 매출</span><b class="k-rev">3,675만 원</b><em>방문 × 구매전환 × 객단가 35,000원</em></div>
      <div><span>현장 구매자</span><b class="k-buy">1,050명</b><em>1인 1건 가정</em></div>
      <div class="hl"><span>첫 온라인 구매자</span><b class="k-onl">525명</b><em>QR 유입 고객 중</em></div>
      <div><span>90일 재구매</span><b class="k-rep">158명</b><em>첫 온라인 구매자 중</em></div>
    </div>
    <div class="dash-body">
      <div class="dash-ctrl">
        <label><span>팝업 방문</span><output class="o-vis">7,000명</output><input type="range" class="r-vis" min="3000" max="12000" step="500" value="7000"></label>
        <label><span>구매 전환</span><output class="o-cv">15%</output><input type="range" class="r-cv" min="5" max="30" step="1" value="15"></label>
        <label><span>온라인 전환</span><output class="o-on">50%</output><input type="range" class="r-on" min="20" max="70" step="5" value="50"></label>
        <label><span>90일 재구매</span><output class="o-rp">30%</output><input type="range" class="r-rp" min="10" max="50" step="5" value="30"></label>
        <button type="button" class="dash-reset">기준 시나리오로</button>
      </div>
      <div class="dash-fun" role="img" aria-label="방문에서 재구매까지 퍼널">
        <div class="df"><span>방문</span><i style="width:100%"></i><b class="f-vis">7,000</b></div>
        <div class="df"><span>현장 구매</span><i class="fb-buy" style="width:15%"></i><b class="f-buy">1,050</b></div>
        <div class="df"><span>첫 온라인 구매</span><i class="fb-onl" style="width:7.5%"></i><b class="f-onl">525</b></div>
        <div class="df hl"><span>90일 재구매</span><i class="fb-rep" style="width:2.25%"></i><b class="f-rep">158</b></div>
      </div>
    </div>
    <p class="src">모든 값은 기획 가정이며 실적이 아닙니다. 기준 시나리오: 방문 7,000명 · 구매전환 15% · 온라인 전환 50% · 재구매 30%. 막대 길이는 방문 대비 비율입니다.</p>
  </div>
"""
NX = re.sub(r'    <div class="rev">.*?</div></div>\n', lambda m: "", NX, count=1, flags=re.S)
NX = sub1(NX, '  <div class="cond-wrap">', DASH + '  <div class="cond-wrap">')
# 정적 퍼널·분기는 대시보드가 대신함
NX = re.sub(r'    <div class="ffun".*?\n    </div>\n    <div class="outcome-branches">.*?\n    </div>\n', lambda m: "", NX, count=1, flags=re.S)
NX = sub1(NX, '<h3>검증 지표: 전환과 재구매를 나눠 측정</h3>', '<h3>검증 방식: 전환과 재구매를 나눠 측정</h3>')

# ---------- 부록 ----------
def apx(block, letter, title, num):
    block = re.sub(r'<div class="sec-no"><b>\d+</b>', f'<div class="sec-no"><b>{letter}</b>', block, count=1)
    return f'  <details class="apx" id="apx-{letter}"><summary><span class="al">부록 {letter}</span><b>{title}</b><i aria-hidden="true">+</i></summary>\n{block}  </details>\n'


APP = ('<!-- APPENDIX -->\n<section id="appendix" class="appendix">\n  <div class="head"><div class="sec-no"><b>+</b><span>근거와 검토</span></div>'
       '<h2>MD 검토용 부록</h2><p class="sub">경쟁 비교·고객 데이터·리스크·예상 질문. 눌러서 펼쳐 보세요.</p></div>\n'
       + apx(WHY, "A", "왜 무신사인가 · 경쟁 크림 비교", 1)
       + apx(DATA, "B", "고객 데이터 · 설문 응답", 2)
       + apx(RISK, "C", "약점과 대응", 3)
       + apx(QA, "D", "MD가 물을 질문 6가지", 4)
       + "</section>\n\n")

# ---------- 본문 재조립 ----------
a = s.index("<!-- SUMMARY -->")
b = s.index("<footer>")
s = s[:a] + P + ST + PO + NX + APP + ONE + s[b:]

# 내비게이션
s = re.sub(r'(<span class="brand">ZEROID × MUSINSA BEAUTY</span>\n).*?(  </div>\n</nav>)',
           lambda m: m.group(1) + '    <a href="#persona">01 페르소나</a>\n    <a href="#strength">02 효능</a>\n    <a href="#popup">03 팝업 구성</a>\n'
                     '    <a href="#impact">04 기대효과</a>\n    <a href="#appendix">부록</a>\n' + m.group(2), s, count=1, flags=re.S)

CSS = open(D / "redesign_v7.css", encoding="utf-8").read()
JS = open(D / "redesign_v7.js", encoding="utf-8").read()
assert s.count("</style>") == 1 and s.count("</script>") == 1
s = s.replace("</style>", CSS + "\n</style>").replace("</script>", JS + "\n</script>")
p.write_text(s, encoding="utf-8")
print("ok", len(s))

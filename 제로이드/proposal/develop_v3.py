"""2차 디벨롭(기획의 정석 적용): 컨셉 한 줄(연결), 4MAT 섹션 라벨, MD 질문에 먼저 답하기(두려움 해소), 한 장 요약(기억자 마무리)."""
import shutil
from pathlib import Path

D = Path(__file__).parent
p = D / "index.html"
shutil.copy2(p, D / "index_before_v3.html")
s = p.read_text(encoding="utf-8")


def replace(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:80])
    s = s.replace(old, new)


# 0) develop_v2가 남긴 07 리스크 카드의 고아 마크업 제거
replace("""    </div>
      <span class="rsrc">향료 무첨가 · 인텐시브 크림 자극도 응답</span>
      <div class="ra"><svg class="i"><use href="#i-shield"/></svg><b>‘향 없는 크림’ = 예민한 날의 장점</b></div>
    </div>
""", "    </div>\n")

# 1) 컨셉 한 줄: 무신사 고객의 '핏' 습관에 장벽을 연결
replace("<h1>장벽부터 세우는 보습,<br>이제 <em>성수</em>에서 만납니다.</h1>",
        "<h1>옷은 핏으로,<br>크림은 <em>장벽</em>으로 고릅니다.</h1>")
replace("민감 피부 장벽 케어 브랜드 제로이드가 무신사뷰티 2030 고객의 ‘정착 크림’이 되겠습니다.",
        "무신사 고객이 옷의 핏을 입어 보고 고르듯, 성수 팝업에서 ‘내 장벽에 맞는 크림’을 발라 보고 고르게 하겠습니다.")

# 2) 4MAT: 섹션 라벨을 MD가 묻는 질문 순서로
for old, new in [("<b>01</b><span>요약</span>", "<b>01</b><span>한눈에</span>"),
                 ("<b>02</b><span>왜 무신사인가</span>", "<b>02</b><span>왜 무신사인가</span>"),
                 ("<b>03</b><span>브랜드 강점</span>", "<b>03</b><span>왜 제로이드인가</span>"),
                 ("<b>04</b><span>고객 데이터</span>", "<b>04</b><span>고객이 말한 근거</span>"),
                 ("<b>05</b><span>퍼소나</span>", "<b>05</b><span>누가, 언제 쓰나</span>"),
                 ("<b>06</b><span>팝업 운영안</span>", "<b>06</b><span>어떻게 운영하나</span>"),
                 ("<b>07</b><span>리스크</span>", "<b>07</b><span>약점은 어떻게 푸나</span>"),
                 ("<b>08</b><span>지표와 다음 단계</span>", "<b>08</b><span>그래서 뭐가 달라지나</span>")]:
    if old != new:
        replace(old, new)

# 3) 09 MD 질문에 먼저 답하기 + 한 장 요약 (08 뒤, footer 앞)
QA = """
<!-- QA -->
<section id="qa">
  <div class="head">
    <div class="sec-no"><b>09</b><span>MD가 물을 질문</span></div>
    <h2>결정 전에 물으실 6가지, 먼저 답합니다</h2>
  </div>
  <div class="qa">
    <div class="q"><span class="qn">Q1</span><h4>같은 네오팜의 아토팜과 겹치지 않나요?</h4><p>아토팜은 유아·가족 보습, 제로이드는 2030 민감 피부의 데일리 장벽 케어입니다. 기술(MLE)은 같아도 <b>고객과 사용 상황이 다릅니다.</b></p></div>
    <div class="q"><span class="qn">Q2</span><h4>올리브영보다 비싸 보이지 않을까요?</h4><p>정가는 같게 두고, 할인 대신 <b>무신사 전용 구성</b>(패키지·파우치)으로 차별합니다. 세일 기간 실구매가는 사전에 함께 점검합니다.</p></div>
    <div class="q"><span class="qn">Q3</span><h4>비용은 누가 부담하나요?</h4><p>BA 4명·샘플 3,000개·파우치 제작은 <b>브랜드 부담</b>으로 제안합니다. 임대·시공·수수료는 견적 후 협의합니다.</p></div>
    <div class="q"><span class="qn">Q4</span><h4>왜 지금인가요?</h4><p>건조가 시작되는 환절기는 리뷰에서 가장 많이 언급된 고민(건조·환절기)과 맞닿습니다. 겨울 전 운영을 희망하며 시기는 협의합니다.</p></div>
    <div class="q"><span class="qn">Q5</span><h4>성과가 안 나오면요?</h4><p>2주 뒤 구매전환·온라인 유입으로 1차 판단하고, 목표에 못 미치면 <b>확대를 보류</b>합니다. 상시 입점을 먼저 요구하지 않습니다.</p></div>
    <div class="q"><span class="qn">Q6</span><h4>무신사뷰티에는 무엇이 남나요?</h4><p>아직 무신사에 없는 장벽 크림 라인, 목표 기준 <b>첫 온라인 구매자 525명·리뷰 260건</b>, 그리고 성수 팝업 콘텐츠입니다.</p></div>
  </div>
  <p class="src">Q4·Q6의 숫자와 시기는 08의 기획 가정을 따릅니다.</p>
</section>

<!-- ONE PAGE -->
<section id="onepage" class="onepage">
  <span class="op-label">한 장 요약 · 이것만 기억해 주세요</span>
  <h2 class="op-title">옷은 핏으로, 크림은 <em>장벽</em>으로 고릅니다.</h2>
  <ol class="op">
    <li><span class="k">왜</span><b>커지는 무신사뷰티,<br>아직 없는 장벽 크림</b><p>거래액 2024년 2배 이상 · 제로이드 무신사 판매 0개</p></li>
    <li><span class="k">무엇을</span><b>4.9만 리뷰로<br>검증된 장벽 크림</b><p>올리브영 17개 제품 평점 4.7 이상</p></li>
    <li><span class="k">어떻게</span><b>성수 2주 팝업 +<br>온라인 동시 운영</b><p>발라 보고 고르는 장벽 핏 체험</p></li>
    <li class="end"><span class="k">달라지는 것</span><b>현장 3,675만 원 ·<br>첫 온라인 구매 525명</b><p>목표 시나리오 · 90일 재구매로 확대 판단</p></li>
  </ol>
</section>

"""
replace("\n\n<footer>", "\n" + QA + "<footer>")
replace('    <a href="#next">08 다음 단계</a>\n',
        '    <a href="#next">08 다음 단계</a>\n    <a href="#qa">09 MD 질문</a>\n')

CSS = """
/* 2차 디벨롭: MD 질문 · 한 장 요약 */
.qa{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--ink)}
.qa .q{padding:22px 22px 24px 0;border-bottom:1px solid var(--line)}
.qa .q+.q{padding-left:22px;border-left:1px solid var(--line)}
.qa .q:nth-child(3n+1){padding-left:0;border-left:0}
.qa .qn{display:inline-block;font-size:12px;font-weight:700;color:var(--barrier);letter-spacing:.04em}
.qa h4{font-size:18px;line-height:1.4;margin:6px 0 10px}
.qa p{font-size:14.5px;line-height:1.7;color:var(--muted);margin:0}
.qa p b{color:var(--ink)}
.onepage{background:var(--barrier-soft);padding:40px 36px 36px;margin-top:72px;border-top:0}
.op-label{font-size:13px;font-weight:700;color:var(--barrier)}
.op-title{font-size:clamp(24px,3vw,34px);margin:10px 0 28px;line-height:1.3}
.op-title em{font-style:normal;color:var(--barrier)}
.op{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(4,1fr);gap:28px}
.op li{position:relative;padding-top:14px;border-top:2px solid var(--ink)}
.op li:not(:last-child)::after{content:"→";position:absolute;right:-22px;top:46px;color:var(--muted);font-size:16px}
.op li.end{border-top-color:var(--barrier)}
.op .k{font-size:12px;font-weight:700;color:var(--muted)}
.op li.end .k,.op li.end b{color:var(--barrier)}
.op b{display:block;font-size:18px;line-height:1.4;margin:8px 0 8px}
.op p{font-size:13.5px;line-height:1.6;color:var(--muted);margin:0}
@media(max-width:900px){.qa{grid-template-columns:1fr 1fr}.qa .q:nth-child(3n+1){padding-left:22px;border-left:1px solid var(--line)}.qa .q:nth-child(2n+1){padding-left:0;border-left:0}
  .op{grid-template-columns:1fr 1fr}.op li:nth-child(2)::after{content:none}}
@media(max-width:560px){.qa{grid-template-columns:1fr}.qa .q,.qa .q+.q{padding-left:0;border-left:0}
  .op{grid-template-columns:1fr}.op li::after{content:none!important}.onepage{padding:28px 20px}}
"""
replace("</style>", CSS + "\n</style>")
p.write_text(s, encoding="utf-8")
print("ok")

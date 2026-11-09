"""온라인 운영 보강(#80~84): 브랜드관 콘텐츠, 검색·랭킹, 기획전·라이브, 재구매 관리를 90일 시점과 함께."""
import shutil
from pathlib import Path

D = Path(__file__).parent
p = D / "index.html"
shutil.copy2(p, D / "index_before_v5.html")
s = p.read_text(encoding="utf-8")


def replace(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:80])
    s = s.replace(old, new)


ONLINE = """플랫폼의 집계 공유가 불가하면 미측정으로 보고합니다.</p>
    <div class="onl">
      <div><span class="ow">개장일부터</span><b>브랜드관 상세</b><p>고민별 루틴 A~D를 상품 묶음으로 구성. 팝업 현장 사진·체험 안내를 상세페이지에 반영</p></div>
      <div><span class="ow">운영 2주</span><b>검색·랭킹 노출</b><p>‘장벽 크림·수분 크림·민감 피부’ 검색에 노출. 광고 상품 이용과 예산은 견적 후 결정</p></div>
      <div><span class="ow">팝업 종료 주</span><b>기획전·라이브</b><p>온라인 런칭 라이브 1회 제안. 환절기·연말 기획전 참여는 무신사 일정에 맞춤</p></div>
      <div><span class="ow">첫 구매 후 90일</span><b>재구매 관리</b><p>사용 기간에 맞춘 재구매 쿠폰. 발송 시점은 용량·사용량 확인 후 확정, 앱 알림 사용 여부는 협의</p></div>
    </div>"""
replace("플랫폼의 집계 공유가 불가하면 미측정으로 보고합니다.</p>", ONLINE)

CSS = """
/* 온라인 운영 4가지 */
.onl{display:grid;grid-template-columns:repeat(4,1fr);margin-top:22px;border-top:1px solid var(--ink)}
.onl>div{padding:16px 18px 18px 0}.onl>div+div{padding-left:18px;border-left:1px solid var(--line)}
.onl .ow{font-size:12px;font-weight:700;color:var(--barrier)}
.onl b{display:block;font-size:17px;margin:6px 0 8px}
.onl p{font-size:13.5px;line-height:1.65;color:var(--muted);margin:0}
@media(max-width:900px){.onl{grid-template-columns:1fr 1fr}.onl>div:nth-child(3){padding-left:0;border-left:0}.onl>div:nth-child(n+3){border-top:1px solid var(--line)}}
@media(max-width:560px){.onl{grid-template-columns:1fr}.onl>div,.onl>div+div{padding-left:0;border-left:0;border-top:1px solid var(--line)}}
"""
replace("</style>", CSS + "\n</style>")
p.write_text(s, encoding="utf-8")
print("ok")

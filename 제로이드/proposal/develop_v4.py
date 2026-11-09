"""남은 MD 지적 처리: 팝업 판매 구성(#51·54·55·56·89), 데이터 한계(#32·33), 퍼소나 가상 표기 복구(#36·46), 문서 마감(#91·92·95)."""
import shutil
from pathlib import Path

D = Path(__file__).parent
p = D / "index.html"
shutil.copy2(p, D / "index_before_v4.html")
s = p.read_text(encoding="utf-8")


def replace(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:80])
    s = s.replace(old, new)


# 1) 06 판매 구성: 검증 정도로 등급을 나누고, 의료기기 라인은 제외
LINEUP = """  <div class="popup-block">
  <div class="subhead"><h3>판매 구성</h3><span>검증된 정도에 따라 역할을 나눔 · 리뷰 수는 올리브영 2026.10.28 기준</span></div>
  <div class="lineup">
    <div class="lu hero"><span class="lt">주력 · 체험·패키지 중심</span><ul><li>인텐시브 크림<em>리뷰 14,336</em></li><li>수딩 크림<em>리뷰 10,452</em></li></ul></div>
    <div class="lu"><span class="lt">루틴 · 고민별 짝 제품</span><ul><li>포밍 클렌저<em>7,617</em></li><li>데일리 선크림<em>2,980</em></li><li>레드 컨트롤 크림<em>1,876</em></li><li>카밍 앰플<em>405</em></li></ul></div>
    <div class="lu"><span class="lt">테스트 · 샘플·증정 위주</span><ul><li>인텐시브 크림 미스트<em>86</em></li><li>인텐시브 크림 마스크<em>202</em></li></ul><p>리뷰가 적어 판매 비중을 낮게 두고 반응만 확인</p></div>
    <div class="lu out"><span class="lt">제외 · 혼동 방지</span><ul><li>의료기기(MD) 라인</li></ul><p>2014년 의료기기 인증 라인. 화장품과 광고·판매 기준이 달라 팝업에서 다루지 않음. 오인트 크림·우레아 10%는 온라인 단계에서 검토</p></div>
  </div>
  </div>
  <div class="popup-block">
  <div class="subhead"><h3>운영 디테일</h3>"""
replace("""  <div class="popup-block">
  <div class="subhead"><h3>운영 디테일</h3>""", LINEUP)

# 2) 04 데이터 한계
replace("반올림·기타 응답으로 합계 차이 가능 · 2026.10.28 수집</p>",
        "반올림·기타 응답으로 합계 차이 가능 · 2026.10.28 수집</p>\n"
        "  <p class=\"limit\"><b>확인하지 못한 것</b>올리브영 리뷰에는 연령 정보가 없고, 무신사 고객과 얼마나 겹치는지도 공개 데이터로는 알 수 없습니다. "
        "팝업 입구 질문에 ‘연령대·주로 쇼핑하는 채널’ 2문항(선택 응답)을 넣어 처음으로 측정합니다.</p>")

# 3) 퍼소나 가상 표기 복구
replace("온라인 입점 이후 2차 확장 대상으로 봅니다.</p>",
        "온라인 입점 이후 2차 확장 대상으로 봅니다. 아래 4명은 리뷰 패턴으로 만든 가상 인물이며, 시간·감정 곡선은 체험 설계용 시나리오입니다.</p>")

# 4) 문서 마감: 제안사 소개, 상표 고지
replace('<p class="contact">㈜네오팜 제로이드 영업 MD · 담당자 ○○○ · 연락처 ○○○-○○○○-○○○○ · 이메일 ○○○@○○○</p>',
        '<p class="contact">㈜네오팜 제로이드 영업 MD · 담당자 ○○○ · 연락처 ○○○-○○○○-○○○○ · 이메일 ○○○@○○○</p>\n'
        '  <p class="about">제로이드: 2011년 디펜사마이드 개발 · 2014년 MD(의료기기) 라인 인증 · 해외 12개국 판매(2020, 공식 홈페이지 브랜드 연혁)</p>')
replace("· 공개 리뷰는 제품 수용성의 참고 자료입니다. 무신사 고객 수요·매출·전환율은 별도 검증 대상입니다.</p>",
        "· 공개 리뷰는 제품 수용성의 참고 자료입니다. 무신사 고객 수요·매출·전환율은 별도 검증 대상입니다.</p>\n"
        "  <p class=\"src\">· 무신사·무신사뷰티 명칭은 제안 대상을 밝히기 위한 표기이며, 로고·상표 사용은 계약 시 승인받습니다.</p>")

CSS = """
/* 남은 MD 지적: 판매 구성 · 데이터 한계 · 인쇄 */
.lineup{display:grid;grid-template-columns:1.1fr 1.2fr 1fr 1fr;border-top:1px solid var(--ink)}
.lu{padding:18px 18px 20px 0}.lu+.lu{padding-left:18px;border-left:1px solid var(--line)}
.lu .lt{display:block;font-size:12.5px;font-weight:700;color:var(--muted);margin-bottom:10px}
.lu.hero .lt{color:var(--barrier)}
.lu ul{list-style:none;padding:0;margin:0}.lu li{display:flex;justify-content:space-between;gap:10px;font-size:15px;font-weight:600;padding:5px 0;border-bottom:1px dashed var(--line)}
.lu li em{font-style:normal;font-weight:400;font-size:13px;color:var(--muted);white-space:nowrap}
.lu.hero li{font-size:17px}.lu.hero li em{color:var(--barrier);font-weight:600}
.lu p{font-size:13px;line-height:1.6;color:var(--muted);margin:10px 0 0}
.lu.out li{color:var(--muted)}
.limit{margin:16px 0 0;padding:12px 16px;background:var(--soft);font-size:13.5px;line-height:1.7;color:var(--muted)}
.limit b{color:var(--ink);margin-right:10px}
footer .about{font-size:13px;color:var(--muted);margin:4px 0 18px}
@media(max-width:900px){.lineup{grid-template-columns:1fr 1fr}.lu:nth-child(3){padding-left:0;border-left:0}.lu:nth-child(n+3){border-top:1px solid var(--line)}}
@media(max-width:560px){.lineup{grid-template-columns:1fr}.lu,.lu+.lu{padding-left:0;border-left:0;border-top:1px solid var(--line)}}
@media print{nav,.notice{display:none!important}body{background:#fff}section{break-inside:auto}
  .card,.rc,.q,.lu,.zone,.bn,.persona,.onepage,.kpi-wrap,.tl-wrap{break-inside:avoid}.onepage{break-before:page}}
"""
replace("</style>", CSS + "\n</style>")
p.write_text(s, encoding="utf-8")
print("ok")


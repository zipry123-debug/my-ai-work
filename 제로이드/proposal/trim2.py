"""분량 줄이기 2차: 큰 블록 삭제 + 퍼소나 여정 압축 + 퍼널 가로화 + 여백 축소 (index_before_trim2.html 백업)."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_trim2.html")
s = f.read_text(encoding="utf-8")


def cut(a_marker, b_marker, include_b=False, label=""):
    global s
    a = s.find(a_marker)
    assert a >= 0, ("start", label)
    b = s.find(b_marker, a + len(a_marker))
    assert b >= 0, ("end", label)
    if include_b:
        b += len(b_marker)
    s = s[:a] + s[b:]
    print("cut", label, b - a)


# 표지 제품 사진 줄
cut('  <div class="shelf" aria-label="주요 제품">', "</header>", label="cover shelf")
# 04 키워드 막대그래프 (charts 블록 전체)
cut('  <div class="charts">', '  <div class="role-head">', label="theme chart")
s = s.replace('<p class="sub">올리브영 구매자 통계(17개 제품 전체) + 리뷰 샘플 3,280건 분석</p>',
              '<p class="sub">올리브영 구매자 설문(제품별 전체 구매자 기준)</p>')
# 05 퍼소나: 리뷰 말풍선, 단계 설명 문장
n0 = len(s)
s = re.sub(r'\n      <div class="bubble">.*?</div>', "", s)
s = re.sub(r'(<div class="step[^"]*"[^>]*>.*?</h4>)<p>[^<]*</p>', r"\1", s)
print("persona trimmed", n0 - len(s))
# 06 히어로 SKU 블록
a = s.find('<div class="subhead"><h3>히어로 SKU</h3>')
a = s.rfind('  <div class="popup-block">', 0, a)
b = s.find("</section>", a)
s = s[:a] + s[b:]
print("cut sku block")
# 08 로드맵
cut('    <ol class="roadmap">', "    </ol>\n", include_b=True, label="roadmap")
# 08 퍼널 → 가로 숫자 한 줄
FUN = '''    <div class="kfun" role="img" aria-label="성과 지표 목표: 방문 7,000명, 체험 4,200명, 구매 1,050건, 온라인 사용 525명, 리뷰 260건, 90일 재구매 160명">
      <div><b>7,000</b><span>방문 · 자가진단</span></div>
      <div><b>4,200</b><span>존 체험 · 60%</span></div>
      <div><b>1,050</b><span>현장 구매 · 15%</span></div>
      <div><b>525</b><span>QR 온라인 사용 · 50%</span></div>
      <div><b>260</b><span>온라인 리뷰 · 50%</span></div>
      <div class="hl"><b>160</b><span>90일 재구매 · 30%</span></div>
    </div>
'''
a = s.find('    <div class="funnel"')
b = s.find("    </div>\n", s.find('<div class="fstep hl"', a)) + len("    </div>\n")
s = s[:a] + FUN + s[b:]
s = s.replace('<span class="pill">목표치는 가정 · 괄호는 앞 단계 대비 전환율</span>',
              '<span class="pill">목표치는 가정 · %는 앞 단계 대비 전환율</span>')
# 마지막 슬로건 섹션 삭제, 담당자는 출처 위로
cut('<section class="close">', "</section>\n", include_b=True, label="close section")
s = s.replace('<footer>\n  <span class="eyebrow src">출처</span>',
              '<footer>\n  <p class="contact">㈜네오팜 제로이드 영업 MD · 담당자 ○○○ · 연락처 ○○○-○○○○-○○○○ · 이메일 ○○○@○○○</p>\n  <span class="eyebrow src">출처</span>')
s = s.replace("<p class=\"src\">· 퍼소나 인물은 리뷰 패턴 기반 가상 인물, 인용문은 실제 리뷰 원문</p>",
              "<p class=\"src\">· 퍼소나 인물은 리뷰 패턴 기반 가상 인물</p>")
# 압축 스타일
CSS = """/* 분량 2차: 여백·크기 축소 */
main > section:not(.close){padding-top:32px;padding-bottom:64px}
.head{margin-bottom:32px;gap:10px}
.sec-no{margin-bottom:12px}
.sec-no b{font-size:clamp(44px,6vw,64px)}
.cover{padding-block:48px 56px}
.pc .top img{max-width:120px}
.persona{margin-top:48px;gap:16px}
.p-head .prods img{width:88px;height:88px}
.curve{height:64px}
.step{padding-block:10px 12px}
.step .mood{display:none}
.voice{grid-template-columns:1fr}
.why{display:flex;align-items:baseline;gap:14px}
.why b{font-size:28px}
.comp{margin-top:48px}
.comp td,.comp th{padding-block:8px}
.cond-wrap,.online-wrap{margin-bottom:40px}
.popup-block + .popup-block{margin-top:48px}
.kfun{display:grid;grid-template-columns:repeat(6,1fr);border-top:1px solid var(--ink)}
.kfun > div{padding:16px 12px 16px 0;display:grid;gap:4px;border-right:1px solid var(--line)}
.kfun > div + div{padding-left:12px}
.kfun > div:last-child{border-right:0}
.kfun b{font-family:var(--display);font-size:26px;font-weight:900;font-variant-numeric:tabular-nums}
.kfun span{font-size:13px;color:var(--muted)}
.kfun .hl b{color:var(--barrier)}
@media (max-width:760px){.kfun{grid-template-columns:repeat(3,1fr)}.kfun > div:nth-child(3){border-right:0}.kfun > div:nth-child(4){padding-left:0}.kfun > div:nth-child(n+4){border-top:1px solid var(--line)}}
.tl-wrap{margin-top:40px}
footer .contact{font-size:14px;margin-bottom:8px}
"""
s = s.replace("</style>", CSS + "</style>", 1)
f.write_text(s, encoding="utf-8")

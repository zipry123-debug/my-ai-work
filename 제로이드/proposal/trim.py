"""분량 줄이기: 중복·저우선 블록 삭제 (실행 전 index_before_trim.html 백업)."""
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_trim.html")
s = f.read_text(encoding="utf-8")


def cut(start_marker, end_marker, keep_end=True, label=""):
    global s
    a = s.find(start_marker)
    assert a >= 0, ("start", label)
    b = s.find(end_marker, a + len(start_marker))
    assert b >= 0, ("end", label)
    if not keep_end:
        b += len(end_marker)
    s = s[:a] + s[b:]
    print("cut", label, b - a, "chars")


def drop_line(prefix, label):
    global s
    a = s.find(prefix)
    assert a >= 0, label
    b = s.find("\n", a) + 1
    ls = s.rfind("\n", 0, a) + 1
    s = s[:ls] + s[b:]
    print("drop", label)


# 01 요약: 한 줄 요약 3개
cut('  <div class="three">', "</section>", label="summary three")
# 04 데이터: 누적 리뷰 수 막대그래프
cut('    <div class="chart" role="img" aria-label="올리브영 상품별 누적 리뷰 수">', '    <div class="chart"', label="review count chart")
# 05 퍼소나 개요 카드
cut('  <div class="pov">', "  </div>\n", keep_end=False, label="persona overview")
# 05 퍼소나별 고민·해결·근거 (4회)
for i in range(4):
    cut('    <div class="facts">', '    <div class="journey-wrap">', label=f"facts {i+1}")
# 06 고객 동선 블록
a = s.find('<div class="subhead"><h3>고객 동선</h3>')
a = s.rfind('  <div class="popup-block">', 0, a)
b = s.find('  <div class="popup-block">', a + 10)
s = s[:a] + s[b:]
print("cut customer flow block")
# 06 운영 디테일 3개 + NFC 출처
drop_line("    <div><span>자가진단 · 쿠폰</span>", "ops 자가진단")
drop_line("    <div><span>수량</span>", "ops 수량")
drop_line("    <div><span>메이크업 협업</span>", "ops 메이크업")
drop_line('  <p class="src" style="margin-top:12px">무뷰페 NFC 운영 사례', "nfc src")
# 08 온라인 카드 3개
drop_line("      <div><span>런칭 노출</span>", "online 런칭 노출")
drop_line("      <div><span>CRM</span>", "online CRM")
drop_line("      <div><span>무뷰페 참여</span>", "online 무뷰페")
s = s.replace("출처: 바이라인네트워크(2026.08.25) · 비즈워치(2026.08.20) 무신사 발표 인용",
              "라이브 수치 출처: 비즈워치(2026.08.20) 무신사 발표 인용")
f.write_text(s, encoding="utf-8")

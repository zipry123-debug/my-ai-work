"""전체 렌더 확인 후 수정: 검정 띠 제목이 찢긴 가장자리에 걸림, 손글씨 동그라미가 글자를 가림, 평면도 아래 빈 공간."""
import re
from pathlib import Path

p = Path(__file__).parent / "proposal-zine.html"
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:60])
    s = s.replace(a, b)


# 띠 제목: 안쪽으로 들이고 조금 작게
s = re.sub(r'(<h2 class="t kor on-ink" style="left:)84px;top:66px;font-size:(\d+)px',
           lambda m: f'{m.group(1)}112px;top:74px;font-size:{int(m.group(2)) - 6}px', s)
rep('<h2 class="t riso-c" style="left:100px;top:108px;', '<h2 class="t riso-c" style="left:130px;top:112px;')
# 클로징 '장벽으로.' 띠
rep('<b class="t kor on-ink" style="left:84px;top:64px;font-size:96px"><span class="riso">장벽</span>으로.</b>',
    '<b class="t kor on-ink" style="left:120px;top:70px;font-size:92px"><span class="riso">장벽</span>으로.</b>')
# 문제 제기: 형광 스티커가 위로 잘림
rep('<div class="pc" style="left:1560px;top:-30px;transform:rotate(9deg)"><img class="bgp" src="tex/p2_fluo.png"',
    '<div class="pc" style="left:1540px;top:10px;transform:rotate(9deg)"><img class="bgp" src="tex/p2_fluo.png"')
# MLE: 랜섬 라벨을 제품 위가 아닌 오른쪽 위로
rep('data-ransom="02 MLE" data-seed="71" style="left:80px;top:770px;', 'data-ransom="02 MLE" data-seed="71" style="left:620px;top:780px;')
# 평면도: 존 칸이 시트 높이를 채우게, 동그라미는 3번 존 바깥 모서리로
rep('<div style="display:grid;grid-template-columns:1fr 1fr 1fr;grid-template-rows:auto auto;gap:14px;margin-top:6px">',
    '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;grid-template-rows:1fr 1fr;gap:16px;margin-top:6px;flex:1">')
rep('<svg class="t" style="left:1180px;top:240px" width="300" height="220" viewBox="0 0 300 220"',
    '<svg class="t" style="left:1530px;top:150px" width="300" height="220" viewBox="0 0 300 220"')
# 일정: 동그라미를 D-DAY 점 둘레로
rep('<svg class="t" style="left:1090px;top:610px" width="230" height="170"', '<svg class="t" style="left:1070px;top:560px" width="230" height="170"')
# 경쟁 비교: 숫자를 가리던 동그라미 삭제, 행 간격 키움
s = re.sub(r'\n  <svg class="t" style="left:1410px;top:440px".*?</svg>', '', s, count=1, flags=re.S)
rep('<div class="in" style="padding:60px 66px 40px;gap:12px">', '<div class="in" style="padding:60px 66px 40px;gap:20px">')
rep('.crow{display:grid;grid-template-columns:520px 1fr 120px 130px;gap:18px;align-items:center;font-size:24px}',
    '.crow{display:grid;grid-template-columns:520px 1fr 120px 130px;gap:18px;align-items:center;font-size:26px}')
p.write_text(s, encoding="utf-8")
print("ok")

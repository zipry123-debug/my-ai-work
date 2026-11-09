"""08 섹션 도식화: 운영 조건 → 아이콘 스펙 타일, 온라인 운영 → 흐름도, 일정 설명 문장 제거."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_sec8.html")
s = f.read_text(encoding="utf-8")

ICONS = '''  <symbol id="i-cal" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16"/><path d="M3 10h18M8 3v4M16 3v4"/></symbol>
  <symbol id="i-tag" viewBox="0 0 24 24"><path d="M3 12V3h9l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.5"/></symbol>
  <symbol id="i-pct" viewBox="0 0 24 24"><path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/></symbol>
  <symbol id="i-box" viewBox="0 0 24 24"><path d="M3 7l9-4 9 4v10l-9 4-9-4z"/><path d="M3 7l9 4 9-4M12 11v10"/></symbol>
  <symbol id="i-qr" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM20 14v7M14 20h3"/></symbol>
  <symbol id="i-live" viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14"/><path d="M10 9l5 3-5 3z"/></symbol>
</svg>'''
s = s.replace("</svg>\n\n<nav", ICONS + "\n\n<nav", 1)
assert "i-live" in s

COND_NEW = '''    <div class="spec">
      <div><svg class="i"><use href="#i-cal"/></svg><b>2주 · 15평</b><span>11~12월 · 일 500명</span></div>
      <div><svg class="i"><use href="#i-tag"/></svg><b>정가 유지</b><span>올리브영과 동일</span></div>
      <div><svg class="i"><use href="#i-gift"/></svg><b><s>63,000</s> 49,000원</b><span>한정 패키지 · 크림+미스트+파우치</span></div>
      <div><svg class="i"><use href="#i-pct"/></svg><b>30%</b><span>무신사 판매 수수료</span></div>
      <div><svg class="i"><use href="#i-box"/></svg><b>BA 4 · 샘플 3,000</b><span>제로이드 부담 · 파우치 1,000 · 쿠폰 50%</span></div>
    </div>
'''
a = s.find('    <div class="cond">')
b = s.find("    </div>\n", s.find("비용 분담", a)) + len("    </div>\n")
assert a > 0 and b > a
s = s[:a] + COND_NEW + s[b:]

FLOW = '''    <ol class="oflow">
      <li><svg class="i"><use href="#i-qr"/></svg><b>QR 쿠폰</b><span>팝업 출구에서 발급</span></li>
      <li><svg class="i"><use href="#i-store"/></svg><b>브랜드관</b><span>고민별 루틴 4종 · 체험 리뷰</span></li>
      <li><svg class="i"><use href="#i-live"/></svg><b>런칭 라이브</b><span>한정 패키지 동시 판매</span></li>
      <li class="end"><svg class="i"><use href="#i-repeat"/></svg><b>90일 재구매</b><span>쿠폰 코드로 추적 · 월 1회 공유</span></li>
    </ol>
    <p class="src">참고: 무뷰페 협업 상품 라이브는 시작 3분 만에 방송 전체 거래액의 30% (비즈워치 2026.08.20, 무신사 발표)</p>
'''
a = s.find('    <div class="ops">', s.find('<h3>온라인 운영 계획</h3>'))
b = s.find("  </div>\n", a)
assert a > 0
s = s[:a] + FLOW + s[b:]

# 일정 카드 설명 문장 제거
seg_a = s.find('<ol class="timeline">')
seg_b = s.find("</ol>", seg_a)
seg = re.sub(r"</h4><p>[^<]*</p>", "</h4>", s[seg_a:seg_b])
s = s[:seg_a] + seg + s[seg_b:]

CSS = """/* 08 도식 */
.spec{display:grid;grid-template-columns:repeat(5,1fr);border-top:1px solid var(--ink)}
.spec > div{padding:18px 14px 18px 0;display:grid;gap:6px;align-content:start;border-right:1px solid var(--line);min-width:0}
.spec > div + div{padding-left:14px}
.spec > div:last-child{border-right:0}
.spec svg.i{width:28px;height:28px;color:var(--barrier)}
.spec b{font-family:var(--display);font-size:20px;font-weight:900;line-height:1.25}
.spec b s{font-size:14px;font-weight:500;color:var(--muted);margin-right:4px}
.spec span{font-size:13px;color:var(--muted);line-height:1.45}
@media (max-width:900px){.spec{grid-template-columns:repeat(3,1fr)}.spec > div:nth-child(3){border-right:0}.spec > div:nth-child(4){padding-left:0}.spec > div:nth-child(n+4){border-top:1px solid var(--line)}}
@media (max-width:520px){.spec{grid-template-columns:1fr 1fr}.spec > div{border-right:0!important;padding-left:0!important;border-top:1px solid var(--line)}}
.oflow{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,1fr);gap:28px;border-top:1px solid var(--ink);padding-top:20px}
.oflow li{position:relative;display:grid;gap:6px;justify-items:start;align-content:start;padding:18px;background:var(--soft);min-width:0}
.oflow li svg.i{width:30px;height:30px;color:var(--barrier)}
.oflow li b{font-family:var(--display);font-size:19px;font-weight:900}
.oflow li span{font-size:13px;color:var(--muted);line-height:1.45}
.oflow li:not(:last-child)::after{content:"→";position:absolute;right:-22px;top:50%;transform:translateY(-50%);font-size:18px;color:var(--muted)}
.oflow li.end{background:var(--barrier);color:var(--on-dark)}
.oflow li.end svg.i,.oflow li.end span{color:var(--on-dark)}
@media (max-width:760px){.oflow{grid-template-columns:1fr 1fr;gap:28px 28px}.oflow li:nth-child(2)::after{display:none}}
@media (max-width:480px){.oflow{grid-template-columns:1fr;gap:26px}.oflow li::after{content:"↓"!important;display:block!important;right:auto;left:50%;top:auto;bottom:-24px;transform:none}.oflow li:last-child::after{display:none!important}}
.online-wrap .src{margin-top:4px}
"""
s = s.replace("</style>", CSS + "</style>", 1)
f.write_text(s, encoding="utf-8")
print("done")

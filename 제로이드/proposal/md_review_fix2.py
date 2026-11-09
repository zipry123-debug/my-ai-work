"""MD 검토 2차 반영: 팝업 한정 패키지·굿즈, 가정 수치, 남성 제외 사유, 담당자 자리표시, 일정 현실화."""
from pathlib import Path

f = Path(__file__).parent / "index.html"
s = f.read_text(encoding="utf-8")

COND = '''  <div class="cond-wrap">
    <div class="kpi-title"><h3>운영 조건</h3><span class="pill">모두 가정치 · 미팅에서 확정</span></div>
    <div class="cond">
      <div><span>팝업</span><b>2주 · 약 15평</b><p>11~12월 건조 시즌 · 일 방문 500명 가정</p></div>
      <div><span>현장 매출</span><b>약 3,700만 원</b><p>방문 7,000명 × 구매 전환 15% × 객단가 35,000원</p></div>
      <div><span>가격 정책</span><b>정가 유지</b><p>올리브영과 같은 정가 · 할인은 팝업 한정 패키지로만</p></div>
      <div><span>팝업 한정 패키지</span><b>49,000원</b><p>인텐시브 크림 + 크림 미스트 (정가 63,000원) + 한정 파우치</p></div>
      <div><span>판매 수수료</span><b>30%</b><p>무신사 판매 수수료율 가정</p></div>
      <div><span>비용 분담</span><b>제로이드</b><p>BA 4명 · 샘플 3,000개 · 파우치 1,000개 · QR 쿠폰 할인 재원 50%</p></div>
    </div>
  </div>

'''

R = [
    # 단독 혜택: 팝업 한정 패키지·굿즈
    ("<ul><li>팝업에서 첫 구매</li><li>온라인 브랜드관에서 재구매</li></ul>",
     "<ul><li>성수 팝업 한정 패키지·굿즈로 첫 구매</li><li>온라인 브랜드관에서 재구매</li></ul>"),
    # 남성 제외 사유
    ('    <a class="pe" href="#pd"><span class="L">D</span><h3>성수 투어러·건조러</h3><span class="when">찬바람 부는 외출</span><p>크림 미스트 · 크림 마스크</p></a>\n  </div>\n',
     '    <a class="pe" href="#pd"><span class="L">D</span><h3>성수 투어러·건조러</h3><span class="when">찬바람 부는 외출</span><p>크림 미스트 · 크림 마스크</p></a>\n  </div>\n'
     '  <p class="src note">남성 고객은 리뷰 샘플 3,280건 중 관련 언급이 2%(가족 구매 포함)로 낮아 1차 타깃에서 제외하고, 온라인 입점 이후 2차 확장 대상으로 봅니다.</p>\n'),
    # 운영 조건(가정) 블록 + 퍼널 수치
    ('  <div class="kpi-wrap">\n', COND + '  <div class="kpi-wrap">\n'),
    ('<span class="pill">목표치는 미팅에서 함께 설정</span>', '<span class="pill">목표치는 가정 · 괄호는 앞 단계 대비 전환율</span>'),
    ('<b>배리어 체크 참여</b><span>참여자 수 · 퍼소나 A~D 분포</span></div><em>방문</em>',
     '<b>방문 · 배리어 체크</b><span>퍼소나 A~D 분포 수집</span></div><em>7,000명</em>'),
    ('<b>퍼소나 존 체험</b><span>존별 체험 수 · 체류 시간</span></div><em>체험</em>',
     '<b>퍼소나 존 체험</b><span>존별 체험 수 · 체류 시간 (60%)</span></div><em>4,200명</em>'),
    ('<b>팝업 현장 구매</b><span>구매 전환율 · 트라이얼 키트 판매량</span></div><em>구매</em>',
     '<b>팝업 현장 구매</b><span>방문 대비 15% · 한정 패키지 판매량</span></div><em>1,050건</em>'),
    ('<b>QR 쿠폰 → 온라인</b><span>쿠폰 발급 대비 무신사뷰티 사용률</span></div><em>전환</em>',
     '<b>QR 쿠폰 → 무신사뷰티 사용</b><span>구매자 대비 50%</span></div><em>525명</em>'),
    ('<b>온라인 리뷰 적립</b><span>리뷰 수 · 평점</span></div><em>리뷰</em>',
     '<b>온라인 리뷰 적립</b><span>온라인 구매자 대비 50%</span></div><em>260건</em>'),
    ('<b>90일 재구매</b><span>무신사뷰티 온라인 재구매율</span></div><em>핵심</em>',
     '<b>90일 온라인 재구매</b><span>온라인 구매자 대비 30%</span></div><em>160명</em>'),
    # 일정 현실화
    ('<span class="pill">일정은 협의 후 확정</span>', '<span class="pill">가정 일정 · 협의 후 확정</span>'),
    ('<span class="when">W1</span>', '<span class="when">D-12주</span>'),
    ('<span class="when">W2</span>', '<span class="when">D-8주</span>'),
    ('<h4>샘플 키트 전달</h4><p>히어로 8종 + 퍼소나 A~D 루틴 카드</p>',
     '<h4>패키지·굿즈 확정</h4><p>한정 패키지 · 파우치 · 루틴 카드 생산</p>'),
    ('<span class="when">W3–4</span>', '<span class="when">D-4주</span>'),
    ('<h4>존 설계 확정</h4><p>6개 존 배치 · 메이크업 브랜드 협업 범위</p>',
     '<h4>시공 · BA 교육</h4><p>6개 존 시공 · 응대 스크립트 교육</p>'),
    ('<span class="when">팝업</span>', '<span class="when">D-day</span>'),
    ('<h4>성수 팝업 운영</h4><p>진단 → 체험 → 구매 → QR 온라인 연결</p>',
     '<h4>성수 팝업 2주 운영</h4><p>진단 → 체험 → 구매 → QR 온라인 연결</p>'),
    ('<span class="when">종료 후</span>', '<span class="when">D+90일</span>'),
    ('<h4>온라인 브랜드관 입점</h4><p>팝업 성과 리뷰 · 90일 재구매 트래킹</p>',
     '<h4>온라인 브랜드관 운영</h4><p>팝업 성과 공유 · 90일 재구매 트래킹</p>'),
    # 담당자 자리표시
    ('  <h2>한 번 맞으면 오래 쓰는 크림.<br>그 첫 만남을 성수에서.</h2>\n</section>',
     '  <h2>한 번 맞으면 오래 쓰는 크림.<br>그 첫 만남을 성수에서.</h2>\n'
     '  <p class="contact">㈜네오팜 제로이드 영업 MD · 담당자 ○○○ · 연락처 ○○○-○○○○-○○○○ · 이메일 ○○○@○○○</p>\n</section>'),
    # 스타일
    (".close{padding-block:96px;",
     ".note{margin-top:14px}\n"
     ".cond-wrap{display:grid;gap:20px;margin-bottom:64px}\n"
     ".cond{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--ink)}\n"
     ".cond > div{padding:18px 20px 18px 0;border-bottom:1px solid var(--line);display:grid;gap:4px;align-content:start}\n"
     ".cond span{font-size:13px;font-weight:500;color:var(--muted)}\n"
     ".cond b{font-family:var(--display);font-size:22px;font-weight:900}\n"
     ".cond p{font-size:14px;color:var(--muted)}\n"
     "@media (max-width:760px){.cond{grid-template-columns:1fr 1fr}}\n"
     "@media (max-width:480px){.cond{grid-template-columns:1fr}}\n"
     ".fstep{grid-template-columns:1fr 110px}\n"
     ".fbar{width:100%}\n"
     ".fstep em{font-family:var(--display);font-size:20px;font-weight:900;color:var(--ink);font-variant-numeric:tabular-nums}\n"
     ".fstep.hl em{color:var(--barrier)}\n"
     "@media (max-width:640px){.fstep{grid-template-columns:1fr 90px}.fstep em{display:block;font-size:17px}}\n"
     ".close .contact{font-size:14px;color:var(--muted)}\n"
     ".close{padding-block:96px;"),
]
for a, b in R:
    n = s.count(a)
    print(f"[{n}] {a[:60]!r}")
    assert n >= 1, a
    s = s.replace(a, b, 1)
f.write_text(s, encoding="utf-8")

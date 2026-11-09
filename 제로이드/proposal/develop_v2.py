from pathlib import Path
import re
import shutil

D = Path(__file__).parent
p = D / 'index.html'
shutil.copy2(p, D / 'index_before_logic_v2.html')
s = p.read_text(encoding='utf-8')
changes = []

def replace(old, new):
    global s
    n = s.count(old)
    if not n:
        raise ValueError('문구를 찾지 못함: ' + old[:100])
    s = s.replace(old, new)
    changes.append((n, old[:65]))

replace('① 무신사뷰티 성수 팝업 입점 &nbsp;② 팝업 이후 무신사뷰티 온라인 브랜드관 입점',
        '① 성수 팝업·온라인 동시 테스트 &nbsp;② 성과 확인 후 온라인 상시 운영 확대')
replace('제로이드의 무신사 첫 입점,<br>그 자체가 단독 런칭입니다',
        '검증된 제품을, 무신사만의 이유로.<br>성수에서 체험하고 온라인에서 검증합니다')
replace('무신사에 아직 없는 검증된 더마', '제품 수요가 확인된 더마 브랜드')
replace('<li>무신사 판매 상품 0개</li><li>피지오겔·일리윤·에스트라·아벤느는 이미 입점</li><li>올리브영 리뷰 4.9만 건으로 수요 검증</li>',
        '<li>올리브영 리뷰 약 4.9만 건: 제품 수용성 참고</li><li>인텐시브·수딩: 보습감 비교 체험의 중심</li><li>무신사 내 신규 수요는 팝업에서 검증</li>')
replace('성수에서 공개하는<br>제로이드 무신사 첫 런칭', '무신사 전용 구성으로<br>첫 구매의 이유 만들기')
replace('<li>팝업에서 첫 공개 + 한정 패키지·굿즈</li><li>이후 온라인 브랜드관에서 재구매</li>',
        '<li>전용 패키지·파우치 디자인 제안</li><li>전용 구성과 판매 기간은 계약 시 확정</li>')
replace(' · 무신사 상품 검색 ‘제로이드’ 결과 및 유사 브랜드 노출(2026.10.29)',
        ' · 공개 채널 정보는 시장 배경 자료이며 무신사 내부 실적·운영 약속과 구분')
# 유사 브랜드 노출만으로 확정했던 입점 여부 열을 제거.
s = re.sub(r'<span>무신사</span>(?=</div>)', '', s)
s = re.sub(r'<span class="cmu(?: no)?">.*?</span>', '', s)
s = s.replace('<th>무신사</th>', '')
s = re.sub(r'<td>(?:<b>)?(?:미입점|입점)(?:</b>)?</td>', '', s)
replace('순함과 평점은 경쟁 크림과 비슷합니다. 차이는 <b>복합성에 맞는 수딩 크림</b>, 보습·트러블·선케어까지 이어지는 <b>라인 루틴</b>, 그리고 <b>무신사 첫 입점</b>입니다.',
        '순함·평점만으로 우위를 주장하지 않습니다. <b>수딩과 인텐시브의 보습감 비교</b>를 첫 체험으로, <b>고민별 루틴과 전용 구성</b>을 구매 이유로 제안합니다.')
replace('‘–’는 해당 설문 문항이 없는 제품 · 무신사 입점 여부는 무신사 브랜드 노출 기준',
        '공개 상품페이지의 응답·리뷰 누적치 비교. 응답자·판매 기간·기획 구성이 달라 효과 우열이나 시장점유율을 뜻하지 않습니다.')
# 시험 원문/조건 없는 수치 대신 제품 역할로 제안.
replace('순한데, 숫자로 증명합니다', '체험할 이유가 분명한 4개 제품')
replace('상세페이지에 공개된 인체적용시험 결과', '공식 제품 설명을 바탕으로 구성한 체험 역할')
replace('<b class="num">2.5배</b><p>1회 사용<br>손상 피부장벽 개선</p>', '<b class="num product-role">집중 보습</b><p>인텐시브 크림<br>건조한 날의 보습감 비교</p>')
replace('<b class="num">54%</b><p>1회 사용<br>피부 민감도 개선</p>', '<b class="num product-role">데일리 보습</b><p>수딩 크림<br>일상 루틴의 사용감 비교</p>')
replace('<b class="num">89.36%</b><p>1주 사용<br>붉은기 진정</p>', '<b class="num product-role">pH4</b><p>레드 컨트롤 크림<br>핌프로브 루틴의 크림 단계</p>')
replace('<b class="num">111%</b><p>1주 사용<br>손상 피부장벽 개선 (사용 전 대비)</p>', '<b class="num product-role">수분 진정</b><p>카밍 앰플<br>핌프로브 루틴의 앰플 단계</p>')
replace('피부 지질을 닮은 구조로 장벽 강화. 전 라인 공통', '브랜드의 장벽 케어 기술 · 적용 여부는 개별 제품 기준')
replace('디펜사마이드(방어력) · 레스토마이드(붉은기 진정)', '디펜사마이드 · 레스토마이드 등 제품별 성분 설명')
replace('10가지 유해성분 무첨가 · 하이포알러제닉 테스트 완료', '테스트·무첨가 항목은 제품별 공식 표기로 안내')
replace('출처: 제로이드 공식 홈페이지 제품 상세페이지 표기(자사 인체적용시험). 시험 개요는 미팅 시 별도 제공.',
        '출처: 제로이드 공식 제품 설명. 개인별 사용감 차이가 있으며, 시험 조건을 확인하지 않은 효능 수치는 본문에서 제외했습니다.')
replace('올리브영 구매자 설문(제품별 전체 구매자 기준)', '올리브영 상품페이지의 설문 참여 응답 비율')
replace('구매자가 고른 효과: 제품마다 역할이 다릅니다', '설문에서 확인한 제품별 기대 역할')
replace('올리브영 구매자 설문 응답(%, 제품별 전체 구매자 기준) · 나머지는 ‘주름/미백’ 응답 · 2026.10.28',
        '설문 참여자 응답(%) · 전체 구매자의 평가를 뜻하지 않음 · 반올림·기타 응답으로 합계 차이 가능 · 2026.10.28 수집')
replace('남성 고객은 리뷰 샘플 3,280건 중 관련 언급이 2%(가족 구매 포함)로 낮아 1차 타깃에서 제외하고, 온라인 입점 이후 2차 확장 대상으로 봅니다.',
        '1차 기획은 장벽·진정·메이크업 전·외출 중 보습의 네 상황에 집중합니다. 성별로 구매를 제한하지 않으며, 연령·직업·감정 곡선은 체험 설계를 위한 가상 시나리오입니다.')
replace('각질 없는 출근 화장', '다음 날 사용감 확인')
replace('<span class="t">4주 뒤</span><h4>크림 다 쓸 때쯤 재구매</h4>', '<span class="t">소진 시점</span><h4>사용량에 맞춰 재구매</h4>')
replace('<span class="t">한 달 뒤</span><h4>다음 마감 전 재구매</h4>', '<span class="t">사용 후 판단</span><h4>맞는 루틴만 재구매</h4>')
replace('<span class="t">한 달 뒤</span><h4>쿠션과 함께 장바구니</h4>', '<span class="t">다음 쇼핑</span><h4>메이크업 구매 때 함께 탐색</h4>')
replace('<span class="t">2주 뒤</span><h4>본품 재구매 + 추천</h4>', '<span class="t">체험 후 판단</span><h4>사용감 확인 뒤 본품 탐색</h4>')
replace('리뷰 샘플 중 ‘트러블·붉은기’ 언급, 2위. 다른 제품 쓰다 돌아오는 고객', '도움순 리뷰 샘플의 관련 키워드 언급 · 재구매율과 구분')
replace('리뷰 샘플 중 ‘산뜻·안 끈적’ 언급. 더마 브랜드가 데일리 베이스로', '도움순 리뷰 샘플의 사용감 언급 · 메이크업 적합성은 체험으로 확인')
replace('리뷰 샘플 중 ‘건조·환절기’ 언급 1위. 굿즈가 첫 구매 계기가 되는 고객', '도움순 리뷰 샘플의 건조 관련 언급 · 굿즈 구매 유도 효과는 미확인')
# 동선은 공간 실측 전 가정. 4분 공통+8분 선택 체험.
replace('입구에서 진단하고, 내 퍼소나 존에서 체험하고, 출구에서 온라인으로 연결', '4분 공통 안내 + 8분 선택 체험 1곳 → 구매·온라인 연결')
replace('6개 존 · 입구에서 출구 순서', '6개 기능의 개념 배치 · 실제 면적·피난 동선 확인 후 확정')
replace('QR 자가진단 → A·B·C·D 루틴 카드 + 앱 쿠폰', '피부 고민 3문항 → 선택 체험 1곳 안내 · 진단·측정 없음')
replace('화장 위 미스트 체험 · 미니 증정', '분사감·손등 사용감 체험 · 샘플은 준비 수량 내 제공')
replace('크림 위 선크림·협업 브랜드 쿠션 밀림 테스트', '크림·선크림 사용감 비교 · 쿠션 협업은 별도 협의')
replace('리뷰 &amp; 굿즈 카운터', '구매 &amp; 온라인 연결')
replace('구매 시 한정 파우치 · QR → 무신사뷰티 온라인 쿠폰', '한정 구성 구매 시 파우치 · QR로 온라인 상품 연결')
replace('<b>시간당 120명</b><p>체험 1회 15분 × 동시 30명. 일 10시간 운영 시 1,200명까지 수용해 목표 500명 대비 여유</p>',
        '<b>목표 시간당 50명</b><p>일 10시간·500명 가정. 방문객 동시 12명 × 시간당 5회 = 이론상 60명. 직원 6명 포함 실측·리허설 후 수용 인원 확정</p>')
replace('존 1~4 BA 각 1명(제로이드) · 입구·출구 카운터 2명(무신사 운영 인력 가정)',
        'BA 4명 + 입출구 2명 배치 가정. 브랜드가 조달 계획·휴게 대체인력·교육안을 마련하고 비용은 계약 전 협의')
replace('<b>테스터 2시간 교체</b><p>일회용 스패출러·코튼 사용 · 존마다 손 소독 · 개봉일 표기</p>',
        '<b>개인별 도구 · 오염 즉시 교체</b><p>일회용 도구 사용·손 소독·개봉일 기록. 매 2시간 위생 점검, 제품 교체 기준은 품질 지침에 맞춰 확정</p>')
replace('<b>무신사 앱 사전 예약</b><p>시간대별 예약 · 현장 대기는 QR 웨이팅 · 회원 적립 연계</p>',
        '<b>30분 슬롯 · 현장 대기</b><p>슬롯당 25명 가정. 앱 연동은 협의하고 불가 시 별도 예약·대기표 운영. 개인정보는 운영 목적에 필요한 항목만 수집</p>')
replace('메가스토어 성수와 같은 결제 시스템 사용 협의 · 현장 구매도 무신사 회원 구매로 집계',
        'POS·정산·취소·회원 식별 범위는 계약 전 확인. 연동 불가 시 현장 결제와 온라인 유입 성과를 분리 집계')
# 07 부적절한 증거 연결 교정.
replace('“세정력이 약해요”', '세정 기대치의 차이')
replace('포밍 클렌저 세정력 응답</span>', '세정력: 만족 50% · 보통 48% · 아쉬움 2% (보통≠불만)</span>')
replace('아침·이중세안용 루틴으로 안내', '메이크업·선크림 사용 여부를 묻고 세안 순서 안내')
start=s.index('      <div class="rbar" role="img" aria-label="인텐시브 크림 자극도 응답:')
end=s.index('    </div>', start)
s=s[:start]+'''      <div class="sensory-flow"><span>원료 향 체험</span><b aria-hidden="true">→</b><span>취향 확인</span></div>
      <span class="rsrc">향 선호에 대한 정량 근거 없음 · 자극도와 구분</span>
      <div class="ra"><svg class="i"><use href="#i-shield"/></svg><b>구매 전에 향을 맡고 선택할 수 있게 안내</b></div>
'''+s[end:]
replace('<div class="rprice"><s>63,000원</s><em>→</em><b>49,000원</b></div>',
        '<div class="rprice"><span>제안 판매가</span><b>49,000원</b></div>')
replace('할인·가성비 언급 9% (리뷰 샘플)', '가격 가정 · 구성·증정 원가를 확인한 뒤 확정')
replace('팝업 한정 패키지 · 재구매는 QR 쿠폰', '한정 구성의 가치를 설명하고 채널 실구매가 점검')
# 08 명확한 분모/브랜칭/손익한계.
replace('<span class="pill">모두 가정치 · 미팅에서 확정</span>', '<span class="pill">아래 숫자는 기획 가정 · 실제 견적·계약 미확정</span>')
replace('<div class="rev"><span>현장 매출 계산</span>', '<div class="rev"><span>기준 시나리오 · 부가세 포함 총매출 가정</span>')
replace('약 3,700만 원', '3,675만 원')
replace('<b>2주 · 15평</b><span>11~12월 · 일 500명</span>', '<b>2주 · 약 15평</b><span>D-12주 준비 · 시기는 별도 확정</span>')
replace('<b>정가 유지</b><span>올리브영과 동일</span>', '<b>실구매가 점검</b><span>동일 용량·쿠폰·증정까지 비교</span>')
replace('<b><s>63,000</s> 49,000원</b><span>한정 패키지 · 크림+미스트+파우치</span>',
        '<b>49,000원 제안</b><span>크림+미스트+파우치 · 원가 확인 전</span>')
replace('<b>30%</b><span>무신사 판매 수수료</span>', '<b>30% 가정</b><span>계약 수수료·정산 기준 미확정</span>')
replace('<b>BA 4 · 샘플 3,000</b><span>제로이드 부담 · 파우치 1,000 · 쿠폰 50%</span>',
        '<b>BA 4 · 샘플 3,000</b><span>브랜드 부담 제안 · 비용 승인 전</span>')
replace('<h3>온라인 운영 계획</h3>', '<h3>온라인 전환: 팝업 개장일부터 연결</h3>')
replace('비용·일정은 가정 · 무신사 데이터 공유는 협의', '플랫폼 기능·데이터 공유는 협의')
replace('<b>QR 쿠폰</b><span>팝업 출구에서 발급</span>', '<b>QR 유입</b><span>전용 링크·쿠폰 코드</span>')
replace('<b>브랜드관</b><span>고민별 루틴 4종 · 체험 리뷰</span>', '<b>온라인 구매</b><span>개장 전 판매·배송 준비</span>')
replace('<b>런칭 라이브</b><span>한정 패키지 동시 판매</span>', '<b>사용 후 확인</b><span>라이브·리뷰는 별도 운영</span>')
replace('<b>90일 재구매</b><span>쿠폰 코드로 추적 · 월 1회 공유</span>', '<b>90일 평가</b><span>동의된 고객군의 재구매 확인</span>')
replace('참고: 무뷰페 협업 상품 라이브는 시작 3분 만에 방송 전체 거래액의 30% (비즈워치 2026.08.20, 무신사 발표)',
        'QR은 유입만 식별합니다. 재구매는 최초 온라인 구매 고객군의 주문 이력으로 측정하며, 플랫폼의 집계 공유가 불가하면 미측정으로 보고합니다.')
start=s.index('  <div class="kpi-wrap">',s.index('<section id="next">'))
end=s.index('  <div class="tl-wrap">',start)
s=s[:start]+'''  <div class="kpi-wrap">
    <div class="kpi-title"><h3>검증 지표: 전환과 재구매를 나눠 측정</h3><span class="pill">목표 시나리오 · 실적 아님</span></div>
    <div class="ffun" role="img" aria-label="가정: 방문 7000명, 체험 4200명, 현장 구매자 1050명, 최초 온라인 구매자 525명">
      <div class="frow"><span class="fl">팝업 방문<em>중복 입장 제외</em></span><span class="fb"><i style="width:100%"></i></span><b>7,000명</b></div>
      <div class="frow"><span class="fl">선택 체험<em>방문자의 60%</em></span><span class="fb"><i style="width:60%"></i></span><b>4,200명</b></div>
      <div class="frow"><span class="fl">현장 구매자<em>체험자의 25% · 방문자의 15%</em></span><span class="fb"><i style="width:15%"></i></span><b>1,050명</b></div>
      <div class="frow hl"><span class="fl">최초 온라인 구매자<em>현장 구매자 중 50% 가정</em></span><span class="fb"><i style="width:7.5%"></i></span><b>525명</b></div>
    </div>
    <div class="outcome-branches">
      <div><span>525명에서 별도로 집계 ↙</span><b>리뷰 260건</b><p>525명 대비 약 49.5% · 선택 행동</p></div>
      <div><span>별도 집계 ↘</span><b>再구매 약 158명</b><p>525명 중 90일 내 2회 이상 구매 · 30% 가정</p></div>
    </div>
    <p class="src">현장 1인 1건 구매 가정. 온라인 첫 구매일부터 90일 관찰하며 리뷰 작성 여부와 관계없이 재구매를 집계합니다.</p>
    <div class="decision-gate"><b>확대 판단</b><p>현장 구매전환·온라인 유입은 2주 운영 후 평가. 재구매는 고객별 90일 관찰 완료 후 평가하고, 비용·반품을 반영한 수익성 확인 뒤 확대를 결정합니다.</p></div>
  </div>

'''+s[end:]
replace('<h4>킥오프 미팅</h4>', '<h4>조건·예산·KPI 합의</h4>')
replace('<h4>시공 · BA 교육</h4>', '<h4>리허설·온라인 판매 준비</h4>')
replace('<h4>성수 팝업 2주 운영</h4>', '<h4>팝업·온라인 동시 운영</h4>')
replace('<span class="when">D+90일</span>', '<span class="when">고객별 90일</span>')
replace('<h4>온라인 브랜드관 운영</h4>', '<h4>재구매 평가·확대 결정</h4>')
# 확정한 비용처럼 쓰지 않기. 숫자를 늘리지 않고 손익 경계 한 줄.
needle='  </div>\n\n  <div class="online-wrap">'
idx=s.index(needle,s.index('<section id="next">'))
s=s[:idx]+s[idx:].replace(needle,'''    <p class="src">매출은 이익이 아닙니다. 원가·수수료·임대·시공·인건비·증정·할인·반품을 포함한 견적 후 손익을 확정합니다. 패키지 판매 비중은 객단가 35,000원 가정과 함께 검증합니다.</p>
  </div>

  <div class="online-wrap">''',1)
# 기존 잘못된 닫힘 div 제거.
s=s.replace('  </div>\n  </div>\n\n  <div class="kpi-wrap">', '  </div>\n\n  <div class="kpi-wrap">')
replace('· 퍼소나 인물은 리뷰 패턴 기반 가상 인물', '· 공개 리뷰는 제품 수용성의 참고 자료입니다. 무신사 고객 수요·매출·전환율은 별도 검증 대상입니다.')
replace('숫자로 보는 제로이드', '제품 근거에서 출발해, 채널 성과를 검증합니다')
css='''
/* 2차 논리 보강: 기존의 차분한 블루와 간결한 구성 유지 */
.product-role{font-size:clamp(21px,2.4vw,32px)!important;letter-spacing:-.05em}
.cchart .crow{grid-template-columns:minmax(170px,1.3fr) minmax(130px,1fr) minmax(180px,1.2fr) 60px}
.comp .cchart{overflow-x:auto}.sensory-flow{display:flex;gap:12px;align-items:center;min-height:40px;background:var(--soft);padding:10px 12px;font-size:15px}
.outcome-branches{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:14px 0 6px 0;padding:18px 0;border-top:1px solid var(--line)}
.outcome-branches>div{border-left:2px solid var(--barrier);padding-left:16px}.outcome-branches span{font-size:12px;color:var(--muted)}
.outcome-branches b{display:block;font-size:23px;color:var(--barrier);margin-top:6px}.outcome-branches p{font-size:13px;color:var(--muted);margin:4px 0}
.decision-gate{display:flex;align-items:baseline;gap:18px;padding:16px 18px;background:var(--barrier-soft);margin-top:18px}
.decision-gate>b{white-space:nowrap;color:var(--barrier)}.decision-gate p{font-size:14px;margin:0;line-height:1.7}
@media(max-width:760px){.cchart .crow{grid-template-columns:minmax(140px,1fr) minmax(110px,1fr);gap:8px}.cchart .crow .cm{display:none}.cchart .crow .stack,.cchart .crow .na,.cchart .crow .lg{grid-column:1/-1}.decision-gate{display:block}.decision-gate>b{display:block;margin-bottom:8px}}
@media(max-width:480px){.outcome-branches{grid-template-columns:1fr}.outcome-branches b{font-size:21px}}
'''
s=s.replace('</style>',css+'\n</style>',1).replace('再구매','재구매')
p.write_text(s,encoding='utf-8')
print('반영한 문구 교체',len(changes),'항목')
print('현장매출',7000*.15*35000,'체험→현장',1050/4200,'재구매목표',round(525*.3))

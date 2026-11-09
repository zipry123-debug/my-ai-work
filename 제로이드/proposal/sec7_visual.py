"""07 리스크 도식화: 고객의 말(근거 막대) → 우리의 답 카드 3장."""
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_sec7.html")
s = f.read_text(encoding="utf-8")

NEW = '''  <div class="rcards">
    <div class="rc">
      <div class="rq"><svg class="i"><use href="#i-alert"/></svg><strong>“세정력이 약해요”</strong></div>
      <div class="rbar" role="img" aria-label="포밍 클렌저 세정력 응답: 아주 만족 50%, 보통 48%, 다소 아쉬워요 2%">
        <i class="g" style="flex:50" title="아주 만족해요 50%">만족 50%</i><i class="m" style="flex:48" title="보통이에요 48%">보통 48%</i><i class="b" style="flex:2" title="다소 아쉬워요 2%"></i>
      </div>
      <span class="rsrc">포밍 클렌저 세정력 응답</span>
      <div class="ra"><svg class="i"><use href="#i-shield"/></svg><b>아침·이중세안용 루틴으로 안내</b></div>
    </div>
    <div class="rc">
      <div class="rq"><svg class="i"><use href="#i-alert"/></svg><strong>“향이 별로예요”</strong></div>
      <div class="rbar" role="img" aria-label="인텐시브 크림 자극도 응답: 자극 없이 순해요 75%, 보통 24%, 자극 1%">
        <i class="g" style="flex:75" title="자극없이 순해요 75%">순해요 75%</i><i class="m" style="flex:24" title="보통이에요 24%">24%</i><i class="b" style="flex:1" title="자극이 느껴져요 1%"></i>
      </div>
      <span class="rsrc">향료 무첨가 · 인텐시브 크림 자극도 응답</span>
      <div class="ra"><svg class="i"><use href="#i-shield"/></svg><b>‘향 없는 크림’ = 예민한 날의 장점</b></div>
    </div>
    <div class="rc">
      <div class="rq"><svg class="i"><use href="#i-alert"/></svg><strong>“가격만 조금 더 착하면”</strong></div>
      <div class="rprice"><s>63,000원</s><em>→</em><b>49,000원</b></div>
      <span class="rsrc">할인·가성비 언급 9% (리뷰 샘플)</span>
      <div class="ra"><svg class="i"><use href="#i-shield"/></svg><b>팝업 한정 패키지 · 재구매는 QR 쿠폰</b></div>
    </div>
  </div>
'''
a = s.find('  <div class="risks">')
b = s.find("</section>", a)
assert a > 0
s = s[:a] + NEW + s[b:]

CSS = """/* 07 도식 */
.rcards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;border-top:1px solid var(--ink);padding-top:20px}
.rc{display:grid;gap:12px;align-content:start;min-width:0}
.rq{display:flex;align-items:center;gap:10px}
.rq svg.i{color:var(--muted);width:22px;height:22px}
.rq strong{font-family:var(--display);font-size:19px;font-weight:900}
.rbar{display:flex;gap:2px;height:26px}
.rbar i{display:flex;align-items:center;padding-left:8px;font-style:normal;font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;min-width:3px}
.rbar i:first-child{border-radius:4px 0 0 4px}.rbar i:last-child{border-radius:0 4px 4px 0}
.rbar .g{background:var(--barrier);color:var(--on-dark)}
.rbar .m{background:var(--bar-other);color:var(--ink)}
.rbar .b{background:var(--line)}
.rprice{display:flex;align-items:center;gap:10px;height:26px}
.rprice s{font-size:15px;color:var(--muted)}
.rprice em{font-style:normal;color:var(--muted)}
.rprice b{font-family:var(--display);font-size:22px;font-weight:900;color:var(--barrier)}
.rsrc{font-size:12px;color:var(--muted)}
.ra{display:flex;align-items:center;gap:10px;padding:14px 16px;background:var(--barrier-soft)}
.ra svg.i{color:var(--barrier);width:22px;height:22px;flex:none}
.ra b{font-size:15px;font-weight:700;color:var(--barrier);line-height:1.4}
@media (max-width:760px){.rcards{grid-template-columns:1fr;gap:28px}}
"""
s = s.replace("</style>", CSS + "</style>", 1)
f.write_text(s, encoding="utf-8")
print("done")

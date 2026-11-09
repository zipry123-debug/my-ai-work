"""한 장 요약 임팩트 강화: 코발트 풀 밴드 + 숫자 4개로 이어지는 이야기(0개 → 4.9만 → 2주 → 525명) + 제안 한 줄."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
p = D / "index.html"
shutil.copy2(p, D / "index_before_v6.html")
s = p.read_text(encoding="utf-8")

NEW = """<!-- ONE PAGE -->
<section id="onepage" class="finale">
  <span class="fn-label">한 장 요약 · 이것만 기억해 주세요</span>
  <h2 class="fn-title">옷은 핏으로,<br>크림은 <em>장벽</em>으로 고릅니다.</h2>
  <ol class="fn-steps">
    <li><span class="k">왜</span><b class="big">0<small>개</small></b><p>거래액 2배 성장한 무신사뷰티에<br>제로이드 판매 상품은 아직 0개</p></li>
    <li><span class="k">무엇을</span><b class="big">4.9<small>만 건</small></b><p>리뷰로 이미 검증된<br>장벽 크림을</p></li>
    <li><span class="k">어떻게</span><b class="big">2<small>주</small></b><p>성수 팝업에서 발라 보고 고르고,<br>온라인에서 바로 산다</p></li>
    <li class="end"><span class="k">그래서</span><b class="big">525<small>명</small></b><p>첫 온라인 구매 고객<br>현장 매출 3,675만 원 (목표)</p></li>
  </ol>
  <div class="fn-ask"><span>제안</span><b>① 성수 팝업·온라인 동시 테스트</b><i>→</i><b>② 성과 확인 후 온라인 상시 운영 확대</b></div>
  <p class="fn-note">숫자는 08의 기획 가정 · 무신사 거래액은 2024년 기준(02 출처)</p>
</section>
"""
s, n = re.subn(r"<!-- ONE PAGE -->\n<section id=\"onepage\".*?</section>\n", NEW, s, flags=re.S)
assert n == 1, n

CSS = """
/* 한 장 요약: 피날레 밴드 (라이트·다크 공통 고정색) */
.finale{background:#1f3a8a;color:#fff;margin:80px 0 0;padding:64px 48px 44px;border-top:0!important;position:relative;overflow:hidden}
.finale::before{content:"";position:absolute;right:-120px;top:-120px;width:420px;height:420px;border-radius:50%;border:2px solid rgba(255,255,255,.12)}
.fn-label{font-size:13px;font-weight:700;letter-spacing:.04em;color:#b9c9f5}
.fn-title{font-size:clamp(34px,5.4vw,68px);line-height:1.12;letter-spacing:-.04em;margin:14px 0 48px;color:#fff;font-weight:900}
.fn-title em{font-style:normal;color:#9fb8ff}
.fn-steps{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-top:1px solid rgba(255,255,255,.35)}
.fn-steps li{padding:22px 22px 26px 0;position:relative}
.fn-steps li+li{padding-left:22px;border-left:1px solid rgba(255,255,255,.18)}
.fn-steps .k{font-size:13px;font-weight:700;color:#b9c9f5}
.fn-steps .big{display:block;font-size:clamp(44px,5.6vw,76px);font-weight:900;letter-spacing:-.04em;line-height:1;margin:14px 0 14px;color:#fff;font-variant-numeric:tabular-nums}
.fn-steps .big small{font-size:.32em;font-weight:700;margin-left:4px;letter-spacing:0}
.fn-steps p{font-size:14px;line-height:1.6;color:#d6e0fb;margin:0}
.fn-steps li.end{background:#fff;color:#1f3a8a;padding-left:22px;border-left:0}
.fn-steps li.end .k{color:#3557b8}.fn-steps li.end .big{color:#1f3a8a}.fn-steps li.end p{color:#3d4b70}
.fn-ask{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;margin-top:36px;padding:18px 22px;border:1.5px solid rgba(255,255,255,.55);font-size:17px}
.fn-ask span{font-size:13px;font-weight:700;color:#1f3a8a;background:#fff;padding:3px 10px}
.fn-ask b{font-weight:700;color:#fff}.fn-ask i{font-style:normal;color:#9fb8ff}
.fn-note{font-size:12px;color:#b9c9f5;margin:14px 0 0}
@media(max-width:900px){.finale{padding:48px 28px 36px}.fn-steps{grid-template-columns:1fr 1fr}
  .fn-steps li:nth-child(3){padding-left:0;border-left:0}.fn-steps li:nth-child(n+3){border-top:1px solid rgba(255,255,255,.18)}
  .fn-steps li.end{padding-left:22px}}
@media(max-width:560px){.finale{padding:40px 20px 30px}.fn-steps{grid-template-columns:1fr}
  .fn-steps li,.fn-steps li+li{padding-left:0;border-left:0;border-top:1px solid rgba(255,255,255,.18)}
  .fn-steps li.end{padding-left:18px}.fn-ask{font-size:15px}}
@media print{.finale{break-before:page;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""
assert s.count("</style>") == 1
s = s.replace("</style>", CSS + "\n</style>")
p.write_text(s, encoding="utf-8")
print("ok")

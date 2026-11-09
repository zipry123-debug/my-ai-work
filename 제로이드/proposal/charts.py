"""도표화: 02 경쟁 비교(리뷰 수 막대 + 피부타입 누적 막대), 08 퍼널(실제 비율), 08 현장 매출 계산식. 팔레트는 validate_palette로 검사한 값."""
from pathlib import Path

f = Path(__file__).parent / "index.html"
s = f.read_text(encoding="utf-8")

ROWS = [  # 이름, 리뷰 수, (건성, 복합성, 지성) or None, 순함, 무신사, 제로이드 여부
    ("일리윤 세라마이드 아토 집중크림", 38553, None, "–", "입점", False),
    ("피지오겔 DMT 페이셜 크림", 23347, (54, 43, 4), "76%", "입점", False),
    ("제로이드 인텐시브 크림", 14350, (47, 46, 7), "75%", "미입점", True),
    ("제로이드 수딩 크림", 10476, (26, 57, 17), "75%", "미입점", True),
    ("아벤느 시칼파트 플러스 크림", 9945, (41, 51, 8), "70%", "입점", False),
    ("에스트라 아토베리어365 크림", 8780, (55, 40, 5), "79%", "입점", False),
    ("아토팜 MLE 크림 (같은 네오팜)", 1379, None, "–", "입점", False),
]
MAX = 38553
SK = ["건성", "복합성", "지성"]


def row(name, n, skin, mild, mus, me):
    w = n / MAX * 100
    if skin:
        segs = "".join(
            f'<i class="sk{k+1}" style="flex:{v}" title="{name} · {SK[k]}에 좋아요 {v}%">{f"{v}%" if v >= 15 else ""}</i>'
            for k, v in enumerate(skin))
        skin_html = f'<span class="stack">{segs}</span>'
    else:
        skin_html = '<span class="na">피부타입 설문 없음</span>'
    return (f'      <div class="crow{" me" if me else ""}">'
            f'<span class="cn">{name}</span>'
            f'<span class="cbar"><i style="width:{w:.1f}%" title="{name} · 올리브영 리뷰 {n:,}건"></i><b>{n:,}</b></span>'
            f'{skin_html}'
            f'<span class="cm">{mild}</span>'
            f'<span class="cmu{" no" if mus == "미입점" else ""}">{mus}</span></div>\n')


CHART = ('    <div class="cchart" role="img" aria-label="경쟁 장벽 크림 7종의 올리브영 리뷰 수와 피부타입 응답 비교">\n'
         '      <div class="crow ch"><span>제품</span><span>올리브영 리뷰 수</span>'
         '<span class="lg"><em><i class="sk1"></i>건성</em><em><i class="sk2"></i>복합성</em><em><i class="sk3"></i>지성</em></span>'
         '<span class="cm">순해요</span><span>무신사</span></div>\n'
         + "".join(row(*r) for r in ROWS) + "    </div>\n")

# 기존 표는 '표로 보기'로 접어서 유지
a = s.find('    <div class="comp-scroll">')
b = s.find("    </div>\n", s.find("</table>", a)) + len("    </div>\n")
assert a > 0 and b > a
table = s[a:b].replace('<div class="comp-scroll">', '<details class="tview"><summary>표로 보기</summary><div class="comp-scroll">', 1)
table = table[: table.rstrip().rfind("</div>")] + "</div></details>\n"
s = s[:a] + CHART + table + s[b:]

# 08 퍼널: 실제 비율 막대
FUN = [("방문 · 자가진단", 7000, "", "명"), ("퍼소나 존 체험", 4200, "60%", "명"), ("팝업 현장 구매", 1050, "15%", "건"),
       ("QR → 무신사뷰티 사용", 525, "50%", "명"), ("온라인 리뷰", 260, "50%", "건"), ("90일 재구매", 160, "30%", "명")]
rows = "".join(
    f'      <div class="frow{" hl" if i == len(FUN) - 1 else ""}"><span class="fl">{lab}{f"<em>앞 단계의 {cv}</em>" if cv else ""}</span>'
    f'<span class="fb"><i style="width:{v/7000*100:.2f}%" title="{lab} {v:,}{u}"></i></span><b>{v:,}{u}</b></div>\n'
    for i, (lab, v, cv, u) in enumerate(FUN))
FUNNEL = ('    <div class="ffun" role="img" aria-label="성과 지표 퍼널: 방문 7,000명에서 90일 재구매 160명까지">\n' + rows + "    </div>\n")
a = s.find('    <div class="kfun"')
b = s.find("    </div>\n", a) + len("    </div>\n")
assert a > 0
s = s[:a] + FUNNEL + s[b:]
s = s.replace('<span class="pill">목표치는 가정 · %는 앞 단계 대비 전환율</span>',
              '<span class="pill">목표치는 가정 · 막대 길이는 방문 7,000명 대비 실제 비율</span>')

# 08 현장 매출: 계산식
old = '<div><span>현장 매출</span><b>약 3,700만 원</b><p>방문 7,000명 × 구매 전환 15% × 객단가 35,000원</p></div>'
assert old in s
s = s.replace(old, "")
EQ = ('    <div class="rev"><span>현장 매출 계산</span><div class="eqn">'
      '<i><b>7,000명</b>방문</i><em>×</em><i><b>15%</b>구매 전환</i><em>×</em><i><b>35,000원</b>객단가</i>'
      '<em>=</em><i class="res"><b>약 3,700만 원</b>2주 현장 매출</i></div></div>\n')
a = s.find('    <div class="cond">')
s = s[:a] + EQ + s[a:]

CSS = """/* 도표 */
:root{--skin1:#1b2a6b;--skin2:#3d63d6;--skin3:#86a8f5;--bar-other:#c9ced8}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--skin1:#c3d0ff;--skin2:#7d9bff;--skin3:#3a58b8;--bar-other:#3a3f4a}}
:root[data-theme="dark"]{--skin1:#c3d0ff;--skin2:#7d9bff;--skin3:#3a58b8;--bar-other:#3a3f4a}
.cchart{display:grid;border-top:1px solid var(--ink)}
.crow{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1.3fr) minmax(0,1.6fr) 56px 64px;gap:16px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line);font-size:14px}
.crow.ch{font-size:12px;font-weight:500;color:var(--muted);padding:10px 0}
.crow .cn{font-weight:500}
.crow.me .cn{color:var(--barrier);font-weight:700}
.cbar{display:flex;align-items:center;gap:8px;min-width:0}
.cbar i{display:block;height:14px;background:var(--bar-other);border-radius:0 4px 4px 0;min-width:3px}
.crow.me .cbar i{background:var(--barrier)}
.cbar b{font-size:13px;font-variant-numeric:tabular-nums;white-space:nowrap}
.stack{display:flex;gap:2px;height:22px}
.stack i{display:flex;align-items:center;justify-content:center;font-style:normal;font-size:11px;font-weight:700;min-width:4px}
.sk1{background:var(--skin1);color:var(--bg)}
.sk2{background:var(--skin2);color:#fff}
.sk3{background:var(--skin3);color:var(--ink)}
.stack i:first-child{border-radius:4px 0 0 4px}.stack i:last-child{border-radius:0 4px 4px 0}
.na{font-size:12px;color:var(--muted)}
.crow .cm{text-align:right;font-variant-numeric:tabular-nums}
.cmu{font-size:13px;color:var(--muted)}
.cmu.no{color:var(--barrier);font-weight:700}
.lg{display:flex;gap:10px;flex-wrap:wrap}
.lg em{font-style:normal;display:flex;align-items:center;gap:4px}
.lg i{display:inline-block;width:10px;height:10px;border-radius:2px}
.tview{margin-top:8px}
.tview summary{cursor:pointer;font-size:13px;color:var(--muted)}
@media (max-width:760px){.crow{grid-template-columns:minmax(0,1fr) minmax(0,1fr);row-gap:6px}.crow .cn{grid-column:1/-1}.crow .cm,.crow .cmu{text-align:left}.crow.ch .cn{display:none}}
.ffun{display:grid;gap:10px;border-top:1px solid var(--ink);padding-top:16px}
.frow{display:grid;grid-template-columns:200px minmax(0,1fr) 90px;gap:14px;align-items:center}
.fl{font-size:14px;font-weight:500;display:grid}
.fl em{font-style:normal;font-size:12px;font-weight:400;color:var(--muted)}
.fb{height:18px;background:var(--soft);border-radius:0 4px 4px 0}
.fb i{display:block;height:100%;background:var(--bar-other);border-radius:0 4px 4px 0;min-width:3px}
.frow b{font-family:var(--display);font-size:18px;font-weight:900;text-align:right;font-variant-numeric:tabular-nums}
.frow.hl .fb i{background:var(--barrier)}
.frow.hl b,.frow.hl .fl{color:var(--barrier)}
@media (max-width:640px){.frow{grid-template-columns:minmax(0,1fr) 80px}.fb{grid-column:1/-1;grid-row:2}}
.rev{display:grid;gap:10px;margin-bottom:8px}
.rev > span{font-size:13px;font-weight:500;color:var(--muted)}
.eqn{display:flex;flex-wrap:wrap;align-items:stretch;gap:8px}
.eqn i{font-style:normal;display:grid;gap:2px;padding:12px 16px;background:var(--soft);font-size:12px;color:var(--muted);min-width:0}
.eqn i b{font-family:var(--display);font-size:20px;font-weight:900;color:var(--ink)}
.eqn em{font-style:normal;align-self:center;font-size:20px;color:var(--muted)}
.eqn i.res{background:var(--barrier);color:var(--on-dark)}
.eqn i.res b{color:var(--on-dark)}
"""
s = s.replace("</style>", CSS + "</style>", 1)

# 보습·진정 팔레트 교체 (검사 통과 값)
s = s.replace("--moist:#1b2a6b; --calm:#7fb0ff;", "--moist:#2a46b0; --calm:#7fb0ff;")
n = s.count("--moist:#dbe3ff;--calm:#4f86f0;")
s = s.replace("--moist:#dbe3ff;--calm:#4f86f0;", "--moist:#6f8cf2;--calm:#3b5cc4;")
print("dark moist/calm replaced", n)
f.write_text(s, encoding="utf-8")
print("ok")

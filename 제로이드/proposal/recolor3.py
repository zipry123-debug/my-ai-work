"""무신사 톤 + 포인트 1색(오렌지레드): 순수 무채색 + #E8461F, 퍼소나·차트는 같은 색의 밝기 단계 (validateOrdinal 통과 값)."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_recolor3.html")
s = f.read_text(encoding="utf-8")

LIGHT = {
    "bg": "#ffffff", "ink": "#111111", "muted": "#6b6b6b", "line": "#e6e6e6", "soft": "#f2f2f2",
    "barrier": "#e8461f", "barrier-soft": "#ffece6",
    "pa": "#7a1f0c", "pa-soft": "#f6e6e2", "pb": "#c63a1a", "pb-soft": "#fbe7e1",
    "pc": "#ff5a36", "pc-soft": "#ffece6", "pe": "#ff9b80", "pe-soft": "#fff3ef",
    "moist": "#e8461f", "calm": "#ff9b80", "numeral": "#111111", "on-dark": "#ffffff",
}
DARK = {
    "bg": "#121212", "ink": "#f2f2f2", "muted": "#a3a3a3", "line": "#2c2c2c", "soft": "#1c1c1c",
    "barrier": "#ff7a56", "barrier-soft": "#2a1813",
    "pa": "#ffc2b2", "pa-soft": "#2a1813", "pb": "#ff8a6b", "pb-soft": "#2a1813",
    "pc": "#e8502c", "pc-soft": "#2a1813", "pe": "#a8371b", "pe-soft": "#2a1813",
    "moist": "#ffc2b2", "calm": "#e8502c", "numeral": "#f2f2f2", "on-dark": "#121212",
}
SKIN_L = {"skin1": "#b8341a", "skin2": "#ff5a36", "skin3": "#ff9b80", "bar-other": "#d6d6d6"}
SKIN_D = {"skin1": "#ffc2b2", "skin2": "#ff7a56", "skin3": "#c4401e", "bar-other": "#3a3a3a"}


def set_tokens(block, vals):
    for k, v in vals.items():
        block, n = re.subn(rf"(--{re.escape(k)}:)\s*#[0-9a-fA-F]{{3,6}}", rf"\g<1>{v}", block)
    return block


# 1) 첫 :root{...} (밝은 화면)
a = s.find(":root{")
b = s.find("}", a)
s = s[:a] + set_tokens(s[a:b], LIGHT) + s[b:]
# 2) 다크 블록 두 곳 (첫 번째 @media 블록, :root[data-theme="dark"]{ 블록)
a = s.find("@media (prefers-color-scheme: dark){")
b = s.find("}\n}", a)
s = s[:a] + set_tokens(s[a:b], DARK) + s[b:]
a = s.find(':root[data-theme="dark"]{')
b = s.find("}", a)
s = s[:a] + set_tokens(s[a:b], DARK) + s[b:]
# 3) 차트 토큰 (skin, bar-other) 세 줄
lines = s.split("\n")
for i, ln in enumerate(lines):
    if "--skin1:" in ln:
        lines[i] = set_tokens(ln, SKIN_D if "dark" in ln else SKIN_L)
s = "\n".join(lines)
# 주석 갱신
s = s.replace("/* 강조: 딥 틸 / 민트 */", "/* 포인트: 오렌지레드 */")
for old, new in [("슬레이트 블루", "포인트 단계 1"), ("/* B 트러블: 로즈 */", "/* B 트러블: 포인트 단계 2 */"),
                 ("/* C 메이크업: 오커 */", "/* C 메이크업: 포인트 단계 3 */"), ("/* D 건조·휴대: 라벤더 */", "/* D 건조·휴대: 포인트 단계 4 */"),
                 ("보습(소프트 블루) / 진정(샌드)", "보습(포인트) / 진정(연한 포인트)")]:
    s = s.replace(old, new)
f.write_text(s, encoding="utf-8")
for tok in ["--barrier:#e8461f", "--barrier:#ff7a56", "--skin1:#b8341a", "--skin1:#ffc2b2", "--pa:#7a1f0c", "--pa:#ffc2b2", "--bg:#121212"]:
    print(tok, s.count(tok))

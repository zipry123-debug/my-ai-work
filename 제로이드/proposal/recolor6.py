"""포인트 색을 코발트 블루로. 퍼소나·차트는 블루 밝기 단계."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_recolor6.html")
s = f.read_text(encoding="utf-8")

LIGHT = {
    "barrier": "#3557b8", "barrier-soft": "#eaeffa",
    "pa": "#1c327a", "pa-soft": "#e6ebf6", "pb": "#3557b8", "pb-soft": "#eaeffa",
    "pc": "#5675cc", "pc-soft": "#edf1fb", "pe": "#7891d6", "pe-soft": "#f1f4fc",
    "moist": "#3557b8", "calm": "#a2b4e4",
}
DARK = {
    "barrier": "#8ea6ea", "barrier-soft": "#161d33",
    "pa": "#c6d3f5", "pa-soft": "#161d33", "pb": "#8ea6ea", "pb-soft": "#161d33",
    "pc": "#5b78cf", "pc-soft": "#161d33", "pe": "#3f5aa6", "pe-soft": "#161d33",
    "moist": "#c6d3f5", "calm": "#5675cc",
}
SKIN_L = {"skin1": "#24408f", "skin2": "#5675cc", "skin3": "#a2b4e4", "bar-other": "#dddddd"}
SKIN_D = {"skin1": "#c6d3f5", "skin2": "#8ea6ea", "skin3": "#4a66bb", "bar-other": "#333333"}


def set_tokens(block, vals):
    for k, v in vals.items():
        block = re.sub(rf"(--{re.escape(k)}:)\s*#[0-9a-fA-F]{{3,6}}", rf"\g<1>{v}", block)
    return block


a = s.find(":root{"); b = s.find("}", a)
s = s[:a] + set_tokens(s[a:b], LIGHT) + s[b:]
a = s.find("@media (prefers-color-scheme: dark){"); b = s.find("}\n}", a)
s = s[:a] + set_tokens(s[a:b], DARK) + s[b:]
a = s.find(':root[data-theme="dark"]{'); b = s.find("}", a)
s = s[:a] + set_tokens(s[a:b], DARK) + s[b:]
lines = s.split("\n")
for i, ln in enumerate(lines):
    if "--skin1:" in ln:
        lines[i] = set_tokens(ln, SKIN_D if "dark" in ln else SKIN_L)
s = "\n".join(lines)
s = s.replace("/* 포인트: 차분한 블루 */", "/* 포인트: 코발트 블루 */")
f.write_text(s, encoding="utf-8")
for tok in ["--barrier:#3557b8", "--barrier:#8ea6ea", "--skin1:#24408f", "--skin1:#c6d3f5", "--pa:#1c327a", "--pa:#c6d3f5", "#3b5b8c"]:
    print(tok, s.count(tok))



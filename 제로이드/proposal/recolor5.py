"""포인트 색을 차분한 블루로. 퍼소나·차트는 블루 밝기 단계."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_recolor5.html")
s = f.read_text(encoding="utf-8")

LIGHT = {
    "barrier": "#3b5b8c", "barrier-soft": "#eaf0f7",
    "pa": "#1f3557", "pa-soft": "#e6ecf4", "pb": "#3b5b8c", "pb-soft": "#eaf0f7",
    "pc": "#5a7aaa", "pc-soft": "#edf2f8", "pe": "#7894bd", "pe-soft": "#f1f5fa",
    "moist": "#3b5b8c", "calm": "#a3b8d6",
}
DARK = {
    "barrier": "#8fabd6", "barrier-soft": "#18202c",
    "pa": "#c9d7ec", "pa-soft": "#18202c", "pb": "#8fabd6", "pb-soft": "#18202c",
    "pc": "#5f7fb0", "pc-soft": "#18202c", "pe": "#47618c", "pe-soft": "#18202c",
    "moist": "#c9d7ec", "calm": "#5878a8",
}
SKIN_L = {"skin1": "#2a4470", "skin2": "#5c7cab", "skin3": "#a3b8d6", "bar-other": "#dddddd"}
SKIN_D = {"skin1": "#c9d7ec", "skin2": "#8fabd6", "skin3": "#4f6d9c", "bar-other": "#333333"}


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
s = s.replace("/* 포인트: 회색 */", "/* 포인트: 차분한 블루 */")
f.write_text(s, encoding="utf-8")
for tok in ["--barrier:#3b5b8c", "--barrier:#8fabd6", "--skin1:#2a4470", "--skin1:#c9d7ec", "--pa:#1f3557", "--pa:#c9d7ec", "#555555"]:
    print(tok, s.count(tok))


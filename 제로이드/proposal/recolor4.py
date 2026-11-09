"""포인트 색을 회색으로: 전체 무채색. 퍼소나·차트는 회색 밝기 단계."""
import re
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_recolor4.html")
s = f.read_text(encoding="utf-8")

LIGHT = {
    "barrier": "#555555", "barrier-soft": "#efefef",
    "pa": "#222222", "pa-soft": "#ececec", "pb": "#555555", "pb-soft": "#efefef",
    "pc": "#888888", "pc-soft": "#f2f2f2", "pe": "#b8b8b8", "pe-soft": "#f6f6f6",
    "moist": "#444444", "calm": "#b0b0b0",
}
DARK = {
    "barrier": "#bdbdbd", "barrier-soft": "#262626",
    "pa": "#eeeeee", "pa-soft": "#262626", "pb": "#b5b5b5", "pb-soft": "#262626",
    "pc": "#7d7d7d", "pc-soft": "#262626", "pe": "#525252", "pe-soft": "#262626",
    "moist": "#e0e0e0", "calm": "#6e6e6e",
}
SKIN_L = {"skin1": "#333333", "skin2": "#777777", "skin3": "#b5b5b5", "bar-other": "#dddddd"}
SKIN_D = {"skin1": "#e6e6e6", "skin2": "#a3a3a3", "skin3": "#606060", "bar-other": "#333333"}


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
s = s.replace("/* 포인트: 오렌지레드 */", "/* 포인트: 회색 */")
f.write_text(s, encoding="utf-8")
for tok in ["--barrier:#555555", "--barrier:#bdbdbd", "--skin1:#333333", "--skin1:#e6e6e6", "--pa:#222222", "--pa:#eeeeee", "#e8461f", "#ff7a56"]:
    print(tok, s.count(tok))

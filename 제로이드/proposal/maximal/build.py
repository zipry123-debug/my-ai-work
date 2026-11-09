"""slides.html의 cut/·img/ 이미지를 data URI로 넣어 더블클릭으로 바로 여는 단일 HTML을 만든다."""
import base64
import re
from pathlib import Path

D = Path(__file__).parent
s = (D / "slides.html").read_text(encoding="utf-8")
cache = {}


def inline(m):
    p = m.group(1)
    if p not in cache:
        mime = "image/png" if p.endswith(".png") else "image/jpeg"
        cache[p] = f"data:{mime};base64," + base64.b64encode((D / p).read_bytes()).decode()
    return f'src="{cache[p]}"'


out = re.sub(r'src="((?:cut|img)/[^"]+)"', inline, s)
(D / "ZEROID_maximal_deck.html").write_text(out, encoding="utf-8")
art = re.sub(r"<!doctype html>\s*<html[^>]*>\s*<head>\s*", "", out, flags=re.I)
art = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>\s*', "", art)
art = re.sub(r"</head>\s*<body>\s*", "", art)
art = re.sub(r"\s*</body>\s*</html>\s*$", "\n", art)
(D / "artifact.html").write_text(art, encoding="utf-8")
print(len(cache), "images", round(len(out) / 1024), "KB")

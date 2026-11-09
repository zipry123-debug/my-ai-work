"""proposal-zine.html의 tex/ 이미지를 WebP로 줄여 data URI로 넣고, 폴더 없이 하나로 열리는 HTML을 만든다."""
import base64
import io
import re
from pathlib import Path

from PIL import Image

D = Path(__file__).parent
import sys
name = sys.argv[1] if len(sys.argv) > 1 else "proposal-zine"
s = (D / f"{name}.html").read_text(encoding="utf-8")
cache = {}


def uri(path):
    if path not in cache:
        im = Image.open(D / path)
        buf = io.BytesIO()
        if im.mode == "RGBA":
            im.save(buf, "WEBP", quality=62, method=6)
            mime = "image/webp"
        else:
            im.convert("RGB").save(buf, "JPEG", quality=78, optimize=True); mime = "image/jpeg"
        cache[path] = f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()
    return cache[path]


s = re.sub(r'src="(tex/[^"]+)"', lambda m: f'src="{uri(m.group(1))}"', s)
s = re.sub(r'url\((tex/[^)]+)\)', lambda m: f'url({uri(m.group(1))})', s)
# JS가 이름을 조합해 쓰는 조각(카드·제품·테이프)은 TEXMAP으로 넘김
dyn = sorted({f.name for f in (D / "tex").glob("*.png") if re.match(r"(t_card_|w_|tape)", f.name)}) if "TEXMAP" in s else []
if dyn:
    import json
    m = json.dumps({n: uri("tex/" + n) for n in dyn})
    s = s.replace("<script>document.documentElement.classList", f"<script>window.TEXMAP={m}</script>\n<script>document.documentElement.classList", 1)
assert not re.search(r'(src="|url\()tex/', s)
out = D / f"{name}_single.html"
out.write_text(s, encoding="utf-8")
art = re.sub(r"<!doctype html>\s*<html[^>]*>\s*<head>\s*", "", s, flags=re.I)
art = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>\s*', "", art)
art = re.sub(r"</head>\s*<body>\s*", "", art)
art = re.sub(r"\s*</body>\s*</html>\s*$", "\n", art)
art = art.replace('<html lang="ko" class="no-js">', "")
(D / f"{name}_artifact.html").write_text(art, encoding="utf-8")
print(len(cache), "images", round(out.stat().st_size / 1048576, 1), "MB")

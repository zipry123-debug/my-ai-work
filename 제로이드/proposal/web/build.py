"""web/index.html의 img/*.jpg(../img)를 data URI로 넣어 바로 여는 단일 HTML과 아티팩트용 파일을 만든다."""
import base64, re
from pathlib import Path

D = Path(__file__).parent
src = (D / "index.html").read_text(encoding="utf-8")
cache = {}


def inline(m):
    p = m.group(1)
    if p not in cache:
        cache[p] = "data:image/jpeg;base64," + base64.b64encode((D.parent / p).read_bytes()).decode()
    return m.group(0).replace(p, cache[p])


out = re.sub(r'"(img/[a-z_]+\.jpg)"', inline, src)
dst = D.parent / "제로이드_무신사뷰티_웹제안서.html"
dst.write_text(out, encoding="utf-8")
print(dst.name, round(len(out) / 1024), "KB", len(cache), "images")

art = re.sub(r"<!doctype html>\s*<html[^>]*>\s*<head>\s*", "", out, flags=re.I)
art = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>\s*', "", art)
art = re.sub(r"</head>\s*<body>\s*", "", art)
art = re.sub(r"\s*</body>\s*</html>\s*$", "\n", art)
(D / "artifact.html").write_text(art, encoding="utf-8")
print("artifact.html", round(len(art) / 1024), "KB")

"""proposal/img 제품 사진의 흰 배경을 테두리에서부터 지워(누끼) 여백 없이 잘라 PNG로 저장한다."""
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

D = Path(__file__).parent
SRC = D.parent / "img"
OUT = D / "cut"
OUT.mkdir(exist_ok=True)
TOL = 5  # 255에서 이만큼까지 배경으로 본다


def cut(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    bg = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.extend([(x, 0), (x, h - 1)])
    for y in range(h):
        q.extend([(0, y), (w - 1, y)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or bg[y][x]:
            continue
        r, g, b = px[x, y]
        if min(r, g, b) < 255 - TOL:
            continue
        bg[y][x] = True
        q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    # 흰 제품 몸통으로 배경이 새어 들어간 곳을 막기: 행·열마다 제품의 양 끝 사이를 모두 제품으로 채운다
    fg = [[not bg[y][x] for x in range(w)] for y in range(h)]
    for y in range(h):
        xs = [x for x in range(w) if fg[y][x]]
        if len(xs) > 1:
            for x in range(xs[0], xs[-1] + 1):
                fg[y][x] = True
    for x in range(w):
        ys = [y for y in range(h) if fg[y][x]]
        if len(ys) > 1:
            for y in range(ys[0], ys[-1] + 1):
                fg[y][x] = True
    alpha = Image.new("L", (w, h), 0)
    a = alpha.load()
    for y in range(h):
        for x in range(w):
            if fg[y][x]:
                a[x, y] = 255
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    rgba = im.convert("RGBA")
    rgba.putalpha(alpha)
    box = alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
    rgba = rgba.crop(box)
    rgba.save(OUT / (path.stem + ".png"), optimize=True)
    return rgba.size


for f in sorted(SRC.glob("*.jpg")):
    print(f.name, cut(f))


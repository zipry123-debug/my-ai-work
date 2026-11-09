"""진(zine) 슬라이드용 질감·오브제를 PNG/JPG로 굽는다(PDF에서 SVG 필터·블렌드 없이 같은 모습이 나오도록).
- 종이 배경(그레인·구김·섬유), 찢은 종이 조각(섬유 단면·그림자·하프톤), 마스킹테이프, 스테이플러 심,
  흰 테두리 컷아웃 제품, 흑백 복사(xerox) 제품 스크랩, 낡은 도장용 스펙클.
찢김 모양은 조각마다 시드가 달라 같은 경로가 반복되지 않는다."""
import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

D = Path(__file__).parent
OUT = D / "tex"; OUT.mkdir(exist_ok=True)
CUT = D.parent / "maximal" / "cut"

PAPER = (239, 230, 211)   # 미색 종이
FIBER = (250, 246, 236)   # 찢긴 단면의 흰 섬유
INK = (17, 17, 20)
COBALT = (27, 63, 176)
FLUO = (255, 46, 136)     # 형광 핑크(포인트 1색)
COLORS = {"paper": PAPER, "white": (251, 249, 243), "ink": INK, "cobalt": COBALT, "fluo": FLUO, "gray": (196, 191, 180)}


def noise(w, h, scale, seed):
    """부드러운 저주파 노이즈(0~1)."""
    r = np.random.default_rng(seed)
    small = r.random((max(2, h // scale), max(2, w // scale)))
    im = Image.fromarray((small * 255).astype("uint8")).resize((w, h), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32) / 255


def texture(rgb, w, h, seed, grain=9, crumple=0.07, speckle=0.0015):
    """단색 면에 종이 그레인 + 구김 음영 + 복사기 점을 입힌다."""
    r = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * np.array(rgb, np.float32)
    shade = (noise(w, h, 90, seed) - .5) * 2 * crumple + (noise(w, h, 22, seed + 1) - .5) * crumple * .6
    base *= (1 + shade)[..., None]
    base += r.normal(0, grain, (h, w, 1))
    sp = r.random((h, w)) < speckle
    base[sp] = base[sp] * .35
    return np.clip(base, 0, 255).astype("uint8")


def torn_poly(w, h, seed, sides, amp):
    """사각형 둘레를 따라 찢긴 윤곽 점들(시계 방향)과 각 점의 안쪽 법선을 만든다."""
    rnd = random.Random(seed)
    pts = []

    def edge(n, torn):
        out, v = [], 0.0
        ph = [rnd.uniform(0, 6.3) for _ in range(3)]
        fr = [rnd.uniform(.6, 1.6), rnd.uniform(2.5, 4.5), rnd.uniform(7, 12)]
        for i in range(n + 1):
            t = i / max(n, 1)
            if torn:
                v += rnd.uniform(-1, 1) * amp * .3
                v *= .7
                wav = sum(math.sin(t * f * 6.283 + p) * a for f, p, a in zip(fr, ph, (1.1, .45, .2))) * amp
                j = wav + v + rnd.uniform(-1, 1) * amp * .12 + (rnd.random() < .04) * rnd.uniform(.3, .9) * amp
                k = min(t, 1 - t) / .08
                if k < 1: j = j * k - amp * 1.8 * (1 - k)
            else:
                j = rnd.uniform(-.6, .6)
            out.append(j)
        return out

    step = 7
    for side, (n, L) in zip("trbl", [(w // step, w), (h // step, h), (w // step, w), (h // step, h)]):
        js = edge(n, side in sides)
        for i, j in enumerate(js[:-1]):
            t = i / n * L
            m = j + amp * 1.8 if side in sides else abs(j)
            if side == "t": pts.append((t, m, (0, 1)))
            if side == "r": pts.append((w - m, t, (-1, 0)))
            if side == "b": pts.append((w - t, h - m, (0, -1)))
            if side == "l": pts.append((m, h - t, (1, 0)))
    return pts


def piece(name, w, h, color, seed, sides="trbl", amp=14, fiber=True, shadow=True, halftone=None, rot=0.0):
    """찢은 종이 조각 PNG. halftone=(색, 간격) 이면 점 무늬를 얹는다."""
    S, pad = 2, 40
    W, H = (w + pad * 2) * S, (h + pad * 2) * S
    pts = torn_poly(w, h, seed, sides, amp)
    rnd = random.Random(seed + 7)
    outer = [((x + pad) * S, (y + pad) * S) for x, y, _ in pts]
    inner = []
    band = noise(len(pts), 1, 6, seed + 11)[0] if fiber else None
    for k, (x, y, (nx, ny)) in enumerate(pts):
        d = (2 + band[k] * 13 + rnd.uniform(0, 2)) if fiber else 0
        inner.append(((x + pad + nx * d) * S, (y + pad + ny * d) * S))
    m_out = Image.new("L", (W, H), 0); ImageDraw.Draw(m_out).polygon(outer, fill=255)
    m_in = Image.new("L", (W, H), 0); ImageDraw.Draw(m_in).polygon(inner, fill=255)
    m_out = m_out.resize((W // S, H // S), Image.LANCZOS); m_in = m_in.resize((W // S, H // S), Image.LANCZOS)
    Wc, Hc = m_out.size
    face = Image.fromarray(texture(COLORS[color], Wc, Hc, seed, grain=7, crumple=.025 if color == "white" else .06))
    if halftone:
        hc, gap = halftone
        dots = Image.new("L", (Wc, Hc), 0); dd = ImageDraw.Draw(dots)
        fall = noise(Wc, Hc, 160, seed + 3)
        for yy in range(0, Hc, gap):
            for xx in range(0 if (yy // gap) % 2 == 0 else gap // 2, Wc, gap):
                r0 = gap * .42 * fall[min(yy, Hc - 1), min(xx, Wc - 1)]
                if r0 > .8: dd.ellipse((xx - r0, yy - r0, xx + r0, yy + r0), fill=255)
        face = Image.composite(Image.new("RGB", (Wc, Hc), COLORS[hc]), face, dots.point(lambda v: int(v * .55)))
    fib = Image.fromarray(texture(FIBER, Wc, Hc, seed + 2, grain=5, crumple=.03, speckle=0))
    img = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (Wc, Hc), (20, 16, 10, 0))
        sh.putalpha(m_out.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * .42)))
        img.alpha_composite(sh, (5, 8)) if False else img.paste(sh, (5, 8), sh)
    fl = fib.convert("RGBA"); fl.putalpha(m_out); img.alpha_composite(fl)
    fc = face.convert("RGBA"); fc.putalpha(m_in); img.alpha_composite(fc)
    if rot:
        img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    img.save(OUT / f"{name}.png", optimize=True)
    return {"name": name, "w": img.width, "h": img.height, "pad": pad}


def paper_bg(name, color="paper", seed=1, w=1920, h=1080):
    """슬라이드 바탕 종이(불투명이라 JPG)."""
    arr = texture(COLORS[color], w, h, seed, grain=7, crumple=.035, speckle=.0008)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im); rnd = random.Random(seed)
    for _ in range(260):  # 종이 섬유 실
        x, y = rnd.randrange(w), rnd.randrange(h); a = rnd.uniform(0, math.pi); L = rnd.uniform(6, 22)
        c = tuple(int(v * rnd.uniform(.86, .95)) for v in COLORS[color])
        d.line((x, y, x + math.cos(a) * L, y + math.sin(a) * L), fill=c, width=1)
    im.save(OUT / f"{name}.jpg", quality=82)


def tape(name, w, h, seed):
    rnd = random.Random(seed)
    pts = [(0, rnd.uniform(0, 5))] + [(w, rnd.uniform(0, 5))]
    right = [(w - rnd.uniform(0, 7), y) for y in np.linspace(0, h, 9)]
    left = [(rnd.uniform(0, 7), y) for y in np.linspace(h, 0, 9)]
    poly = pts + right + [(0 + w, h)] + left
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(poly, fill=200)
    face = Image.fromarray(texture((236, 226, 196), w, h, seed, grain=6, crumple=.05, speckle=0)).convert("RGBA")
    face.putalpha(m)
    sh = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0)); s = Image.new("RGBA", (w, h), (30, 25, 15, 0))
    s.putalpha(m.point(lambda v: int(v * .22)).filter(ImageFilter.GaussianBlur(3))); sh.paste(s, (3, 5), s); sh.alpha_composite(face, (0, 0))
    sh.save(OUT / f"{name}.png", optimize=True)


def staple(name):
    w, h = 64, 14
    im = Image.new("RGBA", (w + 6, h + 6), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 6, w + 3, h + 4), 5, fill=(0, 0, 0, 70))
    d.rounded_rectangle((0, 2, w, h), 5, fill=(150, 152, 158, 255), outline=(90, 92, 98, 255), width=2)
    d.line((6, 5, w - 6, 5), fill=(225, 227, 232, 255), width=2)
    im.save(OUT / f"{name}.png")


def cutout_white(src, name, border=14, gray=False, xerox=False):
    """제품 누끼에 흰 테두리(오려 붙인 사진) + 그림자. xerox=True면 흑백 복사 질감."""
    im = Image.open(CUT / src).convert("RGBA")
    scale = 2.0
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    if gray or xerox:
        L = ImageOps.grayscale(im.convert("RGB"))
        if xerox:
            # 복사기 느낌: 대비를 세게 올리고 중간톤을 하프톤 점으로, 노이즈 얹기
            L = ImageOps.autocontrast(L, cutoff=2).point(lambda v: int(255 * (v / 255) ** 2.2))
            arr = np.asarray(L, np.float32)
            yy, xx = np.mgrid[0:L.height, 0:L.width]
            screen = (np.sin(xx * .9) * np.sin(yy * .9) + 1) * 64 + 64
            arr = np.where(arr > 225, 245, np.where(arr < screen, 25, 235)).astype(np.float32)
            arr += np.random.default_rng(len(src)).normal(0, 14, arr.shape)
            L = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
        rgb = L.convert("RGB"); rgb.putalpha(im.getchannel("A")); im = rgb
    pad = border + 24
    W, H = im.width + pad * 2, im.height + pad * 2
    a = Image.new("L", (W, H), 0); a.paste(im.getchannel("A"), (pad, pad))
    rim = a.filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (20, 16, 10, 0)); sh.putalpha(rim.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * .4)))
    out.paste(sh, (6, 10), sh)
    white = Image.new("RGBA", (W, H), (252, 250, 245, 255)); white.putalpha(rim); out.alpha_composite(white)
    out.alpha_composite(im, (pad, pad))
    out.save(OUT / f"{name}.png", optimize=True)


def speckle(name, w=420, h=420, seed=5):
    """도장 위에 얹어 잉크가 빠진 듯 보이게 하는 종이색 점."""
    r = np.random.default_rng(seed)
    a = (r.random((h, w)) < .09).astype("uint8") * 255
    a = np.maximum(a, ((noise(w, h, 14, seed) > .68) * 230).astype("uint8"))
    im = Image.new("RGBA", (w, h), PAPER + (0,)); im.putalpha(Image.fromarray(a).filter(ImageFilter.GaussianBlur(.6)))
    im.save(OUT / f"{name}.png", optimize=True)


if __name__ == "__main__":
    meta = {}
    paper_bg("bg_paper", "paper", 11)
    paper_bg("bg_ink", "ink", 12)
    # 표지 조각
    for args in [("c_cobalt", 1180, 720, "cobalt", 101, "trbl", 18, True, True, ("fluo", 0) and None),
                 ("c_fluo", 520, 360, "fluo", 102, "trbl", 14),
                 ("c_ink", 900, 210, "ink", 103, "tb", 12),
                 ("c_white", 560, 260, "white", 104, "trbl", 10),
                 ("c_news", 640, 520, "gray", 105, "trbl", 16)]:
        meta[args[0]] = piece(*args)
    meta["c_cobalt_ht"] = piece("c_cobalt_ht", 1180, 720, "cobalt", 101, "trbl", 18, halftone=("ink", 14))
    # 데이터 장 조각
    meta["d_sheet"] = piece("d_sheet", 1560, 720, "white", 201, "t", 16)
    meta["d_ink"] = piece("d_ink", 1080, 150, "ink", 202, "trbl", 10)
    meta["d_fluo"] = piece("d_fluo", 300, 220, "fluo", 203, "trbl", 12)
    meta["d_cobalt"] = piece("d_cobalt", 420, 300, "cobalt", 204, "trbl", 14, halftone=("ink", 12))
    # 리소 판 어긋남용: 코발트 하프톤과 같은 모양의 형광 판
    meta["c_fluo_reg"] = piece("c_fluo_reg", 1180, 720, "fluo", 101, "trbl", 18, fiber=False, shadow=False)
    meta["c_white2"] = piece("c_white2", 1080, 200, "white", 106, "trbl", 12)
    meta["c_white3"] = piece("c_white3", 940, 200, "white", 107, "trbl", 12)
    meta["c_sticker"] = piece("c_sticker", 300, 240, "fluo", 108, "trbl", 14)
    meta["c_label"] = piece("c_label", 760, 90, "white", 109, "lr", 8)
    meta["d_news"] = piece("d_news", 520, 820, "gray", 205, "trbl", 16, halftone=("ink", 10))
    meta["d_label"] = piece("d_label", 520, 80, "fluo", 206, "lr", 8)
    # 장별 조각: (이름, 너비, 높이, 색, 찢는 변, 굴곡, 하프톤). 시드는 이름마다 달라 같은 찢김이 반복되지 않음
    SPEC = [
        ("p2_news", 900, 1000, "gray", "trbl", 18, ("ink", 11)), ("p2_cobalt", 720, 800, "cobalt", "trbl", 18, None),
        ("p2_white1", 560, 170, "white", "trbl", 10, None), ("p2_white2", 620, 230, "white", "trbl", 12, None),
        ("p2_ink", 620, 230, "ink", "trbl", 12, None), ("p2_fluo", 360, 280, "fluo", "trbl", 14, None),
        ("p2_label", 640, 80, "white", "lr", 8, None),
        ("p3_fluo", 1160, 720, "fluo", "trbl", 18, None), ("p3_white", 1040, 200, "white", "trbl", 12, None),
        ("p3_ink", 920, 220, "ink", "trbl", 12, None), ("p3_cobalt", 620, 420, "cobalt", "trbl", 16, ("ink", 12)),
        ("p3_label", 560, 80, "white", "lr", 8, None),
        ("p4_ink", 1120, 150, "ink", "trbl", 10, None), ("p4_a", 540, 760, "white", "trbl", 12, None),
        ("p4_b", 540, 760, "white", "trbl", 12, None), ("p4_c", 540, 760, "white", "trbl", 12, None),
        ("p5_ink", 1120, 150, "ink", "trbl", 10, None), ("p5_d", 540, 760, "white", "trbl", 12, None),
        ("p5_e", 540, 760, "paper", "trbl", 12, None), ("p5_note", 520, 760, "ink", "trbl", 12, None),
        ("p7_white", 820, 800, "white", "trbl", 14, None), ("p7_fluo", 880, 860, "fluo", "trbl", 18, ("ink", 12)),
        ("p7_ink", 960, 170, "ink", "trbl", 10, None), ("p7_text", 800, 420, "white", "trbl", 12, None),
        ("p8_ink", 1180, 150, "ink", "trbl", 10, None), ("p8_sheet", 1760, 720, "white", "t", 16, None),
        ("p8_cobalt", 760, 300, "cobalt", "trbl", 14, ("ink", 12)),
        ("p9_ink", 1000, 150, "ink", "trbl", 10, None), ("p9_1", 470, 740, "white", "trbl", 12, None),
        ("p9_2", 470, 740, "white", "trbl", 12, None), ("p9_3", 360, 740, "paper", "trbl", 12, None),
        ("p9_4", 360, 740, "gray", "trbl", 12, None),
        ("p10_ink", 1240, 150, "ink", "trbl", 10, None), ("p10_sheet", 1760, 300, "white", "trbl", 12, None),
        ("p10_white", 1040, 440, "white", "trbl", 12, None), ("p10_fluo", 700, 460, "fluo", "trbl", 16, None),
        ("p11_white", 1260, 190, "white", "trbl", 12, None), ("p11_fluo", 560, 190, "fluo", "trbl", 12, None),
        ("p11_sheet", 1780, 400, "paper", "trbl", 14, None),
        ("p12_ink", 1160, 150, "ink", "trbl", 10, None), ("p12_sheet", 1760, 740, "white", "t", 16, None),
        ("p13_fluo", 1900, 900, "fluo", "trbl", 20, ("ink", 14)), ("p13_white", 980, 170, "white", "trbl", 12, None),
        ("p13_1", 560, 330, "white", "trbl", 10, None), ("p13_2", 560, 330, "white", "trbl", 10, None),
        ("p13_3", 560, 330, "white", "trbl", 10, None), ("p13_4", 560, 330, "white", "trbl", 10, None),
        ("p13_5", 560, 330, "white", "trbl", 10, None), ("p13_6", 560, 330, "white", "trbl", 10, None),
        ("p14_ink", 1300, 150, "ink", "trbl", 10, None), ("p14_1", 560, 740, "white", "trbl", 12, None),
        ("p14_2", 560, 740, "white", "trbl", 12, None), ("p14_3", 560, 740, "white", "trbl", 12, None),
        ("p15_ink", 1140, 150, "ink", "trbl", 10, None), ("p15_white", 860, 720, "white", "trbl", 12, None),
        ("p15_gray", 880, 720, "paper", "trbl", 12, None),
        ("p16_cobalt", 1880, 1000, "cobalt", "trbl", 20, ("ink", 14)), ("p16_white", 1180, 190, "white", "trbl", 12, None),
        ("p16_ink", 760, 190, "ink", "trbl", 12, None), ("p16_1", 410, 430, "paper", "trbl", 12, None),
        ("p16_2", 410, 430, "white", "trbl", 12, None), ("p16_3", 410, 430, "fluo", "trbl", 12, None),
        ("p16_4", 410, 430, "white", "trbl", 12, None), ("p16_ask", 1400, 100, "white", "lr", 8, None),
    ]
    for k, (nm, w, h, col, sd, amp, ht) in enumerate(SPEC):
        meta[nm] = piece(nm, w, h, col, 1000 + k * 17, sd, amp, halftone=ht)
    for i, (w, h) in enumerate([(170, 46), (150, 42), (190, 48), (140, 40)]):
        tape(f"tape{i}", w, h, 300 + i)
    staple("staple")
    speckle("worn")
    for src in ["intensive_cream", "soothing_cream", "red_control", "calming_ampoule", "cream_mist", "daily_sun", "foaming_cleanser"]:
        cutout_white(src + ".png", "w_" + src)
        cutout_white(src + ".png", "x_" + src, border=10, xerox=True)
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print("ok", len(list(OUT.iterdir())), "files")

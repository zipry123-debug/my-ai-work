"""콘티(JSON)를 읽어 컷 이미지에 말풍선과 한글 대사를 넣는다.

사용법:
    python add_bubbles.py <콘티.json> [--only 01,04]

좌표는 모두 이미지 크기에 대한 퍼센트(0~100)다.
원본 이미지는 건드리지 않고, 결과는 콘티의 final_dir(기본 output/final)에 같은 파일명으로 저장한다.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PROJECT = Path(__file__).resolve().parents[4]
FONT_DIR = PROJECT / "fonts"
FONT_REGULAR = FONT_DIR / "Pretendard-Bold.otf"
FONT_HEAVY = FONT_DIR / "Pretendard-ExtraBold.otf"

SS = 2  # 슈퍼샘플링 배율 (테두리 계단 현상 방지)

# 인스타 피드 규격. 크기 값은 모두 이 가로 폭 기준이며, 다른 크기 이미지는 폭에 비례해 조정된다.
BASE_W, BASE_H = 1080, 1350

# 종류별 기본값(px, 가로 1080 기준).
# 48px은 인스타그램에서 휴대폰 화면(가로 약 390pt)으로 줄였을 때 약 17pt.
# shape: pill(둥근 말풍선) / cloud(구름 모양 속마음) / box(둥근 사각 박스)
# tail: point(뾰족한 꼬리) / dots(작은 동그라미 꼬리) / None
STYLES = {
    "speech":    {"size": 48, "min": 40, "font": FONT_REGULAR, "shape": "pill",  "radius": 0,  "fill": (255, 255, 255), "tail": "point", "max_width": 74},
    "thought":   {"size": 46, "min": 38, "font": FONT_REGULAR, "shape": "cloud", "radius": 0,  "fill": (255, 255, 255), "tail": "dots",  "max_width": 74},
    "narration": {"size": 42, "min": 36, "font": FONT_REGULAR, "shape": "box",   "radius": 10, "fill": (255, 244, 205), "tail": None,    "max_width": 89},
    "info":      {"size": 42, "min": 36, "font": FONT_REGULAR, "shape": "box",   "radius": 22, "fill": (228, 240, 250), "tail": None,    "max_width": 89},
    "title":     {"size": 68, "min": 52, "font": FONT_HEAVY,   "shape": "box",   "radius": 28, "fill": (255, 255, 255), "tail": None,    "max_width": 89},
}
MAX_LINES = 2
SAFE = 60           # 글자를 넣을 수 있는 가장자리 안쪽 여백(px, 1080 기준). 말풍선 전체를 이 안에 둔다
BORDER = 4          # 테두리 두께(px, 1080 기준)
TAIL_MAX = 84       # 꼬리 최대 길이(px, 1080 기준)
TAIL_BASE = 36      # 꼬리 밑변 폭(px, 1080 기준)


def pct_box(box, w, h):
    x1, y1, x2, y2 = box
    return (x1 * w / 100, y1 * h / 100, x2 * w / 100, y2 * h / 100)


def overlap_area(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx * dy if dx > 0 and dy > 0 else 0.0


def text_width(font, s):
    return font.getlength(s)


def wrap(text, font, max_w):
    """공백 기준으로 줄바꿈. 사용자가 넣은 \\n은 그대로 줄바꿈으로 쓴다."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(font, trial) <= max_w:
                cur = trial
                continue
            if cur:
                lines.append(cur)
            cur = ""
            # 단어 하나가 너무 길면 글자 단위로 자른다
            for ch in word:
                if text_width(font, cur + ch) <= max_w:
                    cur += ch
                else:
                    lines.append(cur)
                    cur = ch
        lines.append(cur)
    return lines


def layout(bubble, style, scale, img_w):
    """글자 크기를 정하고 줄을 나눈다. 두 줄을 넘으면 최소 크기까지 줄인다."""
    size = bubble.get("size", style["size"])
    max_w = min(img_w * bubble.get("max_width", style["max_width"]) / 100, img_w - 2 * SAFE * scale)
    font_path = Path(bubble["font"]) if "font" in bubble else style["font"]
    while True:
        px = round(size * scale)
        font = ImageFont.truetype(str(font_path), px)
        pad_x, pad_y = px * 0.9, px * 0.55
        if style["shape"] == "cloud":  # 구름 테두리의 볼록한 부분만큼 안쪽 여유를 더 준다
            pad_x, pad_y = px * 1.3, px * 0.95
        lines = wrap(bubble["text"], font, max_w - 2 * pad_x)
        if len(lines) <= MAX_LINES or size <= style["min"]:
            break
        size -= 2
    line_h = px * 1.32
    text_w = max(text_width(font, ln) for ln in lines)
    box_w = text_w + 2 * pad_x
    box_h = line_h * len(lines) + 2 * pad_y
    if style["shape"] == "pill":
        box_w += px * 0.6  # 둥근 끝 때문에 좌우 여유를 조금 더 준다
    return {"font": font, "px": px, "size": size, "lines": lines, "line_h": line_h, "w": box_w, "h": box_h}


def edge_map(img):
    small = img.convert("L").resize((img.width // 4, img.height // 4))
    return small.filter(ImageFilter.FIND_EDGES)


def busyness(edges, rect):
    x1, y1, x2, y2 = (int(v / 4) for v in rect)
    crop = edges.crop((max(x1, 0), max(y1, 0), max(x2, 1), max(y2, 1)))
    hist = crop.histogram()
    total = sum(hist) or 1
    return sum(i * c for i, c in enumerate(hist)) / total


def auto_place(lay, w, h, edges, avoid, placed):
    """얼굴(avoid)과 다른 말풍선을 피하고, 그림이 단순한 곳을 고른다."""
    best, best_score = None, None
    bw, bh = lay["w"], lay["h"]
    m = SAFE * w / BASE_W
    steps = 12
    for iy in range(steps + 1):
        for ix in range(steps + 1):
            x1 = m + (w - 2 * m - bw) * ix / steps
            y1 = m + (h - 2 * m - bh) * iy / steps
            rect = (x1, y1, x1 + bw, y1 + bh)
            area = bw * bh
            score = busyness(edges, rect)
            score += 1000 * sum(overlap_area(rect, a) for a in avoid) / area
            score += 1000 * sum(overlap_area(rect, p) for p in placed) / area
            score += 5 * iy / steps  # 비슷하면 위쪽을 선호
            if best_score is None or score < best_score:
                best, best_score = rect, score
    return best


def rect_from_pos(pos, lay, w, h):
    cx, cy = pos[0] * w / 100, pos[1] * h / 100
    x1 = cx - lay["w"] / 2
    y1 = cy - lay["h"] / 2
    m = SAFE * w / BASE_W
    x1 = min(max(x1, m), w - m - lay["w"])
    y1 = min(max(y1, m), h - m - lay["h"])
    return (x1, y1, x1 + lay["w"], y1 + lay["h"])


def edge_point(rect, target):
    """말풍선 중심에서 target 방향으로 나갔을 때 테두리와 만나는 점."""
    cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
    dx, dy = target[0] - cx, target[1] - cy
    dist = math.hypot(dx, dy) or 1
    ux, uy = dx / dist, dy / dist
    hw, hh = (rect[2] - rect[0]) / 2, (rect[3] - rect[1]) / 2
    # 둥근 모서리를 고려해 직사각형보다 약간 안쪽에서 만난다고 본다
    t = min(hw / abs(ux) if ux else 1e9, hh / abs(uy) if uy else 1e9) * 0.92
    return (cx + ux * t, cy + uy * t), (ux, uy), dist - t


def cloud_circles(r, bump):
    """구름 테두리를 이루는 원들의 중심. 원이 사각형 r 안쪽에 들어오도록 안으로 bump만큼 들인다."""
    x1, y1, x2, y2 = r[0] + bump, r[1] + bump, r[2] - bump, r[3] - bump
    pts = []
    for (ax, ay), (bx, by) in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)),
                               ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
        n = max(2, math.ceil(math.hypot(bx - ax, by - ay) / (bump * 1.25)))
        pts += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n)]
    return pts


def draw_cloud(draw, r, fill, border):
    bump = min(r[2] - r[0], r[3] - r[1]) * 0.24
    centers = cloud_circles(r, bump)
    for cx, cy in centers:  # 바깥 테두리
        draw.ellipse((cx - bump, cy - bump, cx + bump, cy + bump), fill=fill, outline="black", width=border)
    inner = bump - border
    for cx, cy in centers:  # 원끼리 겹친 안쪽 선 지우기
        draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=fill)
    draw.rectangle((r[0] + bump, r[1] + bump, r[2] - bump, r[3] - bump), fill=fill)


def draw_dots(draw, r, tail_target, scale, fill, border):
    """속마음 꼬리: 말풍선에서 인물 쪽으로 작아지는 동그라미 3개."""
    s = SS
    tgt = (tail_target[0] * s, tail_target[1] * s)
    (ex, ey), (ux, uy), remain = edge_point(r, tgt)
    length = min(TAIL_MAX * 1.3 * scale * s, max(remain, 0))
    if length < 20 * s:
        return
    for i, frac in enumerate((0.3, 0.62, 0.92)):
        rad = (13 - 3.5 * i) * scale * s
        cx, cy = ex + ux * length * frac, ey + uy * length * frac
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=fill, outline="black", width=border)


def draw_bubble(draw, rect, lay, style, tail_target, scale):
    s = SS
    border = max(2, round(BORDER * scale)) * s
    r = [v * s for v in rect]
    fill = style["fill"]

    if style["shape"] == "cloud":
        draw_cloud(draw, r, fill, border)
        if tail_target:
            draw_dots(draw, r, tail_target, scale, fill, border)
        draw_text(draw, r, lay)
        return

    if style["shape"] == "pill":
        radius = (r[3] - r[1]) / 2
    else:
        radius = style["radius"] * scale * s

    tail_poly_fill = None
    if style["tail"] == "point" and tail_target:
        tgt = (tail_target[0] * s, tail_target[1] * s)
        (ex, ey), (ux, uy), remain = edge_point(r, tgt)
        length = min(TAIL_MAX * scale * s, max(remain, 0))
        if length > 8 * s:
            px_, py_ = -uy, ux
            half = TAIL_BASE * scale * s / 2
            tip = (ex + ux * length, ey + uy * length)
            inner = border * 2.5
            base1 = (ex - ux * inner + px_ * half, ey - uy * inner + py_ * half)
            base2 = (ex - ux * inner - px_ * half, ey - uy * inner - py_ * half)
            draw.polygon([base1, tip, base2], fill="white", outline="black", width=border)
            # 말풍선 테두리가 꼬리 입구를 막지 않도록 안쪽을 흰색으로 다시 칠한다
            shrink = border * 1.2
            tip_in = (tip[0] - ux * shrink * 1.8, tip[1] - uy * shrink * 1.8)
            b1 = (base1[0] - px_ * shrink, base1[1] - py_ * shrink)
            b2 = (base2[0] + px_ * shrink, base2[1] + py_ * shrink)
            tail_poly_fill = [b1, tip_in, b2]

    draw.rounded_rectangle(r, radius=radius, fill=fill, outline="black", width=border)
    if tail_poly_fill:
        draw.polygon(tail_poly_fill, fill="white")
    draw_text(draw, r, lay)


def draw_text(draw, r, lay):
    s = SS
    font = ImageFont.truetype(lay["font"].path, lay["px"] * s)
    line_h = lay["line_h"] * s
    total_h = line_h * len(lay["lines"])
    cx = (r[0] + r[2]) / 2
    top = (r[1] + r[3]) / 2 - total_h / 2
    for i, ln in enumerate(lay["lines"]):
        y = top + line_h * i + line_h / 2
        draw.text((cx, y), ln, font=font, fill="black", anchor="mm")


def process_cut(cut, src_dir, out_dir):
    src = src_dir / cut["image"]
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    scale = w / BASE_W
    safe = SAFE * scale
    avoid = [pct_box(b, w, h) for b in cut.get("avoid", [])]
    edges = edge_map(img)
    placed, report = [], []

    layer = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    for bubble in cut["bubbles"]:
        style = STYLES[bubble.get("type", "speech")]
        lay = layout(bubble, style, scale, w)
        if "pos" in bubble:
            rect = rect_from_pos(bubble["pos"], lay, w, h)
        else:
            rect = auto_place(lay, w, h, edges, avoid, placed)
        tail = bubble.get("tail")
        tail_px = (tail[0] * w / 100, tail[1] * h / 100) if tail else None
        draw_bubble(draw, rect, lay, style, tail_px, scale)
        warns = []
        if any(overlap_area(rect, p) > 0 for p in placed):
            warns.append("다른 말풍선과 겹침")
        placed.append(rect)

        if len(lay["lines"]) > MAX_LINES:
            warns.append(f"{len(lay['lines'])}줄 (최대 {MAX_LINES}줄) — 대사를 나누세요")
        if any(overlap_area(rect, a) > 0 for a in avoid):
            warns.append("얼굴(avoid) 영역과 겹침")
        if rect[0] < safe - 0.5 or rect[1] < safe - 0.5 or rect[2] > w - safe + 0.5 or rect[3] > h - safe + 0.5:
            warns.append(f"가장자리 {SAFE}px 안쪽을 벗어남 — 대사를 줄이거나 나누세요")
        report.append({
            "text": bubble["text"].replace("\n", " / "),
            "lines": len(lay["lines"]),
            "size": lay["size"],
            "box_pct": [round(rect[0] / w * 100, 1), round(rect[1] / h * 100, 1),
                        round(rect[2] / w * 100, 1), round(rect[3] / h * 100, 1)],
            "warnings": warns,
        })

    layer = layer.resize((w, h), Image.LANCZOS)
    out = Image.alpha_composite(img, layer).convert("RGB")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / cut["image"]
    out.save(out_path)
    return out_path, report, (w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("conti")
    ap.add_argument("--only", help="처리할 컷 번호(파일명에 포함된 문자열), 쉼표로 구분")
    args = ap.parse_args()

    conti_path = Path(args.conti).resolve()
    conti = json.loads(conti_path.read_text(encoding="utf-8"))
    src_dir = PROJECT / conti.get("source_dir", "output")
    out_dir = PROJECT / conti.get("final_dir", "output/final")
    if out_dir.resolve() == src_dir.resolve():
        sys.exit("final_dir가 source_dir와 같으면 원본을 덮어쓰므로 중단합니다.")
    for f in (FONT_REGULAR, FONT_HEAVY):
        if not f.exists():
            sys.exit(f"글꼴이 없습니다: {f}")

    only = set(args.only.split(",")) if args.only else None
    for cut in conti["cuts"]:
        stem = Path(cut["image"]).stem
        if only and not any(stem == o or stem.endswith("_" + o) for o in only):
            continue
        out_path, report, size = process_cut(cut, src_dir, out_dir)
        size_note = "" if size == (BASE_W, BASE_H) else f" ⚠ 이미지 크기 {size[0]}x{size[1]} (인스타 규격 {BASE_W}x{BASE_H} 아님)"
        print(f"[{cut['image']}] -> {out_path}{size_note}")
        for r in report:
            mark = " ⚠ " + "; ".join(r["warnings"]) if r["warnings"] else ""
            print(f"  - {r['text']} | {r['lines']}줄, {r['size']}px, 위치 {r['box_pct']}{mark}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

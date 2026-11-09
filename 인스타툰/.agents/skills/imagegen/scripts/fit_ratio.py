"""생성된 이미지를 원하는 비율로 자르고 크기를 맞춘다. 새로 그리지 않는다.

기본값은 인스타그램 피드용 4:5, 1080x1350.

사용법:
    python fit_ratio.py <입력> <출력>                      # 4:5, 1080x1350, 가운데 기준
    python fit_ratio.py <입력> <출력> --ratio 1:1           # 1:1, 가로 1080 기준(1080x1080)
    python fit_ratio.py <입력> <출력> --ratio 16:9 --size 1920x1080
    python fit_ratio.py <입력> <출력> --anchor top          # 위쪽 기준으로 자르기 (center/top/bottom)
"""
import argparse
import sys
from pathlib import Path

from PIL import Image


def parse_pair(text, sep):
    a, b = text.lower().split(sep)
    return int(a), int(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--ratio", default="4:5", help="가로:세로 (기본 4:5)")
    ap.add_argument("--size", help="최종 크기 가로x세로. 생략하면 4:5는 1080x1350, 그 외는 가로 1080 기준")
    ap.add_argument("--anchor", default="center", choices=["center", "top", "bottom"])
    args = ap.parse_args()

    rw, rh = parse_pair(args.ratio, ":")
    if args.size:
        out_w, out_h = parse_pair(args.size, "x")
    else:
        out_w, out_h = 1080, round(1080 * rh / rw)

    img = Image.open(args.input)
    w, h = img.size
    target = rw / rh
    if w / h > target:  # 너무 넓다 → 좌우를 자른다
        cw, ch = round(h * target), h
        x0, y0 = (w - cw) // 2, 0
    else:  # 너무 길다 → 위아래를 자른다
        cw, ch = w, round(w / target)
        x0 = 0
        y0 = {"center": (h - ch) // 2, "top": 0, "bottom": h - ch}[args.anchor]
    out = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((out_w, out_h), Image.LANCZOS)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output)
    print(f"{args.input} ({w}x{h}) -> 잘라낸 영역 {cw}x{ch} @({x0},{y0}) -> {args.output} ({out_w}x{out_h})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

"""완성 컷들을 한 장에 모은 미리보기 이미지를 만든다(검수·보고용, 업로드용 아님).

사용법:
    python make_preview.py <final 폴더> <저장 경로> [--cols 4]
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parents[4]
FONT = PROJECT / "fonts" / "Pretendard-ExtraBold.otf"
WIDTH = 1080
GAP = 12
LABEL = 34  # 컷 번호를 쓰는 칸 높이
BG = (245, 242, 235)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("final_dir")
    ap.add_argument("output")
    ap.add_argument("--cols", type=int, default=4)
    args = ap.parse_args()

    files = sorted(Path(args.final_dir).glob("*.png"))
    if not files:
        sys.exit("완성 컷이 없습니다.")
    cols = args.cols
    rows = -(-len(files) // cols)
    tw = (WIDTH - GAP * (cols + 1)) // cols
    first = Image.open(files[0])
    th = round(tw * first.height / first.width)
    sheet = Image.new("RGB", (WIDTH, GAP + rows * (th + LABEL + GAP)), BG)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT), 24)
    for i, f in enumerate(files):
        x = GAP + (i % cols) * (tw + GAP)
        y = GAP + (i // cols) * (th + LABEL + GAP)
        sheet.paste(Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y))
        # 컷 번호는 그림을 가리지 않게 그림 아래 칸에 쓴다
        draw.text((x + tw / 2, y + th + LABEL / 2), f"컷 {i + 1}", font=font, fill=(60, 60, 60), anchor="mm")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    print(f"{len(files)}컷 -> {args.output} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

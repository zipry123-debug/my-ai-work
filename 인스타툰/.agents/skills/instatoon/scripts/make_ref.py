"""references 폴더의 캐릭터 시트들을 가로로 이어 붙여 기준 이미지 한 장을 만든다.

openai-gpt-image의 edit_image는 기준 이미지를 한 장만 받기 때문에 필요하다.

사용법:
    python make_ref.py <저장 경로> [시트 파일명 ...]
시트 파일명을 생략하면 charsheet_hangyeol.png, charsheet_bookmark.png를 쓴다.
"""
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parents[4]
REF_DIR = PROJECT / "references"
DEFAULT_SHEETS = ["charsheet_hangyeol.png", "charsheet_bookmark.png"]
BG = (253, 250, 241)


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: python make_ref.py <저장 경로> [시트 파일명 ...]")
    out_path = Path(sys.argv[1])
    names = sys.argv[2:] or DEFAULT_SHEETS
    sheets = [Image.open(REF_DIR / n).convert("RGB") for n in names]
    h = max(s.height for s in sheets)
    sheets = [s.resize((round(s.width * h / s.height), h)) for s in sheets]
    canvas = Image.new("RGB", (sum(s.width for s in sheets), h), BG)
    x = 0
    for s in sheets:
        canvas.paste(s, (x, 0))
        x += s.width
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    print(f"{out_path} ({canvas.width}x{canvas.height}) <- {', '.join(names)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

"""proposal-zine.html을 임시 폴더로 복사해 장별(?s=N) 1920×1080 캡처와 흑백 테스트 이미지를 만든다. 인자 pdf면 PDF도."""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps

D = Path(__file__).parent
T = Path("C:/Temp/zshot/zine")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
T.mkdir(parents=True, exist_ok=True)
shutil.copy(D / "proposal-zine.html", T / "z.html")
shutil.copytree(D / "tex", T / "tex", dirs_exist_ok=True)
n = (D / "proposal-zine.html").read_text(encoding="utf-8").count('class="frame"')
only = [int(a) for a in sys.argv[1:] if a.isdigit()] or range(1, n + 1)
out = D / "shots"; out.mkdir(exist_ok=True)
for i in only:
    png = T / f"s{i:02d}.png"
    subprocess.run([EDGE, "--headless=new", "--hide-scrollbars", "--virtual-time-budget=6000", "--window-size=1920,1080",
                    f"--screenshot={png}", f"file:///{T.as_posix()}/z.html?s={i}"], check=True)
    im = Image.open(png).convert("RGB")
    im.resize((1280, 720)).save(out / f"s{i:02d}.png")
    ImageOps.grayscale(im).resize((1280, 720)).save(out / f"s{i:02d}_bw.png")
print(len(list(only)), "slides")
if "pdf" in sys.argv:
    subprocess.run([EDGE, "--headless=new", "--virtual-time-budget=8000", "--no-pdf-header-footer",
                    f"--print-to-pdf={T / 'z.pdf'}", f"file:///{T.as_posix()}/z.html"], check=True)
    shutil.copy(T / "z.pdf", D / "proposal-zine.pdf")
    print("pdf", round((D / "proposal-zine.pdf").stat().st_size / 1024 / 1024, 1), "MB")

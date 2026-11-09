"""slides.html을 임시 폴더로 복사해 헤드리스 Edge로 장별(?s=N) 1920×1080 캡처를 만든다. 인자 pdf를 주면 PDF도 만든다."""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

D = Path(__file__).parent
T = Path("C:/Temp/zshot/mx")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
shutil.copy(D / "slides.html", T / "slides.html")
for sub in ("cut", "img"):
    shutil.copytree(D / sub, T / sub, dirs_exist_ok=True)

n = (D / "slides.html").read_text(encoding="utf-8").count('class="frame"')
only = [int(a) for a in sys.argv[1:] if a.isdigit()] or range(1, n + 1)
out = D / "shots"; out.mkdir(exist_ok=True)
for i in only:
    png = T / f"s{i:02d}.png"
    subprocess.run([EDGE, "--headless=new", "--hide-scrollbars", "--virtual-time-budget=5000", "--window-size=1920,1080",
                    f"--screenshot={png}", f"file:///{T.as_posix()}/slides.html?s={i}"], check=True)
    Image.open(png).convert("RGB").resize((1280, 720)).save(out / f"s{i:02d}.png")
print(len(list(only)), "slides")
if "pdf" in sys.argv:
    subprocess.run([EDGE, "--headless=new", "--virtual-time-budget=6000", "--no-pdf-header-footer",
                    f"--print-to-pdf={T / 'deck.pdf'}", f"file:///{T.as_posix()}/slides.html"], check=True)
    shutil.copy(T / "deck.pdf", D / "ZEROID_맥시멀_제안서.pdf")
    print("pdf ok")

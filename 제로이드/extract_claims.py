"""상세페이지 이미지 alt 문구에서 핵심 클레임(성분·임상·수치) 추출 + 제안서용 썸네일 다운로드."""
import json, re, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent
p = json.load(open(ROOT / "zeroid_data/products.json", encoding="utf-8"))
HERO = {320, 323, 325, 345, 340, 341, 372, 370, 319}
for x in p:
    if x["idx"] not in HERO:
        continue
    alts = [i["alt"] for i in x["detail_images"] if len(i["alt"]) > 15]
    keep = [a for a in alts if re.search(r"\d|MLE|Defensamide|임상|시간|배|%|피부과|무기자차|pH|저자극", a)]
    print(f"\n## {x['idx']} {x['name']} ({x['volume']})")
    for a in dict.fromkeys(keep):
        print("  -", a[:260].replace("\n", " "))

THUMBS = {"intensive_cream": "thumb_INTENSIVE_Cream.jpg", "soothing_cream": "thumb_SOOTHING_Cream.jpg",
          "foaming_cleanser": "thumb_SOOTHING_FoamingCleanser.jpg", "red_control": "thumb_500_pimprove_redctrlcr.jpg",
          "calming_ampoule": "202015362207753.jpg", "daily_sun": "데일리_선크림_사이즈베리_4.jpg",
          "cream_mist": "zeroidintensivecreammist500.jpg", "cream_mask": "zeroidintensivecreammask500.jpg",
          "intensive_lotion": "thumb_INTENSIVE_Lotion.jpg"}
out = ROOT / "proposal" / "img"
out.mkdir(parents=True, exist_ok=True)
for k, f in THUMBS.items():
    url = "https://www.zeroid.co.kr/data/rental/brand/" + urllib.parse.quote(f)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    (out / f"{k}.jpg").write_bytes(urllib.request.urlopen(req, timeout=30).read())
print("\nthumbs saved")

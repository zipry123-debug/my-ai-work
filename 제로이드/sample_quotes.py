"""테마별 대표 리뷰 문장 샘플 출력."""
import json, re

p = json.load(open("zeroid_data/products.json", encoding="utf-8"))
T = {"시술후": r"레이저|시술|필링|피부과", "아이/가족": r"아기|아이|딸|아들|남편|신랑", "여드름": r"여드름|트러블|좁쌀",
     "화장/메이크업": r"화장|메이크업|들뜸", "여름/산뜻": r"여름|산뜻|끈적|번들", "겨울/건조": r"겨울|환절기|각질|당김",
     "정착/재구매": r"정착|인생|재구매"}
for t, pat in T.items():
    print("\n==", t)
    hits = [(x["name"], r) for x in p for r in x["reviews"] if re.search(pat, r["text"]) and 60 < len(r["text"]) < 400]
    for n, r in hits[:7]:
        print(f"- [{n}|{r['skin']}] " + r["text"][:210].replace("\n", " "))

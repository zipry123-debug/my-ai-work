"""수집한 리뷰를 피부타입·상황·만족포인트 키워드로 집계."""
import json, re, collections
from pathlib import Path

D = Path(__file__).parent / "zeroid_data"
prods = json.loads((D / "products.json").read_text(encoding="utf-8"))

THEMES = {
    "가족/아이": r"아기|아이|딸|아들|유아|신생아|엄마|가족|남편|신랑|와이프|아내|온가족",
    "병원/시술 후": r"병원|피부과|레이저|시술|필링|처방|의사|수술|재생",
    "아토피/피부염": r"아토피|피부염|지루|습진|태열",
    "여드름/트러블": r"여드름|트러블|뾰루지|좁쌀|피지|모공",
    "민감/홍조/진정": r"민감|홍조|붉|빨갛|따가|자극|진정|열감",
    "건조/각질/당김": r"건조|각질|당김|당기|푸석|갈라|악건성",
    "계절(겨울/환절기)": r"겨울|환절기|가을|찬바람",
    "여름/유분": r"여름|유분|번들|끈적|산뜻|가볍",
    "메이크업/화장": r"화장|메이크업|파데|화장전|들뜸|밀림",
    "재구매/정착": r"재구매|정착|인생|쟁여|대용량|계속|몇통|몇 통",
    "흡수/발림": r"흡수|발림|스며|촉촉|보습감",
    "순함/무향": r"순하|무향|향이 없|냄새|저자극",
    "남성": r"남편|신랑|남자|아빠|군대",
    "임신/출산": r"임신|출산|임산부|산모",
    "운동/야외": r"운동|등산|골프|야외|캠핑|자전거",
}

all_r = [(p["name"], p["line"], r) for p in prods for r in p["reviews"]]
print("총 리뷰", len(all_r))
print("\n[제품별 리뷰수/평점]")
for p in sorted(prods, key=lambda p: -len(p["reviews"])):
    if p["reviews"]:
        print(f"  {p['name']}: {len(p['reviews'])}건, 평균 {sum(r['stars'] for r in p['reviews'])/len(p['reviews']):.2f}")
skin = collections.Counter(s.strip() for _, _, r in all_r for s in r["skin"].split("/") if s.strip())
print("\n[피부타입]", skin.most_common())
years = collections.Counter(r["date"][:4] for _, _, r in all_r)
print("[연도]", sorted(years.items()))
print("\n[테마 언급 리뷰수]")
for t, pat in THEMES.items():
    hits = [(n, r) for n, _, r in all_r if re.search(pat, r["title"] + r["text"])]
    byp = collections.Counter(n for n, _ in hits).most_common(3)
    print(f"  {t}: {len(hits)}건  상위제품={byp}")

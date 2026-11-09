"""올리브영 리뷰 통계·테마 집계 + 테마별 대표 문장."""
import json, re, collections
from pathlib import Path

D = json.loads((Path(__file__).parent / "zeroid_data" / "oliveyoung.json").read_text(encoding="utf-8"))
SKIN = {"A01": "건성", "A02": "복합성", "A03": "지성", "A04": "중성", "A05": "민감성"}
THEMES = {
    "시술/피부과": r"레이저|시술|필링|피부과|병원|처방|재생",
    "트러블/여드름": r"여드름|트러블|뾰루지|좁쌀|붉은|홍조|열감",
    "메이크업/화장": r"화장|메이크업|파데|들뜸|밀림|베이스",
    "건조/각질/계절": r"건조|각질|당김|당기|겨울|환절기|찬바람",
    "산뜻/여름": r"산뜻|끈적|번들|여름|가볍",
    "재구매/정착": r"재구매|정착|인생|쟁여|n통|몇통|몇 통|계속",
    "가족/아이": r"아기|아이|딸|아들|남편|신랑|엄마|가족",
    "선물/콜라보/굿즈": r"누렁이|콜라보|파우치|키링|굿즈|귀여|선물",
    "휴대/외출/미스트": r"휴대|들고|외출|수시로|뿌리|미스트|파우치에",
    "할인/가성비": r"할인|세일|가성비|올영세일|저렴|기획",
}
allr = []
print("[상품별 총 리뷰수/평점/피부타입·자극도 통계]")
for g, v in D.items():
    s = v["stats"] or {}
    sat = {q["questionName"]: {a["answerName"]: a["answerPercentage"] for a in q["answerDtos"]} for q in s.get("satisfactionStats", [])}
    print(f"- {v['name']} | 리뷰 {s.get('reviewCount')} | {s.get('ratingDistribution', {}).get('averageRating')} | {sat}")
    allr += [(v["name"], r) for r in v["reviews"]]
print("\n수집 리뷰", len(allr))
print("연월", sorted(collections.Counter(r["createdDateTime"][:7] for _, r in allr).items())[-14:])
print("피부타입", collections.Counter(SKIN.get(r["profileDto"].get("skinType"), r["profileDto"].get("skinType")) for _, r in allr).most_common())
print("재구매 비율", round(sum(r["isRepurchase"] for _, r in allr) / len(allr) * 100, 1), "%  한달사용", round(sum(r["isMonthUseReview"] for _, r in allr) / len(allr) * 100, 1), "%")
print("\n[테마]")
for t, pat in THEMES.items():
    hits = [(n, r) for n, r in allr if re.search(pat, r["content"])]
    print(f"\n== {t}: {len(hits)}건 ({len(hits)/len(allr)*100:.0f}%)  {collections.Counter(n[:30] for n, _ in hits).most_common(3)}")
    for n, r in [h for h in hits if 50 < len(h[1]["content"]) < 300][:5]:
        print(f"   · [{n[:25]}|{SKIN.get(r['profileDto'].get('skinType'),'')}|{r['createdDateTime']}] {r['content'][:170]}".replace("\n", " "))

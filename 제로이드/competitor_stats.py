"""경쟁 장벽 크림 올리브영 통계 비교 (리뷰 수·평점·자극도·보습/진정·피부타입)."""
import json
from scrape_oliveyoung import call, API

G = {
    "제로이드 인텐시브 크림": "A000000263068",
    "제로이드 수딩 크림": "A000000231589",
    "에스트라 아토베리어365 크림": "A000000198320",
    "일리윤 세라마이드 아토 집중크림": "A000000217766",
    "피지오겔 DMT 페이셜 크림": "A000000239660",
    "아벤느 시칼파트 플러스 크림": "A000000135672",
    "아토팜 MLE 크림": "A000000131051",
}
out = {}
for name, g in G.items():
    d = call(f"{API}/v2/reviews/{g}/stats")["data"] or {}
    sat = {q["questionName"]: {a["answerName"]: a["answerPercentage"] for a in q["answerDtos"]} for q in d.get("satisfactionStats", [])}
    out[name] = {"goods": g, "title": d.get("goodsName"), "reviews": d.get("reviewCount"),
                 "rating": (d.get("ratingDistribution") or {}).get("averageRating"), "sat": sat}
    print(name, "|", d.get("goodsName"), "|", d.get("reviewCount"), "|", out[name]["rating"], "|", sat)
json.dump(out, open("zeroid_data/competitors.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

"""올리브영 제로이드 상품 리뷰 수집 (도움순 커서 API + 통계 API)."""
import json, sys, time, urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "zeroid_data"
API = "https://m.oliveyoung.co.kr/review/api"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
     "Content-Type": "application/json", "Origin": "https://www.oliveyoung.co.kr", "Referer": "https://www.oliveyoung.co.kr/"}
GOODS = ["A000000232081", "A000000263068", "A000000231589", "A000000267477", "A000000263069", "A000000264125",
         "A000000253724", "A000000209913", "A000000267479", "A000000244993", "A000000209905", "A000000209904",
         "A000000267481", "A000000260585", "A000000209917", "A000000263797", "A000000268072", "A000000263058"]


def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=H)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def reviews(goods, limit):
    out, cur = [], {}
    while len(out) < limit:
        d = call(f"{API}/v2/reviews/cursor", {"goodsNumber": goods, "size": 20, "sortType": "USEFUL_SCORE_DESC",
                                               "reviewType": "ALL", **cur})
        lst = (d.get("data") or {}).get("goodsReviewList") or []
        if not lst:
            break
        out += lst
        last = lst[-1]
        cur = {"cursorId": last["reviewId"], "cursorScore": int(last["usefulPoint"]), "cursorCount": None}
        time.sleep(0.3)
    return out[:limit]


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    data = {}
    for g in GOODS:
        try:
            stats = call(f"{API}/v2/reviews/{g}/stats")
            summary = call(f"{API}/v1/reviews/{g}/summary")
            rv = reviews(g, limit)
        except Exception as e:
            print(g, "FAIL", e); continue
        name = rv[0]["goodsDto"]["goodsName"] if rv else g
        data[g] = {"name": name, "stats": stats.get("data"), "summary": summary.get("data"), "reviews": rv}
        print(g, name, len(rv))
    (OUT / "oliveyoung.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("done")

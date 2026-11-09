"""케이크를 파는 가게를 공공자료의 상호와 업종 규칙으로 자동 판정한다.

실행: python 수집/classify_rivals.py 안산시
결과: 데이터/지역/<지역>/raw/rival_cake.json. 규칙으로 정할 수 없는 가게는 미확인으로 남긴다.
가맹 브랜드는 공정거래위원회 가맹정보 브랜드 목록(공공데이터포털 15125467, 이용허락범위 제한 없음)의 주요상품명으로 판정한다.
네이버 블로그 검색은 API 약관(7.3 ③, 검색 특약 2.1) 위반 소지가 있어 쓰지 않는다.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collect_region import ENV, ROOT, get_json  # noqa: E402
from core import tm5174_to_wgs84  # noqa: E402

CAKE_NAME = re.compile(r"케이크|케익|케이커리|cake", re.I)
BAKERY_KIND = "빵/도넛"
FRANCHISE = re.compile(r"[파빠][리]\s*바게|뚜레쥬르|뚜레주르")
# 케이크를 주력으로 팔지 않는 업태와 범위에서 뺀 떡케이크.
NOT_CAKE = re.compile(r"호떡|핫도그|붕어|타코야|와플|도넛|도너츠|또넛|꽈배기|찹쌀|호두|대추빵|찐빵|고로케|도로케|프레즐|프레첼|화덕|레표시카|탄드르|단팥빵|산도|던킨|크로플")
RICE_CAKE = re.compile(r"떡케이크|떡케익|앙금|떡집|떡방|떡창고")
NOT_SHOP = re.compile(r"청소|광고|건축|인테리어")
BRAND_DIR = ROOT / "데이터" / "원본" / "가맹브랜드"
BRAND_YEAR = "2025"
# 가맹 브랜드의 주요상품명으로 판정한다. 조각·떡·팬·파운드·아이스크림 케이크만 있으면 판매로 보지 않는다.
BRAND_CAKE = re.compile(r"(?<!조각)(?<!떡)(?<!팬)(?<!파운드)(?<!파운드 )(?<!아이스크림 )(?<!시나몬 )(케이크|케익|케잌)")
BRAND_NOT_CAKE = re.compile(r"호두|꽈배기|도넛|도너츠|도나스|핫도그|와플|크로플|츄러스|베이글|샌드위치|고로케|붕어빵|계란빵|십원빵|땅콩빵|식빵|소금빵|에그타르트|타르트|카스테라|호떡|프레즐|번$|파이|마카롱|쿠키|스콘|바게|토스트")
# 빵·베이커리·제과·디저트처럼 넓은 말이 있으면 케이크도 팔 수 있어 제외하지 않는다.
BRAND_GENERAL = re.compile(r"(^|[\s,/])빵($|[\s,/류])|베이커리|제과|디저트")
BRAND_MIN_LEN = 3  # 두 글자 브랜드는 다른 상호와 우연히 겹치기 쉬워 쓰지 않는다.

squash = lambda s: re.sub(r"[\s\W_]", "", str(s)).lower()
SAME_SHOP_M = 30  # 상가 자료와 인허가 자료의 같은 가게는 좌표가 거의 같다(대부분 0~15m).
SPELLING = ((re.compile(r"[파빠]리바게[뜨트]"), "파리바게뜨"), (re.compile(r"뚜레주르"), "뚜레쥬르"))


def name_key(name):
    key = squash(name)
    for pattern, fixed in SPELLING:
        key = pattern.sub(fixed, key)
    return key


def same_shop(a, b):
    """두 자료에 따로 실린 같은 가게인지. '파리바게뜨'와 '파리바게뜨 가오은어송점'처럼 지점명만 다를 수 있다."""
    near = math.hypot((a["lat"] - b["lat"]) * 111000, (a["lon"] - b["lon"]) * 111000 * math.cos(math.radians(a["lat"]))) <= SAME_SHOP_M
    x, y = name_key(a["name"]), name_key(b["name"])
    return near and bool(x) and bool(y) and (x in y or y in x or x[:4] == y[:4])


def brand_list():
    """공정거래위원회 가맹정보 브랜드 목록(이용허락범위 제한 없음)을 한 번 받아 둔다."""
    path = BRAND_DIR / f"브랜드_{BRAND_YEAR}.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    rows, page = [], 1
    while True:
        body = get_json("https://apis.data.go.kr/1130000/FftcBrandRlsInfo2_Service/getBrandinfo",
                        {"pageNo": page, "numOfRows": 1000, "jngBizCrtraYr": BRAND_YEAR, "resultType": "json"},
                        key_param="serviceKey", key=ENV["DATA_GO_KR_KEY"])
        rows += body.get("items") or []
        if not body.get("items") or len(rows) >= int(body["totalCount"]):
            break
        page += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False), "utf-8")
    return rows


def candidates(raw_dir, region):
    """상가 자료의 빵집과 케이크 상호, 인허가에만 있는 영업 중 제과점과 케이크 상호를 모은다."""
    def raw(name):
        data = json.loads((raw_dir / f"{name}.json").read_text("utf-8"))
        return data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))

    result, names, merged = [], set(), []
    stores = raw("stores")
    all_store_names = {squash(s.get("bizesNm")) for s in stores}
    for store in stores:
        name = store.get("bizesNm") or ""
        if store.get("indsSclsNm") == BAKERY_KIND or CAKE_NAME.search(name):
            result.append({"id": store["bizesId"], "name": name, "dong": store.get("adongNm", ""), "kind": store.get("indsSclsNm", ""),
                           "lat": round(float(store["lat"]), 6), "lon": round(float(store["lon"]), 6)})
            names.add((squash(name), store.get("adongNm", "")))
    for dataset, only_cake in (("bakeries", False), ("instant_food_processors", True), ("rest_cafes", True)):
        for row in raw(f"license_{dataset}"):
            name = row.get("BPLC_NM") or ""
            if not str(row.get("SALS_STTS_NM", "")).startswith("영업") or (only_cake and not CAKE_NAME.search(name)):
                continue
            if squash(name) in all_store_names:
                continue
            address = row.get("LOTNO_ADDR") or row.get("ROAD_NM_ADDR") or ""
            found = re.search(r"\S+[구군]\s+(\S+?[동리가읍면])(?:\s|$)", address)
            dong = found.group(1) if found else ""
            try:
                lat, lon = tm5174_to_wgs84(float(row["CRD_INFO_X"]), float(row["CRD_INFO_Y"]))
            except (TypeError, ValueError):
                continue
            key = (squash(name), dong)
            if key in names:
                continue
            shop = {"id": row["MNG_NO"], "name": name, "dong": dong, "kind": row.get("SNTTN_BZSTAT_NM") or "", "lat": round(lat, 6), "lon": round(lon, 6)}
            twin = next((other for other in result if same_shop(shop, other)), None)
            if twin:
                merged.append((name, twin["name"]))
                continue
            names.add(key)
            result.append(shop)
    print(f"같은 가게로 보고 합침: {len(merged)}곳", [f"{a} = {b}" for a, b in merged[:8]], flush=True)
    return result


def brand_rules():
    """(상호 앞부분, 판정, 브랜드명) 목록. 긴 브랜드명을 먼저 맞춘다."""
    rules = []
    for brand in brand_list():
        goods = brand.get("majrGdsNm") or ""
        bakery = brand.get("indutyMlsfcNm") == "제과제빵"
        # 커피·빙수 브랜드의 케이크는 조각 케이크인 경우가 많아, 첫 주요상품이 케이크일 때만 판매로 본다.
        if BRAND_CAKE.search(goods if bakery else re.split(r"[,/]", goods)[0]):
            status = "판매"
        elif bakery and BRAND_NOT_CAKE.search(goods) and not BRAND_GENERAL.search(goods):
            status = "제외"
        else:
            continue
        for part in re.split(r"/", re.sub(r"\(.*?\)|\[.*?\]", "", brand["brandNm"])):
            key = squash(part)
            if len(key) >= BRAND_MIN_LEN:
                rules.append((key, status, brand["brandNm"].strip()))
    return sorted(set(rules), key=lambda rule: -len(rule[0]))


def by_rule(shop, brands):
    """상호와 업종으로 (판정, 근거)를 돌려준다. 정할 수 없으면 미확인이다."""
    name = shop["name"]
    if FRANCHISE.search(name):
        return "판매", "프랜차이즈"
    if RICE_CAKE.search(name) or NOT_CAKE.search(name) or NOT_SHOP.search(shop["kind"]) or NOT_SHOP.search(name):
        return "제외", "상호나 업종"
    key = squash(name)
    for prefix, status, brand in brands:
        if key.startswith(prefix):
            return status, f"가맹 브랜드({brand})"
    if CAKE_NAME.search(name) and not re.search(r"학원", shop["kind"]):
        return "판매", "상호에 케이크"
    return "미확인", ""


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    region = sys.argv[1]
    raw_dir = ROOT / "데이터" / "지역" / region / "raw"
    shops = candidates(raw_dir, region)
    print("후보:", len(shops), flush=True)
    brands = brand_rules()
    print("가맹 브랜드 규칙:", len(brands))
    counts = {}
    for shop in shops:
        shop["status"], shop["basis"] = by_rule(shop, brands)
        counts[shop["status"]] = counts.get(shop["status"], 0) + 1
    (raw_dir / "rival_cake.json").write_text(json.dumps(shops, ensure_ascii=False), "utf-8")
    print("판정:", counts)


if __name__ == "__main__":
    main()

"""후보지 하나를 조사해 화면에 넘길 결과를 만든다. 실패한 항목은 0이 아니라 '확인 불가'로 남긴다."""
from datetime import date

import core
from sources import DATASETS, MissingKey, SourceError

KEYWORDS = ["레터링케이크", "주문제작케이크"]


def _failure(err):
    state = "missing_key" if isinstance(err, MissingKey) else "error"
    return {"state": state, "message": str(err)}


def _section(fn):
    try:
        return {"state": "ok", **fn()}
    except SourceError as err:
        return _failure(err)


def _competitors(client, lat, lon, radius):
    wide = {}
    truncated = False
    for keyword in KEYWORDS:
        found = client.places(keyword, lat, lon, core.WIDE_RADIUS_M)
        truncated = truncated or found["total"] > len(found["rows"])
        for place in found["rows"]:
            wide.setdefault(place["id"], place)
    rows = sorted(wide.values(), key=lambda p: p["distance"])
    return {
        "near": sum(1 for p in rows if p["distance"] <= radius),
        "wide": len(rows),
        "truncated": truncated,
        "rows": rows,
    }


def _stores(client, lat, lon, radius):
    found = client.stores(lat, lon, radius)
    bakery = [s for s in found["rows"] if core.is_bakery_store(s)]
    return {
        "food_total": found["total"] if found["total"] is not None else len(found["rows"]),
        "bakery": len(bakery),
        "rows": [
            {
                "name": s.get("bizesNm", ""),
                "category": s.get("indsSclsNm", ""),
                "address": s.get("rdnmAdr") or s.get("lnoAdr", ""),
                "lat": _to_float(s.get("lat")),
                "lon": _to_float(s.get("lon")),
            }
            for s in bakery
        ],
    }


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load(client, dataset, region, name_like=None):
    found = client.licenses(dataset, region, name_like)
    rows = [core.normalize_license(r, DATASETS[dataset]) for r in found["rows"]]
    return rows, found.get("truncated", False)


def _serialize(rows, lat, lon):
    result = []
    for r in rows:
        result.append(
            {
                "name": r["name"],
                "dataset": r["dataset"],
                "status": r["status"] or ("폐업" if r["is_closed"] else ""),
                "is_closed": r["is_closed"],
                "opened": r["opened"].isoformat() if r["opened"] else None,
                "closed": r["closed"].isoformat() if r["closed"] else None,
                "address": r["road"] or r["lot"],
                "lat": r["lat"],
                "lon": r["lon"],
                "distance": round(core.distance_m(lat, lon, r["lat"], r["lon"])) if r["lat"] is not None else None,
            }
        )
    return sorted(result, key=lambda i: (not i["is_closed"], i["closed"] or "", i["name"]))


def _licenses(client, lat, lon, radius, region, today):
    bakery_rows, truncated = _load(client, "bakeries", region)

    # 상호에 '케이크'가 들어간 업소는 제과점 외 업종으로 신고했을 수 있어 함께 본다.
    cake_rows = [r for r in bakery_rows if core.CAKE_WORD in r["name"]]
    partial = []
    for dataset in ("rest_cafes", "instant_food_processors"):
        try:
            rows, cut = _load(client, dataset, region, core.CAKE_WORD)
            cake_rows += rows
            truncated = truncated or cut
        except SourceError as err:
            partial.append(f"{DATASETS[dataset]}: {err}")
    cake_rows = core.dedupe_licenses(cake_rows)

    problems = core.mapping_problems(bakery_rows)
    if problems:
        raise SourceError(f"응답에서 다음 항목을 찾지 못했습니다: {', '.join(problems)}. 필드명 확인이 필요합니다")

    near_bakery = core.within_radius(bakery_rows, lat, lon, radius)
    near_cake = core.within_radius(cake_rows, lat, lon, core.WIDE_RADIUS_M)
    summary = core.license_summary(near_bakery, today)
    return {
        "summary": summary,
        "cake_summary": core.license_summary(near_cake, today),
        "warnings": core.warnings_for(summary),
        "region_rows": len(bakery_rows),
        "no_coordinates": sum(1 for r in bakery_rows if r["lat"] is None),
        "truncated": truncated,
        "partial": partial,
        "rows": _serialize(near_bakery, lat, lon),
        "cake_rows": _serialize(near_cake, lat, lon),
        "dongs": core.dong_table(bakery_rows, today),
    }


def analyze(client, query, radius, today=None):
    today = today or date.today()
    base = {"query": query, "radius": radius}
    try:
        place = client.geocode(query)
    except SourceError as err:
        return {**base, "message": str(err), "state": "failed"}
    if not place:
        return {**base, "state": "failed", "message": "이 이름으로 위치를 찾지 못했습니다"}

    lat, lon = place["lat"], place["lon"]
    region = core.region_from_address(place["address"])
    return {
        **base,
        "state": "ok",
        "place": place,
        "region": region,
        "competitors": _section(lambda: _competitors(client, lat, lon, radius)),
        "stores": _section(lambda: _stores(client, lat, lon, radius)),
        "licenses": _section(lambda: _licenses(client, lat, lon, radius, region, today)),
    }

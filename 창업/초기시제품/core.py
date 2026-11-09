"""입지 지표 계산. 네트워크를 쓰지 않는 순수 함수만 둔다."""
import math
import re
from datetime import date

# 위험 신호 기준. 공식 통계가 아니라 이 프로그램이 정한 실무 기준이라 화면에도 그렇게 표시한다.
CLOSURE_WARNING_COUNT = 3
LOOKBACK_YEARS = 3
WIDE_RADIUS_M = 3000  # 주문제작 케이크는 손님이 찾아오므로 넓은 반경도 함께 본다.

CAKE_WORD = "케이크"
BAKERY_CATEGORY = re.compile(r"빵|제과|케이크|디저트")
BAKERY_NAME = re.compile(r"케이크|케익|베이커리|제과|베이크")


# ---------- 좌표 변환: EPSG:5174(Bessel 중부원점 TM) -> WGS84 ----------
_BESSEL_A = 6377397.155
_BESSEL_F = 1 / 299.1528128
_WGS84_A = 6378137.0
_WGS84_F = 1 / 298.257223563
_LAT0 = math.radians(38.0)
_LON0 = math.radians(127.0028902777778)
_FALSE_E = 200000.0
_FALSE_N = 500000.0
_TOWGS84 = (-115.80, 474.99, 674.11, 1.16, -2.31, -1.63, 6.43)


def _meridian_arc(lat, e2):
    return _BESSEL_A * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lat
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * lat)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * lat)
        - (35 * e2**3 / 3072) * math.sin(6 * lat)
    )


def tm5174_to_wgs84(x, y):
    """TM 좌표(m)를 (위도, 경도)로 바꾼다."""
    e2 = _BESSEL_F * (2 - _BESSEL_F)
    ep2 = e2 / (1 - e2)
    m = _meridian_arc(_LAT0, e2) + (y - _FALSE_N)
    mu = m / (_BESSEL_A * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    fp = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )
    sin_fp, cos_fp, tan_fp = math.sin(fp), math.cos(fp), math.tan(fp)
    c1 = ep2 * cos_fp**2
    t1 = tan_fp**2
    n1 = _BESSEL_A / math.sqrt(1 - e2 * sin_fp**2)
    r1 = _BESSEL_A * (1 - e2) / (1 - e2 * sin_fp**2) ** 1.5
    d = (x - _FALSE_E) / n1
    lat = fp - (n1 * tan_fp / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lon = _LON0 + (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / cos_fp
    return _bessel_to_wgs84(lat, lon)


def _bessel_to_wgs84(lat, lon):
    e2 = _BESSEL_F * (2 - _BESSEL_F)
    n = _BESSEL_A / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    x = n * math.cos(lat) * math.cos(lon)
    y = n * math.cos(lat) * math.sin(lon)
    z = n * (1 - e2) * math.sin(lat)

    dx, dy, dz, rx, ry, rz, ppm = _TOWGS84
    arcsec = math.pi / (180 * 3600)
    rx, ry, rz = rx * arcsec, ry * arcsec, rz * arcsec
    s = 1 + ppm * 1e-6
    xt = dx + s * (x - rz * y + ry * z)
    yt = dy + s * (rz * x + y - rx * z)
    zt = dz + s * (-ry * x + rx * y + z)

    e2w = _WGS84_F * (2 - _WGS84_F)
    p = math.hypot(xt, yt)
    lat_w = math.atan2(zt, p * (1 - e2w))
    for _ in range(6):
        nw = _WGS84_A / math.sqrt(1 - e2w * math.sin(lat_w) ** 2)
        lat_w = math.atan2(zt + e2w * nw * math.sin(lat_w), p)
    return math.degrees(lat_w), math.degrees(math.atan2(yt, xt))


def distance_m(lat1, lon1, lat2, lon2):
    r = 6371008.8
    a1, a2 = math.radians(lat1), math.radians(lat2)
    da = a2 - a1
    db = math.radians(lon2 - lon1)
    h = math.sin(da / 2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(db / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# ---------- 인허가 행 정규화 ----------
# 공식 문서에서 요청 조건 이름만 확인했고 응답 필드명은 확인하지 못해, 후보 이름과 패턴으로 찾는다.
_FIELD_PATTERNS = {
    "name": ["BPLC_NM", "bplcNm", "사업장명"],
    "status": ["SALS_STTS_NM", "DTL_SALS_STTS_NM", "trdStateNm", "영업상태명"],
    "opened": ["LCPMT_YMD", "apvPermYmd", "인허가일자"],
    "closed": ["CLSBIZ_YMD", "CLSBIZ_DE", "CLSBZ_YMD", "CLS_YMD", "dcbYmd", "폐업일자"],
    "road": ["ROAD_NM_ADDR", "rdnWhlAddr", "도로명전체주소", "도로명주소"],
    "lot": ["LOTNO_ADDR", "LCTN_ADDR", "siteWhlAddr", "소재지전체주소", "지번주소"],
    "x": ["CRD_INFO_X", "CRDNT_INFO_X", "CRD_X", "X_CRD", "좌표정보X", "좌표정보(X)", "x"],
    "y": ["CRD_INFO_Y", "CRDNT_INFO_Y", "CRD_Y", "Y_CRD", "좌표정보Y", "좌표정보(Y)", "y"],
}
_FALLBACK = {
    "closed": re.compile(r"CLS|CLOS|폐업", re.I),
    "x": re.compile(r"(CRD|COORD|좌표).*X|X.*(CRD|COORD)", re.I),
    "y": re.compile(r"(CRD|COORD|좌표).*Y|Y.*(CRD|COORD)", re.I),
}


def _pick(row, field):
    lower = {k.lower(): k for k in row}
    for candidate in _FIELD_PATTERNS[field]:
        key = lower.get(candidate.lower())
        if key is not None:
            return row[key]
    pattern = _FALLBACK.get(field)
    if pattern:
        for key, value in row.items():
            if pattern.search(key):
                return value
    return None


def parse_ymd(value):
    digits = re.sub(r"\D", "", str(value or ""))[:8]
    if len(digits) != 8:
        return None
    try:
        return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
    except ValueError:
        return None


def normalize_license(row, dataset):
    """API 행 하나를 공통 형식으로 바꾼다. 데모 데이터는 lat/lon을 직접 넣어 준다."""
    lat, lon = row.get("lat"), row.get("lon")
    if lat is None or lon is None:
        lat = lon = None
        try:
            x, y = float(_pick(row, "x")), float(_pick(row, "y"))
            if x > 0 and y > 0:
                lat, lon = tm5174_to_wgs84(x, y)
        except (TypeError, ValueError):
            pass
    status = str(_pick(row, "status") or "").strip()
    closed = parse_ymd(_pick(row, "closed"))
    return {
        "dataset": dataset,
        "name": str(_pick(row, "name") or "").strip(),
        "status": status,
        "opened": parse_ymd(_pick(row, "opened")),
        "closed": closed,
        "is_closed": closed is not None or "폐업" in status,
        "road": str(_pick(row, "road") or "").strip(),
        "lot": str(_pick(row, "lot") or "").strip(),
        "lat": lat,
        "lon": lon,
    }


def mapping_problems(rows):
    """응답 필드를 못 찾으면 0건으로 보이지 않도록 문제를 알린다."""
    if not rows:
        return []
    problems = []
    if not any(r["name"] for r in rows):
        problems.append("상호")
    if not any(r["opened"] for r in rows):
        problems.append("인허가일자")
    if not any(r["status"] or r["closed"] for r in rows):
        problems.append("영업상태·폐업일자")
    if not any(r["lat"] is not None for r in rows):
        problems.append("좌표")
    return problems


def years_ago(today, years):
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, day=28)


def license_summary(rows, today):
    """영업·개업·폐업 건수와 폐업 업소의 영업 기간을 계산한다."""
    since = years_ago(today, LOOKBACK_YEARS)
    opened = [r for r in rows if r["opened"] and r["opened"] >= since]
    closed = [r for r in rows if r["closed"] and r["closed"] >= since]
    undated = [r for r in rows if r["is_closed"] and not r["closed"]]
    months = sorted(
        (r["closed"] - r["opened"]).days / 30.44
        for r in closed
        if r["opened"] and r["closed"] >= r["opened"]
    )
    median = None
    if months:
        mid = len(months) // 2
        median = months[mid] if len(months) % 2 else (months[mid - 1] + months[mid]) / 2
    return {
        "active": sum(1 for r in rows if not r["is_closed"]),
        "opened": len(opened),
        "closed": len(closed),
        "closed_undated": len(undated),
        "median_months": round(median, 1) if median is not None else None,
    }


def within_radius(rows, lat, lon, radius):
    return [
        r
        for r in rows
        if r["lat"] is not None and distance_m(lat, lon, r["lat"], r["lon"]) <= radius
    ]


def dong_of(row):
    match = re.search(r"\(([^,()]*?(?:동|읍|면|가|리))\s*[,)]", row["road"])
    if match:
        return match.group(1).strip()
    for token in row["lot"].split():
        if re.fullmatch(r"\S*\d*(?:동|읍|면|가)", token) and not token.endswith(("시", "구", "군")):
            return token
    return None


def dong_table(rows, today):
    """시군구 전체 인허가 행을 동별로 묶어 후보 동을 고를 때 쓴다."""
    since = years_ago(today, LOOKBACK_YEARS)
    table = {}
    for r in rows:
        dong = dong_of(r)
        if not dong:
            continue
        item = table.setdefault(dong, {"dong": dong, "active": 0, "opened": 0, "closed": 0})
        if not r["is_closed"]:
            item["active"] += 1
        if r["opened"] and r["opened"] >= since:
            item["opened"] += 1
        if r["closed"] and r["closed"] >= since:
            item["closed"] += 1
    return sorted(table.values(), key=lambda i: (-i["closed"], -i["active"], i["dong"]))


def dedupe_licenses(rows):
    seen = {}
    for r in rows:
        key = (r["name"], r["road"] or r["lot"], r["opened"])
        seen.setdefault(key, r)
    return list(seen.values())


def is_bakery_store(store):
    return bool(
        BAKERY_CATEGORY.search(str(store.get("indsSclsNm") or ""))
        or BAKERY_NAME.search(str(store.get("bizesNm") or ""))
    )


def warnings_for(summary):
    """치명적 신호 중 데이터로 판정할 수 있는 '같은 업종 반복 폐업'만 판정한다."""
    if summary is None:
        return []
    result = []
    if summary["closed"] >= CLOSURE_WARNING_COUNT:
        result.append(f"최근 {LOOKBACK_YEARS}년 반경 내 제과점 폐업 {summary['closed']}건")
    if summary["closed"] and summary["closed"] >= summary["opened"]:
        result.append(f"폐업({summary['closed']}건)이 개업({summary['opened']}건) 이상")
    return result


def region_from_address(address):
    """'서울 송파구 잠실동' -> '송파구', '경기 성남시 분당구 ...' -> '성남시 분당구'."""
    tokens = address.split()
    if len(tokens) < 2:
        return address
    second = tokens[1]
    if second.endswith("시") and len(tokens) > 2 and tokens[2].endswith("구"):
        return f"{second} {tokens[2]}"
    if second.endswith(("시", "군", "구")):
        return second
    return tokens[0]

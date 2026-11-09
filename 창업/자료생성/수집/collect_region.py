"""한 지역의 원자료를 API와 전국 파일에서 모아 데이터/지역/<지역>/raw 에 저장한다. 키는 파일과 출력에 남기지 않는다.

실행: python 수집/collect_region.py 41270   (시군구 코드. 폴더는 데이터/지역/41270)
이미 받은 단계는 건너뛴다. 다시 받으려면 raw 폴더의 해당 파일을 지운다.
"""
import json
import math
import re
import ssl
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "설정.env"
MARGIN_DEG = 0.012  # 지역 경계 밖 약 1km의 역·정류장도 거리 계산에 쓴다.
# 브이월드 '용도지역지구정보' 전국 SHP. 공공데이터포털 15148355에 이용허락범위 제한 없음으로 등록돼 있다.
# 브이월드 API 결과는 약관 제19조(무단 저장·제공 금지) 때문에 쓰지 않는다.
ZONE_DIR = ROOT / "데이터" / "원본" / "용도지역"
ZONE_FILES = {"urban": "국토계획/도시지역", "manage": "국토계획/관리지역", "farm": "국토계획/농림지역",
              "nature": "국토계획/자연환경보전지역", "greenbelt": "개발제한구역지관리/개발제한구역", "industrial": "산업입지/산업단지"}
# 산업단지 파일에는 재생사업지구, 보호림 같은 다른 구역도 섞여 있어 단지 종류만 남긴다.
INDUSTRIAL_KINDS = {"국가산업단지", "일반산업단지", "도시첨단산업단지", "농공단지", "지방산업단지", "준산업단지", "일반지방산업단지"}
POPULATION_FIRST_MONTH = "202210"  # 행정안전부 주민등록 인구 API의 첫 조회 가능 월
LICENSE_DATASETS = {"bakeries": "제과점영업", "rest_cafes": "휴게음식점", "instant_food_processors": "즉석판매제조가공업"}
# 휴게음식점·즉석판매는 상호로 거른 가게만 쓴다(build_region.SWEET_NAME, classify_rivals.CAKE_NAME).
# 전국에 100만 건 넘게 있어 이 말이 든 상호만 받는다. 위 두 규칙의 말을 모두 담아야 한다.
SWEET_NAME_TERMS = ("케이크", "케익", "케이커리", "베이커리", "베이크", "제과", "빵", "디저트", "레터링", "cake", "Cake", "CAKE")
NAME_FILTERED = {"rest_cafes", "instant_food_processors"}
SIDO_SHORT = {"서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천", "광주광역시": "광주",
              "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기", "강원특별자치도": "강원",
              "충청북도": "충북", "충청남도": "충남", "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북",
              "경상남도": "경남", "제주특별자치도": "제주", "전남광주통합특별시": "전남광주"}
# 이름이 바뀐 시도. 바뀌기 전에 폐업한 가게 주소에는 옛 이름이 남아 있을 수 있어 모두 찾는다.
SIDO_OLD = {"강원특별자치도": ["강원도"], "전북특별자치도": ["전라북도"], "전남광주통합특별시": ["광주광역시", "전라남도"]}
CONTEXT = ssl.create_default_context()


def read_env():
    values = {}
    for line in ENV_FILE.read_text("utf-8-sig").splitlines():
        if "=" in line:
            name, value = line.split("=", 1)
            values[name.strip()] = value.strip()
    return values


ENV = read_env()


class QuotaError(RuntimeError):
    """하루 호출 한도에 걸림. 전국 생성은 이때 기다렸다가 다시 시도한다."""


def get_json(url, params, key_param=None, key=None, headers=None):
    query = urllib.parse.urlencode(params, safe="")
    if key_param:
        query += f"&{key_param}=" + (key if "%" in key else urllib.parse.quote(key, safe=""))
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "location-research/1.0", **(headers or {})})
    error = "응답 없음"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=40, context=CONTEXT) as response:
                text = response.read().decode("utf-8", "replace")
            if "LIMITED_NUMBER_OF_SERVICE_REQUESTS" in text:
                raise QuotaError(f"{url.split('/')[-2]} 하루 호출 한도 초과")
            return json.loads(text)
        except urllib.error.HTTPError as err:
            error = f"HTTP {err.code}"
            if err.code == 429:
                raise QuotaError(f"{url.split('/')[-2]} 호출 한도 초과(HTTP 429)") from err
            if err.code < 500:
                break
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as err:
            error = type(err).__name__
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url.split('/')[2]} 호출 실패: {error}")


def confirmed(fetch, empty):
    """이 API들은 가끔 오류 표시 없이 빈 결과를 준다. 비면 잠시 뒤 두 번 더 묻고, 세 번 다 비어야 빈 것으로 본다."""
    for attempt in range(3):
        result = fetch()
        if not empty(result):
            return result
        if attempt < 2:
            time.sleep(3)
    return result


def find_rows(node):
    best = []
    if isinstance(node, list):
        if node and all(isinstance(i, dict) for i in node):
            best = node
        for item in node:
            found = find_rows(item)
            if len(found) > len(best):
                best = found
    elif isinstance(node, dict):
        for value in node.values():
            found = find_rows(value)
            if len(found) > len(best):
                best = found
    return best


def find_total(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in ("totalcount", "total_count"):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    pass
        for value in node.values():
            total = find_total(value)
            if total is not None:
                return total
    elif isinstance(node, list):
        for item in node:
            total = find_total(item)
            if total is not None:
                return total
    return None


def stage(raw_dir, name, fetch):
    path = raw_dir / f"{name}.json"
    if path.exists():
        print(f"건너뜀 {name}")
        return json.loads(path.read_text("utf-8"))
    data = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    temp.replace(path)
    print(f"저장 {name}: {len(data)}건", flush=True)
    return data


# ---------- 용도지역 SHP ----------
def tm5186_to_wgs84(x, y):
    """EPSG:5186(GRS80 중부원점, 가산 200000/600000)을 위경도로 바꾼다. GRS80과 WGS84 차이는 무시한다."""
    a, f = 6378137.0, 1 / 298.257222101
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    lat0, lon0 = math.radians(38), math.radians(127)

    def arc(lat):
        return a * ((1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lat - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * lat)
                    + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * lat) - (35 * e2**3 / 3072) * math.sin(6 * lat))

    mu = (arc(lat0) + (y - 600000.0)) / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    lat1 = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu) + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu) + (1097 * e1**4 / 512) * math.sin(8 * mu))
    s, c, t = math.sin(lat1), math.cos(lat1), math.tan(lat1)
    c1, t1 = ep2 * c * c, t * t
    n1 = a / math.sqrt(1 - e2 * s * s)
    r1 = a * (1 - e2) / (1 - e2 * s * s) ** 1.5
    d = (x - 200000.0) / n1
    lat = lat1 - (n1 * t / r1) * (d * d / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * ep2) * d**4 / 24
                                  + (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * ep2 - 3 * c1 * c1) * d**6 / 720)
    lon = lon0 + (d - (1 + 2 * t1 + c1) * d**3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * ep2 + 24 * t1 * t1) * d**5 / 120) / c
    return math.degrees(lon), math.degrees(lat)


def read_dbf(path):
    with open(path, "rb") as f:
        count, header_size, record_size = struct.unpack("<IHH", f.read(12)[4:12])
        f.seek(32)
        fields = []
        while (block := f.read(32))[0] != 0x0D:
            fields.append((block[:11].split(b"\0")[0].decode("ascii"), block[16]))
        f.seek(header_size)
        for _ in range(count):
            record, pos, row = f.read(record_size), 1, {}
            for name, size in fields:
                row[name] = record[pos:pos + size].split(b"\0")[0].decode("cp949", "replace").strip()
                pos += size
            yield row


def rings_to_polygons(rings):
    """SHP 고리를 [바깥, 구멍...] 다각형으로 묶는다. 바깥 고리는 시계 방향, 구멍은 반시계 방향이다."""
    def area(ring):
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:]))

    def inside(ring, x, y):
        hit, j = False, len(ring) - 1
        for i in range(len(ring)):
            xi, yi, xj, yj = ring[i][0], ring[i][1], ring[j][0], ring[j][1]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                hit = not hit
            j = i
        return hit

    outers = [[r] for r in rings if area(r) < 0]
    for hole in (r for r in rings if area(r) >= 0):
        owner = next((p for p in outers if inside(p[0], *hole[0])), None)
        if owner:
            owner.append(hole)
        else:
            outers.append([hole[::-1]])
    return outers


def zone_shp(label):
    """데이터셋 이름(DBF 첫 행의 A2)으로 전국 SHP를 찾는다. 파일 이름의 번호는 데이터셋 이름과 맞지 않는다."""
    for shp in ZONE_DIR.glob("*/*.shp"):
        first = next(read_dbf(shp.with_suffix(".dbf")), None)
        if first and first.get("A2") == label:
            return shp
    return None


def zone_file(shp, box, keep):
    """전국 SHP에서 box(위경도) 안이고 keep(행)을 만족하는 도형만 GeoJSON 형식으로 꺼낸다."""
    west, south, east, north = box
    features = []
    with open(shp, "rb") as f:
        f.seek(100)
        for row in read_dbf(shp.with_suffix(".dbf")):
            _, length = struct.unpack(">ii", f.read(8))
            content = f.read(length * 2)
            if struct.unpack("<i", content[:4])[0] not in (5, 15, 25) or not keep(row):
                continue
            x0, y0, x1, y1 = struct.unpack("<4d", content[4:36])
            corners = [tm5186_to_wgs84(x, y) for x in (x0, x1) for y in (y0, y1)]
            if max(c[0] for c in corners) < west or min(c[0] for c in corners) > east or max(c[1] for c in corners) < south or min(c[1] for c in corners) > north:
                continue
            parts, points = struct.unpack("<2i", content[36:44])
            starts = list(struct.unpack(f"<{parts}i", content[44:44 + 4 * parts])) + [points]
            xy = struct.unpack(f"<{2 * points}d", content[44 + 4 * parts:44 + 4 * parts + 16 * points])
            rings = [[(xy[2 * i], xy[2 * i + 1]) for i in range(starts[k], starts[k + 1])] for k in range(parts)]
            polygons = [[[[round(v, 7) for v in tm5186_to_wgs84(x, y)] for x, y in ring] for ring in poly] for poly in rings_to_polygons(rings)]
            features.append({"properties": {"uname": row["A6"], "name": row["A8"], "sigungu": row["A4"]},
                             "geometry": {"type": "MultiPolygon", "coordinates": polygons}})
    return features


# ---------- 공공데이터 ----------
def stores_in_dong(codes):
    rows, empty_dongs = {}, []
    for code in codes:
        page = 1
        while True:
            body = confirmed(lambda: get_json(
                "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong",
                {"divId": "adongCd", "key": code, "type": "json", "pageNo": page, "numOfRows": 1000},
                key_param="serviceKey", key=ENV["DATA_GO_KR_KEY"],
            ), lambda b: not find_rows(b.get("body", b)))
            batch = find_rows(body.get("body", body))
            for row in batch:
                rows[row["bizesId"]] = {k: row.get(k) for k in ("bizesId", "bizesNm", "indsMclsNm", "indsSclsNm", "adongCd", "adongNm", "flrNo", "lon", "lat")}
            total = find_total(body)
            if not batch:
                if page == 1:
                    # 새로 생긴 행정동(세종 집현동)은 상가 자료에 코드가 없고 가게는 옛 동 코드로 온다.
                    # 가게는 좌표로 칸에 넣으므로 빠지지 않는다. 그런 동이 많으면 자료 문제로 본다.
                    empty_dongs.append(code)
                    print(f"  상가 {code}: 0곳(세 번 확인, 새 행정동일 수 있음)", flush=True)
                    break
                if total is None or (page - 1) * 1000 < total:
                    raise RuntimeError(f"상가 {code} {page}쪽이 비었는데 전체 {total}건이라 끊김")
                break
            if total is not None and page * 1000 >= total:
                break
            page += 1
        print(f"  상가 {code}: 누적 {len(rows)}", flush=True)
    if len(empty_dongs) > max(1, len(codes) // 10):
        raise RuntimeError(f"상가가 0곳인 행정동이 너무 많음 {len(empty_dongs)}/{len(codes)}: {empty_dongs[:5]}")
    outside = [r for r in rows.values() if str(r.get("adongCd") or "")[:8] not in codes]
    if outside:
        raise RuntimeError(f"요청하지 않은 행정동의 상가 {len(outside)}건: {sorted({str(r.get('adongCd')) for r in outside})[:5]}")
    return list(rows.values())


GENERAL_GU = re.compile(r"^(.+시).+구$")


def region_code(props):
    """지역 id. 일반구(안산시상록구 41271)는 시 코드(41270)로 묶고, 나머지는 시군구 코드 그대로다.
    앞 네 자리만 보면 영동군(43740)과 증평군(43745)처럼 다른 군이 묶이므로 이름도 본다."""
    sgg = props["sgg"]
    return sgg[:4] + "0" if sgg[-1] != "0" and GENERAL_GU.match(props["sggnm"]) else sgg


def region_info(geojson):
    """동 경계에서 지역 코드, 시도, 이름, 인허가 주소 검색어를 읽는다."""
    props = [f["properties"] for f in geojson["features"]]
    codes = {region_code(p) for p in props}
    sidos = {p["sidonm"] for p in props}
    if len(codes) != 1 or len(sidos) != 1:
        raise SystemExit(f"한 지역이 아닙니다: {sorted(codes)} {sorted(sidos)}")
    names = {p["sggnm"] for p in props}
    if len(names) == 1:
        name = names.pop()
    else:
        cities = {GENERAL_GU.match(n).group(1) for n in names}
        if len(cities) != 1:
            raise SystemExit(f"한 지역이 아닙니다: {sorted(names)}")
        name = cities.pop()
    sido = sidos.pop()
    # 세종은 시군구가 없어 주소가 '세종특별자치시 조치원읍 …'이다. 동 경계의 '세종시'를 붙이면 아무것도 안 나온다.
    places = SIDO_OLD.get(sido, [])
    if sido.endswith("특별자치시"):
        terms = [sido] + places
    else:
        terms = [f"{s} {name}" for s in [sido] + places]
    return {"id": codes.pop(), "sido": sido, "sidoShort": SIDO_SHORT.get(sido, sido), "name": name, "terms": terms}


def licenses(dataset, terms, names=(None,), required=False):
    """주소에 검색어(예: '서울특별시 중구')가 든 인허가 행. 시도를 붙여 다른 도시의 같은 이름 구를 막는다.
    names를 주면 상호에 그 말이 든 행만 받는다(API는 한 번에 100행까지라 호출 수를 줄인다)."""
    rows = {}
    for field, region, name in [(f, t, n) for t in terms for f in ("ROAD_NM_ADDR", "LOTNO_ADDR") for n in names]:
        page, seen = 1, 0
        while True:
            params = {"pageNo": page, "numOfRows": 100, "returnType": "json", f"cond[{field}::LIKE]": region}
            if name:
                params["cond[BPLC_NM::LIKE]"] = name
            body = confirmed(lambda: get_json(f"https://apis.data.go.kr/1741000/{dataset}/info", params, key_param="serviceKey", key=ENV["DATA_GO_KR_KEY"]),
                             lambda b: not find_rows(b))
            batch = find_rows(body)
            total = find_total(body)
            seen += len(batch)
            for row in batch:
                rows[row["MNG_NO"]] = row
            if not batch and page > 1 and (total is None or seen < total):
                raise RuntimeError(f"{dataset} '{region}' {page}쪽이 비었는데 전체 {total}건 중 {seen}건만 받음")
            if not batch or (total is not None and seen >= total):
                break
            page += 1
        print(f"  {dataset} {field} '{region}'{f' 상호 {name}' if name else ''}: 응답 {seen}, 누적 {len(rows)}", flush=True)
    # LIKE는 주소 중간도 맞추므로, 주소가 검색어로 시작하는 행만 남긴다(다른 도시 가게가 섞이지 않게).
    kept = [r for r in rows.values() if any((r.get(f) or "").strip().startswith(t) for t in terms for f in ("ROAD_NM_ADDR", "LOTNO_ADDR"))]
    if len(kept) != len(rows):
        print(f"  {dataset}: 주소가 검색어로 시작하지 않는 {len(rows) - len(kept)}건 뺌", flush=True)
    if required and not kept:
        raise RuntimeError(f"{dataset} {terms}: 0건. 검색어가 주소와 맞지 않을 수 있다")
    return kept


def population_rows(code, level, month):
    rows, page = [], 1
    while True:
        body = confirmed(lambda: get_json(
            "https://apis.data.go.kr/1741000/stdgPpltnHhStus/selectStdgPpltnHhStus",
            {"stdgCd": code, "srchFrYm": month, "srchToYm": month, "lv": level, "type": "JSON", "numOfRows": 1000, "pageNo": page},
            key_param="serviceKey", key=ENV["DATA_GO_KR_KEY"],
        ), lambda b: not (b["Response"].get("items") or {}).get("item"))
        items = (body["Response"].get("items") or {}).get("item") or []
        rows += items if isinstance(items, list) else [items]
        total = int(body["Response"]["head"]["totalCount"])
        if not items and page > 1 and len(rows) < total:
            raise RuntimeError(f"인구 {code} {month} {page}쪽이 비었는데 전체 {total}건 중 {len(rows)}건만 받음")
        if not items or len(rows) >= total:
            return rows
        page += 1


def shift_month(month, months):
    index = int(month[:4]) * 12 + int(month[4:]) - 1 + months
    return f"{index // 12}{index % 12 + 1:02d}"


def population(geojson):
    """행정동별 주민등록 인구·세대수. API는 법정동별 통·반 값을 주므로 행정기관코드로 더한다."""
    sgg_codes = sorted({f["properties"]["adm_cd2"][:5] for f in geojson["features"]})
    today = time.localtime()
    latest = shift_month(f"{today.tm_year}{today.tm_mon:02d}", -1)
    for _ in range(6):
        if population_rows(sgg_codes[0] + "00000", 3, latest):
            break
        latest = shift_month(latest, -1)
    else:
        raise RuntimeError(f"최근 6개월 주민등록 인구가 없습니다: {sgg_codes[0]}")
    # 4년 전과 비교한다. API는 2022-10부터 있으므로 그 전이면 2022-10을 쓴다.
    past = max(shift_month(latest, -48), POPULATION_FIRST_MONTH)
    dongs = {}
    for sgg in sgg_codes:
        for month, people_key, households_key in ((latest, "people", "households"), (past, "pastPeople", "pastHouseholds")):
            # 리 코드로 물어도 읍·면 전체가 오므로 읍·면 코드(끝 두 자리 00)로 한 번만 묻는다.
            seen = set()
            totals = population_rows(sgg + "00000", 3, month)
            added = [0, 0]
            for stdg in sorted({row["stdgCd"][:8] + "00" for row in totals}):
                for row in population_rows(stdg, 4, month):
                    key = (row["stdgCd"], row.get("liNm"), row["admmCd"], row["tong"], row["ban"])
                    if key in seen:
                        continue
                    seen.add(key)
                    dong = dongs.setdefault(row["admmCd"], {"name": row["dongNm"], "people": 0, "households": 0, "pastPeople": 0, "pastHouseholds": 0})
                    dong[people_key] += int(row["totNmprCnt"])
                    dong[households_key] += int(row["hhCnt"])
                    added[0] += int(row["totNmprCnt"])
                    added[1] += int(row["hhCnt"])
            # 통·반을 더한 값은 법정동 합계와 같아야 한다. 다르면 중복이나 누락이다(예전 오창읍 230만 명 오류).
            expected = [sum(int(r["totNmprCnt"]) for r in totals), sum(int(r["hhCnt"]) for r in totals)]
            if added != expected:
                raise RuntimeError(f"인구 합계 불일치 {sgg} {month}: 통·반 합 {added}, 법정동 합 {expected}")
        print(f"  인구 {sgg}: 누적 {len(dongs)}개 동, 합계 검사 통과", flush=True)

    # 행정구역이 바뀐 곳(목포시 46110 → 12110)은 4년 전 값이 옛 행정동 코드로 온다. 이름이 같은 지금 동에 붙인다.
    current = {code for code in geojson_codes(geojson)}
    by_name = {}
    for code in current:
        if code in dongs:
            by_name.setdefault(dongs[code]["name"], []).append(code)
    for code in [c for c in dongs if c not in current]:
        old = dongs.pop(code)
        same = by_name.get(old["name"], [])
        if len(same) == 1 and old["people"] == 0:
            dongs[same[0]]["pastPeople"] += old["pastPeople"]
            dongs[same[0]]["pastHouseholds"] += old["pastHouseholds"]
            print(f"  4년 전 인구 옮김: {code} → {same[0]} {old['name']} {old['pastPeople']:,}명")
        else:
            print(f"  경계에 없는 인구 동(버림): {code} {old['name']} 지금 {old['people']:,} 4년 전 {old['pastPeople']:,}")
    missing = sorted(current - set(dongs))
    if missing:
        raise RuntimeError(f"주민등록 인구가 없는 행정동: {missing}")
    return {"latest": latest, "past": past, "dongs": dongs}


def geojson_codes(geojson):
    return [f["properties"]["adm_cd2"] for f in geojson["features"]]


def bounds_of(geojson):
    xs, ys = [], []

    def walk(node):
        if isinstance(node[0], (int, float)):
            xs.append(node[0])
            ys.append(node[1])
        else:
            for child in node:
                walk(child)

    for feature in geojson["features"]:
        walk(feature["geometry"]["coordinates"])
    return (min(xs) - MARGIN_DEG, min(ys) - MARGIN_DEG, max(xs) + MARGIN_DEG, max(ys) + MARGIN_DEG)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    region = sys.argv[1]
    region_dir = ROOT / "데이터" / "지역" / region
    raw_dir = region_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    geojson = json.loads((region_dir / "행정동경계.geojson").read_text("utf-8"))
    info = region_info(geojson)
    sido_names = [info["sido"]] + SIDO_OLD.get(info["sido"], [])
    print(f"지역: {info['sido']} {info['name']} ({info['id']})")
    box = bounds_of(geojson)
    print("수집 범위:", [round(v, 4) for v in box])

    keeps = {"greenbelt": lambda row: row["A6"] == "개발제한구역", "industrial": lambda row: row["A6"] in INDUSTRIAL_KINDS}
    for name, label in ZONE_FILES.items():
        shp = zone_shp(label)
        if shp is None:
            raise SystemExit(f"없음 zone_{name}: {ZONE_DIR}에 '{label}' SHP가 있어야 한다")
        stage(raw_dir, f"zone_{name}", lambda shp=shp, name=name: zone_file(shp, box, keeps.get(name, lambda row: True)))
    stage(raw_dir, "population", lambda: population(geojson))
    codes = sorted(f["properties"]["adm_cd2"][:8] for f in geojson["features"])
    stage(raw_dir, "stores", lambda: stores_in_dong(codes))
    for dataset in LICENSE_DATASETS:
        stage(raw_dir, f"license_{dataset}", lambda dataset=dataset: licenses(
            dataset, info["terms"], SWEET_NAME_TERMS if dataset in NAME_FILTERED else (None,), required=dataset == "bakeries"))
    # 지역 경계 바로 밖의 점포도 거리 계산에 쓰므로 시도 전체를 받는다.
    # 같은 시도의 지역이 여러 개라 시도별로 한 번만 받아 두고 복사한다.
    province = stage(ROOT / "데이터" / "원본" / "대규모점포", info["sido"], lambda: licenses("large_scale_retail_stores", sido_names))
    stage(raw_dir, "license_large_stores", lambda: province)


if __name__ == "__main__":
    try:
        main()
    except QuotaError as err:
        print(f"멈춤: {err}", flush=True)
        sys.exit(3)  # build_all.py가 이 값을 보고 기다렸다가 다시 시도한다

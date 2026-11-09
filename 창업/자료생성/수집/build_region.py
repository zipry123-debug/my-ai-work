"""원자료를 지도용 JSON으로 만든다. 격자는 전국 공통인 EPSG:5179 격자다(칸 200m 또는 100m).

실행: python 수집/build_region.py 41270 지도의_data/regions_폴더 [--cell 100]   (시군구 코드. 폴더는 데이터/지역/41270)
200m는 <시군구 코드>.json, 100m는 <시군구 코드>_100.json에 저장하고 지역 목록 index.json을 갱신한다.
"""
import collections
import csv
import datetime
import json
import math
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import tm5174_to_wgs84  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_region import region_info  # noqa: E402

CELL_SIZES = (200, 100)
CELL_M = 200  # main()에서 --cell 값으로 바꾼다.
TILE_M = 8000  # 화면 격자 보간 조각 크기(칸 크기와 상관없이 8km)
POINT_MARGIN_M = 3000
LOOKBACK_YEARS = 3
SGIS_100M_DIR = ROOT / "데이터" / "원본" / "sgis100m"
AROUND_M = 500
BUS_CSV = ROOT / "데이터" / "원본" / "bus" / "TAGO1020_station_cp949.csv"
SAMPLES = (0.1667, 0.5, 0.8333)  # 칸 하나를 9개 지점으로 나눠 용도지역을 본다.

ZONE_GROUPS = {
    "제1종전용주거지역": "주거", "제2종전용주거지역": "주거", "제1종일반주거지역": "주거", "제2종일반주거지역": "주거",
    "제3종일반주거지역": "주거", "준주거지역": "주거",
    "중심상업지역": "상업", "일반상업지역": "상업", "근린상업지역": "상업", "유통상업지역": "상업",
    "전용공업지역": "공업", "일반공업지역": "공업", "준공업지역": "공업",
    "자연녹지지역": "녹지", "생산녹지지역": "녹지", "보전녹지지역": "보전",
    "자연환경보전지역": "보전", "계획관리지역": "관리", "생산관리지역": "관리", "보전관리지역": "관리", "관리지역": "관리",
    "농림지역": "농림",
}
SWEET_NAME = re.compile(r"케이크|케익|케이커리|베이커리|베이크|제과|빵|디저트|레터링")
STANDARD_DIR = ROOT / "데이터" / "원본" / "공공표준"
# 표준데이터에 없는 서해선 역. 역 이름이나 출구가 붙은 정류장 좌표의 평균으로 위치를 추정한다.
SEOHAE_STATIONS = ("시흥능곡", "시흥시청", "선부", "원시", "달미", "시우")
APARTMENT_STOP = re.compile(r"아파트|APT|\d+단지|자이|푸르지오|힐스테이트|레미안|래미안|e편한|이편한|롯데캐슬|아이파크|주공|더샵|호반|비발디|스위첸|리슈빌|베르디움|아너스빌|데시앙|어울림|꿈에그린|휴먼시아|\d차", re.I)
APARTMENT_STOP_OUT = re.compile(r"어울림센터")
OFFICE_STOP = re.compile(r"시청|구청|행정복지센터|주민센터|보건소|경찰서|파출소|지구대|소방서|안전센터|우체국|세무서|법원|검찰|교육지원청|고용|도서관")
OFFICE_STOP_OUT = re.compile(r"시청역|^우체국사거리")
STOP_SUFFIX = re.compile(r"(\d+동)?(건너편|맞은편|앞|후문|정문|입구|종점|사거리)$")
SAME_PLACE_M = 300
MART_NAME = re.compile(r"마트|홈플러스|코스트코|트레이더스")
MART_NAME_OUT = re.compile(r"에브리데이|익스프레스")


# ---------- EPSG:5179 ----------
A = 6378137.0
F = 1 / 298.257222101
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
K0 = 0.9996
LAT0, LON0 = math.radians(38), math.radians(127.5)
FE, FN = 1000000.0, 2000000.0


def _arc(lat):
    return A * ((1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256) * lat
                - (3 * E2 / 8 + 3 * E2**2 / 32 + 45 * E2**3 / 1024) * math.sin(2 * lat)
                + (15 * E2**2 / 256 + 45 * E2**3 / 1024) * math.sin(4 * lat)
                - (35 * E2**3 / 3072) * math.sin(6 * lat))


M0 = _arc(LAT0)


def to_xy(lat, lon):
    lat, lon = math.radians(lat), math.radians(lon)
    s, c, t = math.sin(lat), math.cos(lat), math.tan(lat)
    n = A / math.sqrt(1 - E2 * s * s)
    T, C, AA = t * t, EP2 * c * c, (lon - LON0) * c
    x = FE + K0 * n * (AA + (1 - T + C) * AA**3 / 6 + (5 - 18 * T + T * T + 72 * C - 58 * EP2) * AA**5 / 120)
    y = FN + K0 * (_arc(lat) - M0 + n * t * (AA * AA / 2 + (5 - T + 9 * C + 4 * C * C) * AA**4 / 24
                                             + (61 - 58 * T + T * T + 600 * C - 330 * EP2) * AA**6 / 720))
    return x, y


def to_latlon(x, y):
    m = M0 + (y - FN) / K0
    mu = m / (A * (1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    lat1 = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu) + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu) + (1097 * e1**4 / 512) * math.sin(8 * mu))
    s, c, t = math.sin(lat1), math.cos(lat1), math.tan(lat1)
    C1, T1 = EP2 * c * c, t * t
    n1 = A / math.sqrt(1 - E2 * s * s)
    r1 = A * (1 - E2) / (1 - E2 * s * s) ** 1.5
    d = (x - FE) / (n1 * K0)
    lat = lat1 - (n1 * t / r1) * (d * d / 2 - (5 + 3 * T1 + 10 * C1 - 4 * C1 * C1 - 9 * EP2) * d**4 / 24
                                  + (61 + 90 * T1 + 298 * C1 + 45 * T1 * T1 - 252 * EP2 - 3 * C1 * C1) * d**6 / 720)
    lon = LON0 + (d - (1 + 2 * T1 + C1) * d**3 / 6 + (5 - 2 * C1 + 28 * T1 - 3 * C1 * C1 + 8 * EP2 + 24 * T1 * T1) * d**5 / 120) / c
    return math.degrees(lat), math.degrees(lon)


LETTERS = "가나다라마바사아"


def sgis_sheet(x, y):
    """SGIS 격자 파일 이름의 도엽 글자. 예: 다사"""
    return f"{LETTERS[int(x // 100000) - 7]}{LETTERS[int(y // 100000) - 13]}"


def parse_100m(code):
    """100m 격자 코드를 (열, 행) 번호로 바꾼다. 번호에 100을 곱하면 칸 서남쪽 좌표(m)다. 예: 다사380250"""
    return (LETTERS.index(code[0]) + 7) * 1000 + int(code[2:5]), (LETTERS.index(code[1]) + 13) * 1000 + int(code[5:8])


# ---------- 도형 ----------
class Shapes:
    """다각형 묶음에서 점이 들어가는 항목을 빠르게 찾는다."""

    def __init__(self, items, bin_deg=0.02):
        self.bin = bin_deg
        self.grid = collections.defaultdict(list)
        for value, geometry in items:
            polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
            for poly in polys:
                outer = poly[0]
                xs, ys = [p[0] for p in outer], [p[1] for p in outer]
                entry = (value, poly, min(xs), min(ys), max(xs), max(ys))
                for ix in range(int(min(xs) // bin_deg), int(max(xs) // bin_deg) + 1):
                    for iy in range(int(min(ys) // bin_deg), int(max(ys) // bin_deg) + 1):
                        self.grid[(ix, iy)].append(entry)

    @staticmethod
    def _ring(ring, lon, lat):
        inside = False
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi, xj, yj = ring[i][0], ring[i][1], ring[j][0], ring[j][1]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside

    def find(self, lat, lon):
        for value, poly, x0, y0, x1, y1 in self.grid.get((int(lon // self.bin), int(lat // self.bin)), ()):
            if x0 <= lon <= x1 and y0 <= lat <= y1 and self._ring(poly[0], lon, lat) and not any(self._ring(h, lon, lat) for h in poly[1:]):
                return value
        return None


def solve_affine(samples):
    """(c, r, 값) 표본에 값 = a + b*c + d*r 을 최소제곱으로 맞춘다."""
    n = len(samples)
    m = [[0.0] * 4 for _ in range(3)]
    for c, r, v in samples:
        row = (1.0, c, r)
        for i in range(3):
            for j in range(3):
                m[i][j] += row[i] * row[j]
            m[i][3] += row[i] * v
    for i in range(3):
        pivot = max(range(i, 3), key=lambda k: abs(m[k][i]))
        m[i], m[pivot] = m[pivot], m[i]
        for k in range(3):
            if k != i:
                factor = m[k][i] / m[i][i]
                for j in range(i, 4):
                    m[k][j] -= factor * m[i][j]
    return [m[i][3] / m[i][i] for i in range(3)] if n else [0, 0, 0]


def zip_name(info):
    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode("cp437").decode("cp949")
    except UnicodeError:
        return info.filename


def read_100m(key, item, sheets):
    """전국 100m 묶음에서 필요한 도엽만 읽어 {(열, 행): 값}으로 돌려준다."""
    values = {}
    for path in sorted(SGIS_100M_DIR.glob("*.zip")):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                match = re.search(rf"2024년_{key}_(..)_100M\.csv$", zip_name(info))
                if not match or match.group(1) not in sheets:
                    continue
                for line in archive.read(info).decode("cp949").splitlines():
                    parts = line.replace('"', "").split(",")
                    if len(parts) == 4 and parts[2] == item:
                        try:
                            values[parse_100m(parts[1])] = int(float(parts[3]))
                        except ValueError:
                            pass
    if not values:
        raise SystemExit(f"{key} 100m 자료를 찾지 못했습니다")
    return values


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    global CELL_M
    args = sys.argv[1:]
    if "--cell" in args:
        at = args.index("--cell")
        CELL_M = int(args[at + 1])
        del args[at:at + 2]
    if CELL_M not in CELL_SIZES:
        raise SystemExit(f"칸 크기는 {CELL_SIZES} 중 하나여야 합니다: {CELL_M}")
    TILE_CELLS = TILE_M // CELL_M
    sub_cells = CELL_M // 100  # 칸 한 변에 들어가는 100m 인구 칸 수
    print(f"칸 크기: {CELL_M}m")
    folder, regions_dir = args[0], Path(args[1])
    region_dir = ROOT / "데이터" / "지역" / folder
    raw_dir = region_dir / "raw"
    today = datetime.date.today()
    cutoff = today.replace(year=today.year - LOOKBACK_YEARS).isoformat()

    def raw(name):
        return json.loads((raw_dir / f"{name}.json").read_text("utf-8"))

    def collected(name):
        return datetime.date.fromtimestamp((raw_dir / f"{name}.json").stat().st_mtime).isoformat()

    # 행정동
    boundary = json.loads((region_dir / "행정동경계.geojson").read_text("utf-8"))
    # 지역 id는 시군구 코드다. 일반구가 있는 시(안산시 41271·41273)는 시 코드(41270)로 묶는다.
    info = region_info(boundary)
    region_id, sido, region = info["id"], info["sidoShort"], info["name"]
    population = raw("population")
    pop_months = [f"{m[:4]}-{m[4:]}" for m in (population["past"], population["latest"])]
    dongs, dong_items = [], []
    for feature in boundary["features"]:
        name = feature["properties"]["adm_nm"].split()[-1]
        pop = population["dongs"].get(feature["properties"]["adm_cd2"])
        if pop is None:
            raise SystemExit(f"주민등록 인구 없음: {feature['properties']['adm_cd2']} {name}")
        # 4년 전 값이 없으면(행정동이 새로 생기거나 나뉨) 감소율을 모른다. 0%로 두지 않는다.
        decline = round((pop["pastPeople"] - pop["people"]) / pop["pastPeople"] * 100, 1) if pop["pastPeople"] else (0.0 if not pop["people"] else None)
        if decline is None:
            print(f"4년 전 인구 없음: {feature['properties']['adm_cd2']} {name} (감소율 미확인)")
        dong_items.append((len(dongs), feature["geometry"]))
        dongs.append({"name": name, "gu": feature["properties"]["sggnm"].replace(region, ""), "households": pop["households"],
                      "people": pop["people"], "decline": decline})
    dong_shapes = Shapes(dong_items)

    # 격자 범위
    xs, ys = [], []
    for _, geometry in dong_items:
        polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for poly in polys:
            for lon, lat in poly[0]:
                x, y = to_xy(lat, lon)
                xs.append(x)
                ys.append(y)
    gx0, gx1 = int(min(xs) // CELL_M), int(max(xs) // CELL_M)
    gy0, gy1 = int(min(ys) // CELL_M), int(max(ys) // CELL_M)

    # 용도지역과 제외 구역
    # 관리·농림·자연환경보전 파일은 받은 지역에서만 쓴다. 없으면 그 땅은 '없음'으로 본다.
    zone_layers = [n for n in ("zone_urban", "zone_manage", "zone_farm", "zone_nature") if (raw_dir / f"{n}.json").exists()]
    print("용도지역 파일:", zone_layers)
    zone_items = []
    for layer in zone_layers:
        for feature in raw(layer):
            if feature.get("geometry"):
                zone_items.append((feature["properties"].get("uname") or "", feature["geometry"]))
    # '도시지역'처럼 세부 용도가 없는 도형이 세부 도형과 겹치면 세부 도형을 먼저 찾게 한다.
    zones = Shapes(sorted(zone_items, key=lambda item: item[0] not in ZONE_GROUPS))
    # 전국 파일 이름 끝의 날짜(예: AL_D124_00_20261009)가 기준일이다.
    zone_dates = sorted(p.name[-8:] for p in (ROOT / "데이터" / "원본" / "용도지역").glob("AL_*") if p.is_dir())
    zone_date = f"{zone_dates[0][:4]}-{zone_dates[0][4:6]}-{zone_dates[0][6:]}" if zone_dates else "미확인"
    green_belt = Shapes([("개발제한구역", f["geometry"]) for f in raw("zone_greenbelt") if f.get("geometry")])
    # 단지 이름이 빈 곳이 많아 이름이 없으면 단지 종류를 쓴다.
    damdan = Shapes([(f"{f['properties']['name'] or f['properties']['uname']}|{f['properties']['uname']}", f["geometry"]) for f in raw("zone_industrial") if f.get("geometry")])

    # 상가
    store_count = collections.Counter()
    for store in raw("stores"):
        try:
            x, y = to_xy(float(store["lat"]), float(store["lon"]))
        except (TypeError, ValueError):
            continue
        store_count[(int(x // CELL_M), int(y // CELL_M))] += 1

    # 100m 격자 인구·가구 (코드집 항목: to_in_001 총인구, to_ga_001 총가구)
    # 지역 범위보다 1km 넓게 본다(500m 안 가구를 세려면 옆 도엽도 필요).
    sheets = {sgis_sheet(x, y) for x in range(gx0 * CELL_M - 1000, (gx1 + 1) * CELL_M + 1001, 500)
              for y in range(gy0 * CELL_M - 1000, (gy1 + 1) * CELL_M + 1001, 500)}
    people_100 = read_100m("인구", "to_in_001", sheets)
    households_100 = read_100m("가구", "to_ga_001", sheets)
    print("100m 칸 수(읽은 도엽):", len(people_100), len(households_100))
    reach = AROUND_M // 100

    # 칸
    cells, zone_names, zone_index, damdan_stats = [], [], {}, collections.defaultdict(collections.Counter)
    used_100m = collections.Counter()  # 100m 인구 칸이 두 칸에 중복으로 들어가지 않았는지 검사한다.
    for gy in range(gy1, gy0 - 1, -1):
        for gx in range(gx0, gx1 + 1):
            x_mid, y_mid = (gx + 0.5) * CELL_M, (gy + 0.5) * CELL_M
            lat, lon = to_latlon(x_mid, y_mid)
            dong = dong_shapes.find(lat, lon)
            if dong is None:
                continue
            counts = collections.Counter()
            for fx in SAMPLES:
                for fy in SAMPLES:
                    la, lo = to_latlon((gx + fx) * CELL_M, (gy + fy) * CELL_M)
                    counts[ZONE_GROUPS.get(zones.find(la, lo), "없음")] += 1
            main_zone = zones.find(lat, lon) or ""
            majority = counts.most_common(1)[0][0]
            if main_zone not in zone_index:
                zone_index[main_zone] = len(zone_names)
                zone_names.append(main_zone)
            home_share = counts["주거"] + counts["상업"]
            belt = green_belt.find(lat, lon)
            dan = damdan.find(lat, lon)
            if dan:
                damdan_stats[dan][majority] += 1
            ix0, iy0 = gx * sub_cells, gy * sub_cells
            parts = [(ix0 + i, iy0 + j) for i in range(sub_cells) for j in range(sub_cells)]
            used_100m.update(parts)
            pop = sum(people_100.get(key, 0) for key in parts)
            hh = sum(households_100.get(key, 0) for key in parts)
            around = 0
            mid_ix, mid_iy = x_mid / 100, y_mid / 100
            for i in range(int(mid_ix) - reach, int(mid_ix) + reach + 1):
                for j in range(int(mid_iy) - reach, int(mid_iy) + reach + 1):
                    if math.hypot(i + 0.5 - mid_ix, j + 0.5 - mid_iy) * 100 <= AROUND_M:
                        around += households_100.get((i, j), 0)
            cells.append({"gx": gx, "gy": gy, "dong": dong, "zone": zone_index[main_zone], "majority": majority,
                          "homeShare": home_share, "belt": bool(belt), "dan": dan.split("|")[0] if dan else "",
                          "stores": store_count.get((gx, gy), 0), "pop": pop, "hh": hh, "around": around})

    print("칸 수:", len(cells))
    if len({(c["gx"], c["gy"]) for c in cells}) != len(cells):
        raise SystemExit("같은 칸 번호가 두 번 나옴")
    doubled = [key for key, n in used_100m.items() if n > 1]
    if doubled:
        raise SystemExit(f"100m 인구 칸이 여러 칸에 중복 집계됨: {len(doubled)}개, 예 {doubled[:3]}")
    print("다수 용도:", collections.Counter(c["majority"] for c in cells).most_common())
    print("산단별 칸의 다수 용도:")
    for name, counter in sorted(damdan_stats.items(), key=lambda kv: -sum(kv[1].values())):
        print(" ", name, sum(counter.values()), counter.most_common(5))
    by_dong = collections.Counter()
    for cell in cells:
        by_dong[cell["dong"]] += cell["pop"]
    print(f"동별 인구 비교(100m 합, 2024 / 행안부 주민등록, {pop_months[1]}):")
    for index, dong in enumerate(dongs):
        print(f"  {dong['name']}: {by_dong[index]:,} / {dong['people']:,}")
    print("합:", sum(by_dong.values()), "/", sum(d["people"] for d in dongs))
    # 두 자료는 시점과 기준이 달라 조금 다르다. 30% 넘게 차이 나면 중복이나 누락을 의심한다.
    grid_total, registered = sum(by_dong.values()), sum(d["people"] for d in dongs)
    if not registered or not 0.7 <= grid_total / registered <= 1.3:
        raise SystemExit(f"인구 합계 차이가 큼: 100m 격자 {grid_total:,} / 주민등록 {registered:,}")
    if not cells:
        raise SystemExit("칸이 하나도 없음")
    print("인구 0인 칸:", sum(1 for c in cells if c["pop"] == 0), "다수 용도별 평균 인구:", {m: round(sum(c["pop"] for c in cells if c["majority"] == m) / max(1, sum(1 for c in cells if c["majority"] == m)), 1) for m in {c["majority"] for c in cells}})
    around_values = sorted(c["around"] for c in cells if c["homeShare"] > 0 and not c["belt"])
    print("주거·상업 칸의 500m 안 가구 분위수:", [around_values[int(len(around_values) * q)] for q in (0.1, 0.25, 0.5, 0.75, 0.9)])

    # 제외·보류
    hold_counts = collections.Counter()
    for cell in cells:
        reason = ""
        if cell["belt"]:
            reason = "개발제한구역"
        elif cell["majority"] == "보전":
            reason = "보전지역"
        elif cell["majority"] == "공업":
            reason = "공업지역"
        elif cell["dan"] and cell["homeShare"] == 0:
            reason = f"산업단지({cell['dan']})"
        cell["hold"] = reason
        hold_counts[reason.split("(")[0]] += 1
    print("보류 사유:", hold_counts.most_common())

    # 지점 거리 계산에 쓸 범위
    near = set()
    reach = POINT_MARGIN_M // 1000 + 1
    for cell in cells:
        kx, ky = cell["gx"] * CELL_M // 1000, cell["gy"] * CELL_M // 1000
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                near.add((kx + dx, ky + dy))

    def is_near(lat, lon):
        x, y = to_xy(lat, lon)
        return (int(x // 1000), int(y // 1000)) in near

    def standard(file, keep, name_key):
        result, latest = [], ""
        for row in json.loads((STANDARD_DIR / file).read_text("utf-8")):
            try:
                lat, lon = float(row["LATITUDE"]), float(row["LONGITUDE"])
            except (TypeError, ValueError):
                continue
            if is_near(lat, lon) and keep(row):
                result.append({"lat": round(lat, 6), "lon": round(lon, 6), "name": row[name_key]})
                latest = max(latest, row.get("REFERENCE_DATE") or "")
        return result, latest

    bus, bus_date = [], ""
    with open(BUS_CSV, encoding="cp949", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            try:
                lat, lon = float(row["위도"]), float(row["경도"])
            except ValueError:
                continue
            if is_near(lat, lon):
                bus.append({"lat": round(lat, 6), "lon": round(lon, 6), "name": row["정류장명"]})
                bus_date = row["정보수집일"] or bus_date

    def stops_named(pattern, excluded):
        """이름이 맞는 정류장을 장소로 쓴다. 같은 이름이 가까이 있으면 건너편이 아닌 쪽을 하나만 남긴다."""
        result = []
        for stop in sorted(bus, key=lambda s: ("건너편" in s["name"] or "맞은편" in s["name"], s["name"])):
            name = re.sub(r"^\(임시\)|\((마을|미정차)\)$", "", stop["name"])
            part = next((p for p in name.split(".") if pattern.search(p) and not excluded.search(p)), None)
            if not part:
                continue
            part = STOP_SUFFIX.sub("", part) or part
            x, y = to_xy(stop["lat"], stop["lon"])
            if not any(r["name"] == part and math.hypot(x - r["x"], y - r["y"]) < SAME_PLACE_M for r in result):
                result.append({"lat": stop["lat"], "lon": stop["lon"], "name": part, "x": x, "y": y})
        return [{k: r[k] for k in ("lat", "lon", "name")} for r in result]

    subway, station_seen = [], set()
    standard_subway, subway_date = standard("역_15013205.json", lambda row: True, "STATN_NM")
    for point in standard_subway:
        point["name"] = point["name"] if point["name"].endswith("역") else point["name"] + "역"
        if point["name"] not in station_seen:
            station_seen.add(point["name"])
            subway.append(point)
    seohae = []
    for station in SEOHAE_STATIONS:
        if station + "역" in station_seen:
            continue
        pattern = re.compile(rf"^{station}역(\d+번출구)?(\.|$)")
        found = [s for s in bus if pattern.search(s["name"])]
        if not found:
            continue  # 지도 범위 밖의 역
        subway.append({"lat": round(sum(s["lat"] for s in found) / len(found), 6), "lon": round(sum(s["lon"] for s in found) / len(found), 6), "name": station + "역"})
        seohae.append(station)
    parking, parking_date = standard("주차장_15012896.json", lambda row: row.get("PRKPLCE_SE") == "공영", "PRKPLCE_NM")
    schools, school_date = standard("학교_15021148.json", lambda row: row.get("OPER_STTUS") == "운영", "SCHOOL_NM")

    # 경쟁점과 폐업은 옆 지역 것도 센다. 대전처럼 구가 나뉜 도시는 구 경계 근처 칸이 길 건너 옆 구 가게를 놓치기 때문이다.
    # 자료를 이미 받아 둔 옆 지역만 쓴다(API를 다시 부르지 않는다). 가게는 지역마다 주소·행정동으로 나눠 받아 겹치지 않는다.
    def load(source, name):
        return json.loads((source / f"{name}.json").read_text("utf-8"))

    neighbours = []
    for other in sorted((ROOT / "데이터" / "지역").iterdir()):
        if other.name == folder or not other.name.isdigit() or not (other / "raw" / "rival_cake.json").exists():
            continue
        if any(is_near(shop["lat"], shop["lon"]) for shop in load(other / "raw", "rival_cake")):
            neighbours.append(other)
    rivals, rival_unknown, closed, closed_other = [], [], [], []
    for source in [raw_dir] + [n / "raw" for n in neighbours]:
        before = len(rivals) + len(rival_unknown) + len(closed)
        for shop in load(source, "rival_cake"):
            if not is_near(shop["lat"], shop["lon"]):
                continue
            point = {"lat": shop["lat"], "lon": shop["lon"], "name": shop["name"]}
            if shop["status"] == "판매":
                rivals.append({**point, "source": shop["basis"]})
            elif shop["status"] == "미확인":
                rival_unknown.append(point)

        for dataset, target, label in (("bakeries", closed, "제과점영업"), ("rest_cafes", closed_other, "휴게음식점"), ("instant_food_processors", closed_other, "즉석판매제조가공업")):
            missing = 0
            for row in load(source, f"license_{dataset}"):
                date = (row.get("CLSBIZ_YMD") or "")[:10]
                if row.get("SALS_STTS_NM") != "폐업" or date < cutoff:
                    continue
                if dataset != "bakeries" and not SWEET_NAME.search(row.get("BPLC_NM") or ""):
                    continue
                try:
                    lat, lon = tm5174_to_wgs84(float(row["CRD_INFO_X"]), float(row["CRD_INFO_Y"]))
                except (TypeError, ValueError):
                    missing += 1
                    continue
                if is_near(lat, lon):
                    target.append({"lat": round(lat, 6), "lon": round(lon, 6), "name": row.get("BPLC_NM") or "", "type": label, "date": date})
            print(f"{label}: 최근 {LOOKBACK_YEARS}년 폐업 집계 후 누적 제과 {len(closed)}, 기타 {len(closed_other)}, 좌표 없음 {missing}")
        if source != raw_dir:
            print(f"옆 지역 {source.parent.name}: 경쟁점·폐업 {len(rivals) + len(rival_unknown) + len(closed) - before}곳 더함")
    neighbour_names = []
    for n in neighbours:
        other = region_info(json.loads((n / "행정동경계.geojson").read_text("utf-8")))
        neighbour_names.append(other["name"] if other["name"].startswith(other["sidoShort"]) else f"{other['sidoShort']} {other['name']}")

    marts = []
    for row in raw("license_large_stores"):
        # 롯데마트처럼 쇼핑센터로 등록된 곳이 있어 상호도 함께 본다.
        name = row.get("BPLC_NM") or ""
        is_mart = (row.get("BZSTAT_SE_NM") == "대형마트" or MART_NAME.search(name)) and not MART_NAME_OUT.search(name)
        if not is_mart or row.get("SALS_STTS_NM") != "영업/정상":
            continue
        try:
            lat, lon = tm5174_to_wgs84(float(row["CRD_INFO_X"]), float(row["CRD_INFO_Y"]))
        except (TypeError, ValueError):
            continue
        if is_near(lat, lon):
            marts.append({"lat": round(lat, 6), "lon": round(lon, 6), "name": row.get("BPLC_NM") or ""})

    data = {
        "rival": rivals, "rivalUnknown": rival_unknown, "closed": closed, "closedOther": closed_other, "subway": subway, "bus": bus,
        "parking": parking,
        "mart": marts,
        "school": schools,
        "office": stops_named(OFFICE_STOP, OFFICE_STOP_OUT),
        "apartment": stops_named(APARTMENT_STOP, APARTMENT_STOP_OUT),
    }
    print("지점 수:", {k: len(v) for k, v in data.items()})

    # 화면용 격자: 열은 동쪽, 행은 남쪽으로 증가한다.
    col0, row0 = min(c["gx"] for c in cells), max(c["gy"] for c in cells)
    cols = max(c["gx"] for c in cells) - col0 + 1
    rows = row0 - min(c["gy"] for c in cells) + 1
    samples_lat, samples_lon = [], []
    for cell in cells:
        for corner_c, corner_r in ((0, 0), (1, 1)):
            c = cell["gx"] - col0 + corner_c
            r = row0 - cell["gy"] + corner_r
            lat, lon = to_latlon((col0 + c) * CELL_M, (row0 + 1 - r) * CELL_M)
            samples_lat.append((c, r, lat))
            samples_lon.append((c, r, lon))
    lat_fit, lon_fit = solve_affine(samples_lat), solve_affine(samples_lon)
    # 격자가 지도 좌표와 살짝 어긋나므로, 조각마다 네 모서리 값으로 보간해 위치 오차를 줄인다.
    tile_rows, tile_cols = math.ceil(rows / TILE_CELLS), math.ceil(cols / TILE_CELLS)
    nodes = [[[round(v, 7) for v in to_latlon((col0 + j * TILE_CELLS) * CELL_M, (row0 + 1 - i * TILE_CELLS) * CELL_M)]
              for j in range(tile_cols + 1)] for i in range(tile_rows + 1)]

    def interpolate(c, r):
        j, i = min(int(c // TILE_CELLS), tile_cols - 1), min(int(r // TILE_CELLS), tile_rows - 1)
        u, v = c / TILE_CELLS - j, r / TILE_CELLS - i
        return tuple((1 - v) * ((1 - u) * nodes[i][j][k] + u * nodes[i][j + 1][k]) + v * ((1 - u) * nodes[i + 1][j][k] + u * nodes[i + 1][j + 1][k]) for k in (0, 1))

    worst = 0.0
    for (c, r, lat), (_, _, lon) in zip(samples_lat, samples_lon):
        est_lat, est_lon = interpolate(c, r)
        x1, y1 = to_xy(lat, lon)
        x2, y2 = to_xy(est_lat, est_lon)
        worst = max(worst, math.hypot(x1 - x2, y1 - y2))
    print(f"화면 격자 근사의 최대 오차: {worst:.1f}m")

    lats = [p[2] for p in samples_lat]
    lons = [p[2] for p in samples_lon]
    result = {
        "id": region_id, "sido": sido, "name": region, "builtAt": today.isoformat(),
        "grid": {"cellM": CELL_M, "crs": "EPSG:5179", "col0": col0, "row0": row0, "cols": cols, "rows": rows, "lat": lat_fit, "lon": lon_fit, "tileCells": TILE_CELLS, "nodes": nodes, "maxErrorM": round(worst, 1)},
        "bounds": {"south": min(lats), "north": max(lats), "west": min(lons), "east": max(lons)},
        "dongs": dongs, "zones": zone_names,
        # [행, 열, 동, 용도지역, 주거·상업 표본 수(0~9), 보류 사유 번호, 업소 수, 칸 인구, 칸 가구, 500m 안 가구]
        "holdReasons": [""] + sorted({c["hold"] for c in cells if c["hold"]}),
        "cells": [],
        "data": data,
        "sources": [
            {"name": "행정동 경계", "by": "본 데이터는 통계청 통계지리정보서비스(SGIS, https://sgis.kostat.go.kr)에서 공공누리 제1유형으로 개방한 행정동 경계를 가공한 것이며(가공: vuski/admdongkor, https://github.com/vuski/admdongkor), CC BY 4.0(https://creativecommons.org/licenses/by/4.0/)으로 배포됩니다. 이 지도에서는 " + region + " 범위만 잘라 칸 배정에 썼습니다", "date": "2026-10-01"},
            {"name": "동별 인구·세대", "by": f"행정안전부 주민등록 인구 및 세대현황(감소율은 {pop_months[0]}과 비교)", "date": pop_months[1] + " 말"},
            {"name": "100m 격자 인구·가구", "by": "국가데이터처 SGIS(값이 5 미만이면 0 또는 5로 대체, 최대 ±7 노이즈)", "date": "2024"},
            {"name": "용도지역·개발제한구역·산업단지", "by": "국토교통부 용도지역지구정보(브이월드 다운로드)", "date": zone_date + " 기준"},
            {"name": "상가 업소", "by": "소상공인시장진흥공단 상가(상권)정보", "date": collected("stores") + " 수집"},
            {"name": "폐업", "by": "행정안전부 인허가", "date": collected("license_bakeries") + " 수집"},
            {"name": "버스 정류장", "by": "국토교통부(TAGO)", "date": bus_date},
            {"name": "지하철역", "by": "전국도시철도역사정보표준데이터", "date": subway_date},
            *([{"name": f"서해선 역 {len(seohae)}곳", "by": "버스 정류장 이름으로 추정한 위치(TAGO)", "date": bus_date}] if seohae else []),
            {"name": "공영주차장", "by": "전국주차장정보표준데이터", "date": parking_date},
            {"name": "학교", "by": "전국초중등학교위치표준데이터", "date": school_date},
            {"name": "아파트·공공기관", "by": "버스 정류장 이름으로 추정한 위치(TAGO)", "date": bus_date},
            {"name": "대형마트", "by": "행정안전부 인허가(대규모점포)", "date": collected("license_large_stores") + " 수집"},
            {"name": "경쟁점 후보", "by": "소상공인시장진흥공단 상가정보, 행정안전부 인허가", "date": collected("stores") + " 수집"},
            *([{"name": "옆 지역 경쟁점·폐업", "by": "자료를 만든 옆 지역(" + ", ".join(neighbour_names) + ")의 가게도 거리 안이면 셈. 자료가 없는 옆 지역 가게는 빠짐", "date": today.isoformat()}] if neighbours else [{"name": "옆 지역 경쟁점·폐업", "by": "옆 지역 자료가 없어 지역 안 가게만 셈", "date": today.isoformat()}]),
            {"name": "케이크 판매 여부", "by": "상가·인허가 자료의 상호와 업종 규칙, 공정거래위원회 가맹정보 브랜드 목록(주요상품명)으로 자동 추정", "date": collected("rival_cake") + " 판정"},
        ],
    }
    hold_index = {reason: i for i, reason in enumerate(result["holdReasons"])}
    for cell in cells:
        result["cells"].append([row0 - cell["gy"], cell["gx"] - col0, cell["dong"], cell["zone"], cell["homeShare"], hold_index[cell["hold"]], cell["stores"], cell["pop"], cell["hh"], cell["around"]])

    regions_dir.mkdir(parents=True, exist_ok=True)
    output = regions_dir / (f"{region_id}.json" if CELL_M == 200 else f"{region_id}_{CELL_M}.json")
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print(f"저장: {output} {output.stat().st_size:,} bytes")

    # 첫 화면의 지역 목록. 같은 id는 새 값으로 바꾼다.
    index_path = regions_dir / "index.json"
    index = json.loads(index_path.read_text("utf-8")) if index_path.exists() else {"regions": []}
    entries = {r["id"]: r for r in index["regions"]}
    # bounds: 지도가 화면 근처 지역만 골라 불러오는 데 쓴다.
    # cellSizes: 이 지역에 만들어 둔 칸 크기. 화면은 고른 크기 파일이 있는 지역만 불러온다.
    old = entries.get(region_id, {})
    sizes = sorted(set(old.get("cellSizes", [200] if CELL_M != 200 and old else [])) | {CELL_M}, reverse=True)
    entry = {"id": region_id, "sido": sido, "name": region, "builtAt": today.isoformat(), "bounds": result["bounds"], "cellSizes": sizes}
    if CELL_M != 200 and old:
        entry["builtAt"], entry["bounds"] = old["builtAt"], old["bounds"]  # 목록의 날짜·범위는 200m 기준을 유지한다.
    entries[region_id] = entry
    index["regions"] = sorted(entries.values(), key=lambda r: r["id"])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1), "utf-8")
    print(f"지역 목록: {len(index['regions'])}곳")


if __name__ == "__main__":
    main()

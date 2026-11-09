"""전국 행정동 경계에서 한 지역만 잘라 저장한다. 표준 라이브러리만 쓴다.

예: python -I extract_region.py 원본.geojson 41270 데이터/지역/41270/행정동경계.geojson
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_region import region_code  # noqa: E402  일반구는 시 코드로 묶는다


def bounds(features):
    xs, ys = [], []

    def walk(node):
        if isinstance(node[0], (int, float)):
            xs.append(node[0])
            ys.append(node[1])
        else:
            for child in node:
                walk(child)

    for feature in features:
        walk(feature["geometry"]["coordinates"])
    return [min(xs), min(ys), max(xs), max(ys)]


def main():
    source, code, target = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    if not re.fullmatch(r"\d{5}", code):
        raise SystemExit("시군구 코드 5자리를 넣으세요(예: 마포구 11440, 안산시 41270)")
    data = json.loads(source.read_text("utf-8"))
    features = [f for f in data["features"] if region_code(f["properties"]) == code]
    if not features:
        raise SystemExit(f"'{code}'에 맞는 행정동이 없습니다")

    target.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "type": "FeatureCollection",
        "name": f"{data['name']}_{code}",
        "crs": data["crs"],
        "source": {"file": source.name, "origin": "vuski/admdongkor (CC BY 4.0), SGIS 행정동 경계 보정본"},
        "features": features,
    }
    target.write_text(json.dumps(result, ensure_ascii=False), "utf-8")

    print(f"전국 {len(data['features'])}개 중 {len(features)}개 추출, {target.stat().st_size:,} bytes")
    print("범위(서,남,동,북):", [round(v, 5) for v in bounds(features)])
    for feature in sorted(features, key=lambda f: f["properties"]["adm_cd2"]):
        props = feature["properties"]
        print(props["adm_cd2"], props["adm_nm"])


if __name__ == "__main__":
    main()

"""설정.env의 키가 작동하는지 소량 호출로 확인한다. 키와 요청 주소는 출력하지 않는다.

실행: python 수집/check_keys.py
"""
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "설정.env"
# 안산역 부근. 응답 형식 확인용이다.
LON, LAT = 126.7886, 37.3275
VWORLD_DOMAIN = "http://127.0.0.1"
TIMEOUT = 25


def read_env():
    values = {}
    for line in ENV_FILE.read_text("utf-8-sig").splitlines():
        if "=" in line:
            name, value = line.split("=", 1)
            values[name.strip()] = value.strip()
    return values


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
            if key.lower() in ("totalcount", "total_count", "total"):
                if isinstance(value, (int, str)):
                    return value
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


def call(label, url, params, secrets, headers=None, key_param=None, key=None):
    query = urllib.parse.urlencode(params, safe="")
    if key_param:
        encoded = key if "%" in key else urllib.parse.quote(key, safe="")
        query += f"&{key_param}={encoded}"
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "location-research/1.0", **(headers or {})})

    def clean(text):
        for secret in secrets:
            if secret:
                text = text.replace(secret, "***").replace(urllib.parse.quote(secret, safe=""), "***")
        return text

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=ssl.create_default_context()) as response:
            status, raw = response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        print(f"[실패] {label}: 연결 오류 {type(err).__name__}")
        return

    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[실패] {label}: HTTP {status}, JSON 아님: {clean(raw[:200])!r}")
        return

    rows = find_rows(body)
    if status == 200 and rows:
        fields = list(rows[0].get("properties", rows[0]).keys()) if isinstance(rows[0].get("properties"), dict) else list(rows[0].keys())
        print(f"[성공] {label}: 전체 {find_total(body)}, 받은 행 {len(rows)}")
        print(f"       필드: {', '.join(fields)}")
    else:
        print(f"[확인 필요] {label}: HTTP {status}, 행 없음: {clean(json.dumps(body, ensure_ascii=False)[:300])}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    env = read_env()
    data_key, kakao_key, vworld_key = env.get("DATA_GO_KR_KEY", ""), env.get("KAKAO_REST_KEY", ""), env.get("VWORLD_KEY", "")
    secrets = [data_key, kakao_key, vworld_key]

    call(
        "카카오 키워드 검색",
        "https://dapi.kakao.com/v2/local/search/keyword.json",
        {"query": "레터링케이크", "x": LON, "y": LAT, "radius": 5000, "size": 3},
        secrets,
        headers={"Authorization": f"KakaoAK {kakao_key}"},
    )
    call(
        "상가정보 반경 조회",
        "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius",
        {"radius": 300, "cx": LON, "cy": LAT, "type": "json", "pageNo": 1, "numOfRows": 3},
        secrets,
        key_param="serviceKey",
        key=data_key,
    )
    for dataset, name in (("bakeries", "제과점영업"), ("rest_cafes", "휴게음식점"), ("instant_food_processors", "즉석판매제조가공업")):
        call(
            f"인허가 {name}",
            f"https://apis.data.go.kr/1741000/{dataset}/info",
            {"pageNo": 1, "numOfRows": 2, "returnType": "json", "cond[ROAD_NM_ADDR::LIKE]": "안산시"},
            secrets,
            key_param="serviceKey",
            key=data_key,
        )
    for layer, name in (("LT_C_UQ111", "용도지역(도시지역)"), ("LT_C_DAMDAN", "산업단지 경계"), ("LT_C_UD801", "개발제한구역")):
        call(
            f"브이월드 {name}",
            "https://api.vworld.kr/req/data",
            {
                "request": "GetFeature",
                "data": layer,
                "geomFilter": f"BOX({LON - 0.05},{LAT - 0.05},{LON + 0.05},{LAT + 0.05})",
                "size": 2,
                "geometry": "false",
                "domain": VWORLD_DOMAIN,
            },
            secrets,
            key_param="key",
            key=vworld_key,
        )


if __name__ == "__main__":
    main()

"""외부 API 호출과 캐시. 인증키는 로그나 오류 메시지, 캐시 이름에 남기지 않는다."""
import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_SECONDS = 7 * 24 * 3600
TIMEOUT = 25
LICENSE_PAGE_SIZE = 100
LICENSE_MAX_PAGES = 200
STORE_PAGE_SIZE = 1000
STORE_MAX_PAGES = 20

SEMAS_URL = "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"
MOIS_URL = "https://apis.data.go.kr/1741000/{dataset}/info"
KAKAO_ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

DATASETS = {
    "bakeries": "제과점영업",
    "rest_cafes": "휴게음식점",
    "instant_food_processors": "즉석판매제조가공업",
}


class SourceError(Exception):
    pass


class MissingKey(SourceError):
    pass


def _find_rows(node):
    """응답 구조가 API마다 달라, 가장 긴 객체 배열을 데이터 행으로 본다."""
    best = []
    if isinstance(node, list):
        if node and all(isinstance(i, dict) for i in node):
            best = node
        for item in node:
            found = _find_rows(item)
            if len(found) > len(best):
                best = found
    elif isinstance(node, dict):
        for value in node.values():
            found = _find_rows(value)
            if len(found) > len(best):
                best = found
    return best


def _find_total(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in ("totalcount", "total_count"):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return None
        for value in node.values():
            total = _find_total(value)
            if total is not None:
                return total
    elif isinstance(node, list):
        for item in node:
            total = _find_total(item)
            if total is not None:
                return total
    return None


def _service_error(body):
    if isinstance(body, dict):
        wrapper = body.get("OpenAPI_ServiceResponse")
        if wrapper:
            header = wrapper.get("cmmMsgHeader", {})
            return f"{header.get('returnAuthMsg', '')} ({header.get('errMsg', '')})"
        header = body.get("header") or body.get("response", {}).get("header")
        if isinstance(header, dict):
            code = str(header.get("resultCode", "00"))
            if code == "03":  # 데이터 없음은 오류가 아니다.
                return None
            if code not in ("00", "0", "200"):
                return f"{header.get('resultMsg', '오류')} (코드 {code})"
    return None


class LiveClient:
    demo = False

    def __init__(self, data_key, kakao_key):
        self.data_key = (data_key or "").strip()
        self.kakao_key = (kakao_key or "").strip()
        self.ssl = ssl.create_default_context()

    # ---------- 공통 ----------
    def _cache_path(self, url):
        CACHE_DIR.mkdir(exist_ok=True)
        return CACHE_DIR / (hashlib.sha256(url.encode()).hexdigest() + ".json")

    def _get(self, base, params, headers=None, key_param=None, cached=True):
        query = urllib.parse.urlencode(params, safe="")
        public_url = f"{base}?{query}"
        path = self._cache_path(public_url)
        if cached and path.exists() and time.time() - path.stat().st_mtime < CACHE_SECONDS:
            return json.loads(path.read_text("utf-8"))

        url = public_url
        if key_param:
            # 포털의 인코딩 키(%포함)와 디코딩 키 모두 받아들인다.
            key = self.data_key if "%" in self.data_key else urllib.parse.quote(self.data_key, safe="")
            url = f"{public_url}&{key_param}={key}"
        request = urllib.request.Request(url, headers={"User-Agent": "location-research/1.0", **(headers or {})})

        last_error = "응답 없음"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=TIMEOUT, context=self.ssl) as response:
                    raw = response.read().decode("utf-8", "replace")
                break
            except urllib.error.HTTPError as err:
                raw = err.read().decode("utf-8", "replace")
                if err.code < 500:
                    break
                last_error = f"HTTP {err.code}"
            except (urllib.error.URLError, TimeoutError, OSError) as err:
                last_error = type(err).__name__
            time.sleep(1.5 * (attempt + 1))
        else:
            raise SourceError(f"연결 실패: {last_error}")

        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"<(?:returnAuthMsg|errMsg|resultMsg)>([^<]+)<", raw)
            raise SourceError(match.group(1) if match else "JSON이 아닌 응답을 받았습니다") from None

        error = _service_error(body)
        if error:
            raise SourceError(error)
        if isinstance(body, dict) and body.get("errorType"):
            raise SourceError(f"{body.get('errorType')}: {body.get('message', '')}")
        path.write_text(json.dumps(body, ensure_ascii=False), "utf-8")
        return body

    def _kakao(self, url, params):
        if not self.kakao_key:
            raise MissingKey("카카오 REST API 키가 없습니다")
        try:
            return self._get(url, params, headers={"Authorization": f"KakaoAK {self.kakao_key}"})
        except SourceError as err:
            # 카카오는 오류 메시지에 받은 키를 그대로 돌려주므로 지운다.
            raise SourceError(f"카카오 API 오류: {str(err).replace(self.kakao_key, '***')}") from None

    def _require_data_key(self):
        if not self.data_key:
            raise MissingKey("공공데이터포털 인증키가 없습니다")

    # ---------- 위치 ----------
    def geocode(self, query):
        """주소를 먼저 찾고, 없으면 장소명으로 찾는다."""
        for url in (KAKAO_ADDRESS_URL, KAKAO_KEYWORD_URL):
            body = self._kakao(url, {"query": query, "size": 5})
            documents = body.get("documents") or []
            if documents:
                doc = documents[0]
                return {
                    "lat": float(doc["y"]),
                    "lon": float(doc["x"]),
                    "address": doc.get("address_name") or query,
                    "place": doc.get("place_name") or "",
                    "matches": int(body.get("meta", {}).get("total_count", len(documents))),
                }
        return None

    def places(self, keyword, lat, lon, radius):
        """카카오는 검색어당 최대 45건만 주므로 잘린 경우 truncated로 알린다."""
        result, total = [], 0
        for page in range(1, 4):
            body = self._kakao(
                KAKAO_KEYWORD_URL,
                {"query": keyword, "x": lon, "y": lat, "radius": radius, "sort": "distance", "size": 15, "page": page},
            )
            meta = body.get("meta", {})
            total = int(meta.get("total_count", 0))
            for doc in body.get("documents", []):
                result.append(
                    {
                        "id": doc.get("id"),
                        "name": doc.get("place_name", ""),
                        "category": doc.get("category_name", ""),
                        "address": doc.get("road_address_name") or doc.get("address_name", ""),
                        "lat": float(doc["y"]),
                        "lon": float(doc["x"]),
                        "distance": int(doc.get("distance") or 0),
                        "url": doc.get("place_url", ""),
                    }
                )
            if meta.get("is_end", True):
                break
        return {"rows": result, "total": total}

    # ---------- 공공데이터 ----------
    def stores(self, lat, lon, radius):
        self._require_data_key()
        rows, total = [], None
        for page in range(1, STORE_MAX_PAGES + 1):
            body = self._get(
                SEMAS_URL,
                {
                    "radius": radius,
                    "cx": lon,
                    "cy": lat,
                    "indsLclsCd": "I2",
                    "type": "json",
                    "pageNo": page,
                    "numOfRows": STORE_PAGE_SIZE,
                },
                key_param="serviceKey",
            )
            batch = _find_rows(body)
            rows.extend(batch)
            total = _find_total(body)
            if not batch or (total is not None and len(rows) >= total):
                break
        return {"rows": rows, "total": total}

    def licenses(self, dataset, region, name_like=None):
        """시군구 단위로 내려받아 캐시하고, 반경 판정은 호출한 쪽에서 한다."""
        self._require_data_key()
        rows, total = [], None
        for page in range(1, LICENSE_MAX_PAGES + 1):
            params = {
                "pageNo": page,
                "numOfRows": LICENSE_PAGE_SIZE,
                "returnType": "json",
                "cond[ROAD_NM_ADDR::LIKE]": region,
            }
            if name_like:
                params["cond[BPLC_NM::LIKE]"] = name_like
            body = self._get(MOIS_URL.format(dataset=dataset), params, key_param="serviceKey")
            batch = _find_rows(body)
            rows.extend(batch)
            total = _find_total(body)
            if not batch or (total is not None and len(rows) >= total):
                break
        return {"rows": rows, "total": total, "truncated": total is not None and len(rows) < total}

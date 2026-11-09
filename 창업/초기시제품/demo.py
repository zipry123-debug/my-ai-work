"""화면 점검용 가짜 데이터. 실제 상권과 무관하며, 데모로 켜면 화면에 항상 표시된다."""
import math
import random
import zlib
from datetime import date, timedelta

CENTERS = [
    (37.5665, 126.9780),
    (37.5400, 127.0700),
    (37.4900, 127.0300),
    (37.5200, 126.9000),
]


def _around(rng, lat, lon, max_m):
    distance = rng.uniform(40, max_m)
    angle = rng.uniform(0, 2 * math.pi)
    return (
        lat + distance * math.cos(angle) / 111320,
        lon + distance * math.sin(angle) / (111320 * math.cos(math.radians(lat))),
    )


class DemoClient:
    demo = True

    def _rng(self, *parts):
        return random.Random(zlib.crc32("|".join(map(str, parts)).encode()))

    def geocode(self, query):
        lat, lon = CENTERS[zlib.crc32(query.encode()) % len(CENTERS)]
        return {"lat": lat, "lon": lon, "address": f"데모시 가상구 {query}", "place": "", "matches": 1}

    def places(self, keyword, lat, lon, radius):
        rng = self._rng("places", keyword, lat)
        rows = []
        for i in range(rng.randint(2, 9)):
            p_lat, p_lon = _around(rng, lat, lon, radius)
            distance = round(math.hypot((p_lat - lat) * 111320, (p_lon - lon) * 111320 * math.cos(math.radians(lat))))
            rows.append(
                {
                    "id": f"{keyword}-{i}",
                    "name": f"가짜 레터링 공방 {keyword[0]}{i + 1}",
                    "category": "음식점 > 간식 > 제과,베이커리",
                    "address": "데모시 가상구 가짜로 1",
                    "lat": p_lat,
                    "lon": p_lon,
                    "distance": distance,
                    "url": "",
                }
            )
        return {"rows": rows, "total": len(rows)}

    def stores(self, lat, lon, radius):
        rng = self._rng("stores", lat, radius)
        rows = []
        for i in range(rng.randint(6, 24)):
            s_lat, s_lon = _around(rng, lat, lon, radius)
            rows.append(
                {
                    "bizesNm": f"가짜 빵집 {i + 1}",
                    "indsSclsNm": "빵/도넛",
                    "rdnmAdr": "데모시 가상구 가짜로 2",
                    "lat": s_lat,
                    "lon": s_lon,
                }
            )
        return {"rows": rows, "total": rng.randint(150, 600)}

    def licenses(self, dataset, region, name_like=None):
        # 후보지 좌표는 geocode가 주므로, 가게는 네 중심 전체에 흩어 놓아 반경 필터가 동작하게 한다.
        rng = self._rng("lic", dataset, name_like)
        rows = []
        today = date.today()
        for i in range(120 if dataset == "bakeries" else 24):
            c_lat, c_lon = CENTERS[i % len(CENTERS)]
            lat, lon = _around(rng, c_lat, c_lon, 2500)
            opened = today - timedelta(days=rng.randint(100, 3000))
            closed_flag = rng.random() < 0.45
            closed = opened + timedelta(days=rng.randint(60, 1500)) if closed_flag else None
            if closed and closed > today:
                closed = today - timedelta(days=rng.randint(1, 30))
            dong = "가나다라"[i % 4] + "동"
            rows.append(
                {
                    "BPLC_NM": f"가짜 {'케이크' if name_like or i % 5 == 0 else '제과'} {i + 1}",
                    "SALS_STTS_NM": "폐업" if closed else "영업/정상",
                    "LCPMT_YMD": opened.strftime("%Y%m%d"),
                    "CLSBIZ_YMD": closed.strftime("%Y%m%d") if closed else "",
                    "ROAD_NM_ADDR": f"데모시 가상구 가짜로 {i + 1} ({dong})",
                    "lat": lat,
                    "lon": lon,
                }
            )
        return {"rows": rows, "total": len(rows), "truncated": False}

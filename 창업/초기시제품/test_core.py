import unittest
from datetime import date

import analysis
import core
import sources
from demo import DemoClient


def lic(**kw):
    base = {"BPLC_NM": "가게", "SALS_STTS_NM": "영업/정상", "LCPMT_YMD": "20200101", "lat": 37.5, "lon": 127.0}
    base.update(kw)
    return core.normalize_license(base, "제과점영업")


class Coordinates(unittest.TestCase):
    # 기준값은 pyproj(EPSG:5174 -> EPSG:4326)로 계산했다.
    REFERENCE = [
        (200000, 450000, 37.552268, 127.000788),
        (206000, 445000, 37.5071992, 127.0686482),
        (210000, 441000, 37.4711249, 127.113834),
        (190000, 450000, 37.5522131, 126.8876205),
        (205000, 430000, 37.372054, 127.057238),
        (385000, 185000, 35.1471615, 129.0308441),
        (160000, 190000, 35.2084282, 126.5615228),
        (340000, 280000, 36.01034, 128.553667),
    ]

    def test_matches_pyproj_within_two_metres(self):
        for x, y, lat, lon in self.REFERENCE:
            got_lat, got_lon = core.tm5174_to_wgs84(x, y)
            self.assertLess(core.distance_m(got_lat, got_lon, lat, lon), 2.0)


class Normalize(unittest.TestCase):
    def test_unknown_close_field_found_by_pattern(self):
        row = core.normalize_license({"BPLC_NM": "a", "SOME_CLOSE_DATE": "2024-05-01"}, "x")
        self.assertEqual(row["closed"], date(2024, 5, 1))
        self.assertTrue(row["is_closed"])

    def test_tm_coordinates_are_converted(self):
        row = core.normalize_license({"BPLC_NM": "a", "CRD_INFO_X": "200000", "CRD_INFO_Y": "450000"}, "x")
        self.assertAlmostEqual(row["lat"], 37.55, delta=0.05)
        self.assertAlmostEqual(row["lon"], 127.0, delta=0.05)

    def test_blank_coordinates_stay_empty(self):
        row = core.normalize_license({"BPLC_NM": "a", "CRD_INFO_X": "", "CRD_INFO_Y": ""}, "x")
        self.assertIsNone(row["lat"])

    def test_missing_fields_are_reported_not_zero(self):
        rows = [core.normalize_license({"UNKNOWN": "1"}, "x")]
        self.assertIn("인허가일자", core.mapping_problems(rows))


class Summary(unittest.TestCase):
    today = date(2026, 11, 2)

    def test_window_and_median(self):
        rows = [
            lic(LCPMT_YMD="20240101", CLSBIZ_YMD="20250101", SALS_STTS_NM="폐업"),
            lic(LCPMT_YMD="20230101", CLSBIZ_YMD="20250101", SALS_STTS_NM="폐업"),
            lic(LCPMT_YMD="20100101", CLSBIZ_YMD="20150101", SALS_STTS_NM="폐업"),  # 3년 밖
            lic(LCPMT_YMD="20260101"),
        ]
        s = core.license_summary(rows, self.today)
        self.assertEqual((s["active"], s["closed"]), (1, 2))
        self.assertEqual(s["opened"], 2)  # 2023-01-01 개업은 3년 밖
        self.assertAlmostEqual(s["median_months"], 18, delta=0.5)

    def test_closed_status_without_date_is_counted_separately(self):
        s = core.license_summary([lic(SALS_STTS_NM="폐업")], self.today)
        self.assertEqual((s["active"], s["closed"], s["closed_undated"]), (0, 0, 1))

    def test_warnings(self):
        self.assertEqual(core.warnings_for({"closed": 0, "opened": 0}), [])
        self.assertEqual(len(core.warnings_for({"closed": 3, "opened": 1})), 2)
        self.assertEqual(len(core.warnings_for({"closed": 1, "opened": 5})), 0)


class Address(unittest.TestCase):
    def test_region(self):
        self.assertEqual(core.region_from_address("서울 송파구 잠실동 40"), "송파구")
        self.assertEqual(core.region_from_address("경기 성남시 분당구 정자동"), "성남시 분당구")
        self.assertEqual(core.region_from_address("경기 화성시 동탄면"), "화성시")
        self.assertEqual(core.region_from_address("세종특별자치시 한솔동 1"), "세종특별자치시")

    def test_dong(self):
        self.assertEqual(core.dong_of({"road": "서울 송파구 올림픽로 1 (잠실동)", "lot": ""}), "잠실동")
        self.assertEqual(core.dong_of({"road": "서울 송파구 올림픽로 1 (잠실동, 아파트)", "lot": ""}), "잠실동")
        self.assertEqual(core.dong_of({"road": "", "lot": "서울특별시 송파구 잠실동 40-1"}), "잠실동")
        self.assertIsNone(core.dong_of({"road": "서울 어딘가 1", "lot": ""}))


class Responses(unittest.TestCase):
    def test_rows_found_in_any_shape(self):
        body = {"response": {"body": {"items": {"item": [{"a": 1}, {"a": 2}]}, "totalCount": "2"}}}
        self.assertEqual(len(sources._find_rows(body)), 2)
        self.assertEqual(sources._find_total(body), 2)

    def test_key_error_detected(self):
        body = {"OpenAPI_ServiceResponse": {"cmmMsgHeader": {"errMsg": "SERVICE_KEY_IS_NULL", "returnAuthMsg": "거부"}}}
        self.assertIn("SERVICE_KEY_IS_NULL", sources._service_error(body))

    def test_no_data_code_is_not_error(self):
        self.assertIsNone(sources._service_error({"header": {"resultCode": "03", "resultMsg": "NODATA"}}))


class Failures(unittest.TestCase):
    def test_missing_keys_give_unknown_not_zero(self):
        result = analysis.analyze(sources.LiveClient("", ""), "잠실동", 500)
        self.assertEqual(result["state"], "failed")
        self.assertIn("카카오", result["message"])

    def test_kakao_error_hides_key(self):
        client = sources.LiveClient("", "secret-key")

        def echo_key(*args, **kwargs):
            raise sources.SourceError("wrong appKey(secret-key) format")

        client._get = echo_key
        with self.assertRaises(sources.SourceError) as caught:
            client.geocode("잠실동")
        self.assertNotIn("secret-key", str(caught.exception))

    def test_missing_data_key_keeps_other_sections(self):
        client = DemoClient()
        client.stores = sources.LiveClient("", "").stores
        result = analysis.analyze(client, "데모", 500)
        self.assertEqual(result["stores"]["state"], "missing_key")
        self.assertEqual(result["competitors"]["state"], "ok")

    def test_demo_runs_end_to_end(self):
        result = analysis.analyze(DemoClient(), "데모", 1000, date(2026, 11, 2))
        self.assertEqual(result["licenses"]["state"], "ok")
        self.assertGreater(len(result["licenses"]["dongs"]), 0)


if __name__ == "__main__":
    unittest.main()

"""전국 시군구를 차례로 만든다. 이미 만든 지역은 건너뛰므로 멈춘 뒤 다시 실행해도 된다.

실행: python 수집/build_all.py            (전국)
      python 수집/build_all.py 12110 11140 (그 지역만)
칸 크기 200m(<코드>.json)와 100m(<코드>_100.json)를 모두 만든다.
기록: 데이터/전국생성_기록.txt (지역마다 결과 한 줄), 데이터/전국생성_로그/<코드>.txt (자세한 출력)
하루 호출 한도에 걸리면 1시간 기다렸다가 같은 지역부터 다시 한다. 다른 오류는 기록하고 다음 지역으로 넘어간다.
"""
import collections
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_region import region_code  # noqa: E402
SOURCE = ROOT / "데이터" / "원본" / "admdongkor" / "HangJeongDong_ver20261001.geojson"
DIST_REGIONS = ROOT.parent / "ansan-location-map-handoff" / "ansan-location-map-handoff" / "dist" / "data" / "regions"
LOCAL_REGIONS = ROOT / "data" / "regions"
RECORD = ROOT / "데이터" / "전국생성_기록.txt"
LOG_DIR = ROOT / "데이터" / "전국생성_로그"
QUOTA_EXIT = 3
WAIT_S = 3600
MAX_WAIT_S = 3 * 24 * 3600


def run(log, *args):
    with log.open("a", encoding="utf-8") as out:
        out.write(f"\n$ {' '.join(args)}\n")
        out.flush()
        result = subprocess.run([sys.executable, *args], cwd=ROOT, stdout=out, stderr=subprocess.STDOUT,
                                env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return result.returncode


def last_lines(log, count=3):
    lines = [line for line in log.read_text("utf-8", "replace").splitlines() if line.strip()]
    return " / ".join(lines[-count:])


def record(code, status, detail=""):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M} {code} {status} {detail}".rstrip()
    print(line, flush=True)
    with RECORD.open("a", encoding="utf-8") as out:
        out.write(line + "\n")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads(SOURCE.read_text("utf-8"))
    groups = collections.defaultdict(list)
    for feature in data["features"]:
        groups[region_code(feature["properties"])].append(feature)
    codes = sys.argv[1:] or sorted(groups)  # 코드를 주면 그 지역만 한다(시험용)
    print(f"전국 {len(codes)}곳", flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    waited = 0
    done = failed = 0
    for number, code in enumerate(codes, 1):
        have_200 = (DIST_REGIONS / f"{code}.json").exists()
        if have_200 and (DIST_REGIONS / f"{code}_100.json").exists():
            done += 1
            continue
        log = LOG_DIR / f"{code}.txt"
        boundary = ROOT / "데이터" / "지역" / code / "행정동경계.geojson"
        steps = [
            ("동 경계", ["수집/extract_region.py", str(SOURCE), code, str(boundary)]),
            ("수집", ["수집/collect_region.py", code]),
            ("경쟁점 판정", ["수집/classify_rivals.py", code]),
            ("지도 자료", ["수집/build_region.py", code, str(DIST_REGIONS)]),
            ("지도 자료 100m", ["수집/build_region.py", code, str(DIST_REGIONS), "--cell", "100"]),
        ]
        if have_200:  # 200m는 이미 있고 100m만 없으면 100m만 만든다.
            steps = steps[-1:]
        print(f"[{number}/{len(codes)}] {code} 시작", flush=True)
        error = None
        for label, args in steps:
            if label == "동 경계" and boundary.exists():
                continue
            while True:
                code_out = run(log, *args)
                if code_out != QUOTA_EXIT:
                    break
                if waited >= MAX_WAIT_S:
                    record(code, "중단", "호출 한도로 3일 넘게 기다림")
                    return
                record(code, "대기", f"호출 한도: {last_lines(log, 1)}. 1시간 뒤 다시 시도")
                time.sleep(WAIT_S)
                waited += WAIT_S
            if code_out != 0:
                error = f"{label} 실패: {last_lines(log)}"
                break
        if error:
            failed += 1
            record(code, "실패", error)
            continue
        waited = 0
        done += 1
        for name in (f"{code}.json", f"{code}_100.json", "index.json"):
            shutil.copy2(DIST_REGIONS / name, LOCAL_REGIONS / name)
        record(code, "완료", last_lines(log, 1))
    record("전체", "끝", f"완료 {done}곳, 실패 {failed}곳")


if __name__ == "__main__":
    main()

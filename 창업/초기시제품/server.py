"""입지 조사 프로그램 로컬 서버. 파이썬 표준 라이브러리만 쓰며 이 컴퓨터에서만 접속된다."""
import argparse
import json
import re
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import analysis
from demo import DemoClient
from sources import LiveClient

ROOT = Path(__file__).parent
ENV_FILE = ROOT / "설정.env"
INDEX = ROOT / "index.html"
MAP_PAGE = ROOT / "지도.html"
KEY_NAMES = ("DATA_GO_KR_KEY", "KAKAO_REST_KEY")
MAX_CANDIDATES = 10
RADII = (300, 500, 1000, 2000)


def read_env():
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text("utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                name, value = line.split("=", 1)
                values[name.strip()] = value.strip()
    return values


def write_env(values):
    lines = [f"{name}={values.get(name, '')}" for name in KEY_NAMES]
    ENV_FILE.write_text("\n".join(lines) + "\n", "utf-8")


class Handler(BaseHTTPRequestHandler):
    demo = False
    allowed_hosts = ()

    def log_message(self, *args):  # 요청 주소를 콘솔에 남기지 않는다.
        pass

    def _json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _trusted(self):
        # 다른 웹사이트가 브라우저를 통해 이 서버를 호출하지 못하게 막는다.
        if self.headers.get("Host") not in self.allowed_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or re.sub(r"^https?://", "", origin) in self.allowed_hosts

    def _status(self):
        env = read_env()
        return {
            "demo": self.demo,
            "today": date.today().isoformat(),
            "keys": {name: bool(env.get(name)) for name in KEY_NAMES},
        }

    def do_GET(self):
        if not self._trusted():
            return self._json(403, {"error": "허용되지 않은 접속입니다"})
        path = self.path.split("?", 1)[0]  # /map?region=mapo 처럼 지역을 붙여 연다.
        if path in ("/", "/index.html", "/map"):
            data = (MAP_PAGE if path == "/map" else INDEX).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        elif re.fullmatch(r"/data/regions/[a-z0-9_-]+\.json", self.path):
            target = ROOT / self.path.lstrip("/")
            if not target.exists():
                return self._json(404, {"error": "없는 지역입니다"})
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/api/status":
            self._json(200, self._status())
        else:
            self._json(404, {"error": "없는 주소입니다"})

    def do_POST(self):
        if not self._trusted():
            return self._json(403, {"error": "허용되지 않은 접속입니다"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._json(400, {"error": "요청 형식이 잘못되었습니다"})

        if self.path == "/api/keys":
            env = read_env()
            for name in KEY_NAMES:
                value = str(body.get(name) or "").strip()
                if value:  # 빈칸은 기존 키를 유지한다.
                    env[name] = re.sub(r"\s", "", value)
            write_env(env)
            return self._json(200, self._status())

        if self.path == "/api/analyze":
            queries = [str(q).strip() for q in body.get("candidates", []) if str(q).strip()]
            queries = list(dict.fromkeys(queries))
            if not queries:
                return self._json(400, {"error": "후보지를 한 곳 이상 입력하세요"})
            if len(queries) > MAX_CANDIDATES:
                return self._json(400, {"error": f"후보지는 한 번에 {MAX_CANDIDATES}곳까지 가능합니다"})
            radius = body.get("radius")
            if radius not in RADII:
                return self._json(400, {"error": "반경 값이 잘못되었습니다"})
            env = read_env()
            client = DemoClient() if self.demo else LiveClient(env.get("DATA_GO_KR_KEY"), env.get("KAKAO_REST_KEY"))
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda q: analysis.analyze(client, q, radius), queries))
            return self._json(200, {"demo": self.demo, "results": results})

        self._json(404, {"error": "없는 주소입니다"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--demo", action="store_true", help="가짜 데이터로 화면만 점검")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    Handler.demo = args.demo
    Handler.allowed_hosts = (f"127.0.0.1:{args.port}", f"localhost:{args.port}")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"입지 조사 프로그램 실행 중: {url}  (끄려면 이 창을 닫으세요)", flush=True)
    if not args.no_browser:
        webbrowser.open(f"{url}/map")
    server.serve_forever()


if __name__ == "__main__":
    main()

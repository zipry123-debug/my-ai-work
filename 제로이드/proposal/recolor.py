"""파랑 과다 정리: 강조색을 잉크로, 연파랑 배경을 회색으로, 피부타입은 회색 단계, 보습·진정은 파랑+앰버 (검사 통과 값)."""
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_recolor.html")
s = f.read_text(encoding="utf-8")
R = [
    ("--barrier:#2340c9; --barrier-soft:#e8edfc;", "--barrier:#0d0f14; --barrier-soft:#f3f5f8;", 1),
    ("--barrier:#8197ff;--barrier-soft:#1c2347;", "--barrier:#eef0f4;--barrier-soft:#171a21;", 2),
    ("--moist:#2a46b0; --calm:#7fb0ff;", "--moist:#3d63d6; --calm:#d4952a;", 1),
    ("--moist:#6f8cf2;--calm:#3b5cc4;", "--moist:#6b88ee;--calm:#b9822a;", 2),
    ("--skin1:#1b2a6b;--skin2:#3d63d6;--skin3:#86a8f5;", "--skin1:#2b303b;--skin2:#6b7280;--skin3:#a9afba;", 1),
    ("--skin1:#c3d0ff;--skin2:#7d9bff;--skin3:#3a58b8;", "--skin1:#e3e6ec;--skin2:#9aa1ad;--skin3:#5a606c;", 2),
    (".sk2{background:var(--skin2);color:#fff}", ".sk2{background:var(--skin2);color:var(--on-dark)}", 1),
]
for a, b, n in R:
    c = s.count(a)
    print(c, "/", n, a[:40])
    assert c == n, a
    s = s.replace(a, b)
f.write_text(s, encoding="utf-8")

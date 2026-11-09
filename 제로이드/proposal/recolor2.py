"""뮤트 팔레트 적용 (validate_palette 통과 값): 강조 딥 틸, 퍼소나 슬레이트블루·로즈·오커·라벤더, 보습·진정 소프트블루·샌드, 피부타입 틸 3단계."""
import shutil
from pathlib import Path

D = Path(__file__).parent
f = D / "index.html"
shutil.copy(f, D / "index_before_recolor2.html")
s = f.read_text(encoding="utf-8")
R = [
    ("  --barrier:#0d0f14; --barrier-soft:#f3f5f8;\n", "  --barrier:#1f7a72; --barrier-soft:#e4f2ef;   /* 강조: 딥 틸 / 민트 */\n", 1),
    ("  --pa:#2f5bea; --pa-soft:#edf2ff;   /* A 장벽 회복: 블루 */", "  --pa:#4a72d1; --pa-soft:#edf1fb;   /* A 장벽 회복: 슬레이트 블루 */", 1),
    ("  --pb:#e03e48; --pb-soft:#fdeef0;   /* B 트러블: 레드 */", "  --pb:#d5616c; --pb-soft:#fbedee;   /* B 트러블: 로즈 */", 1),
    ("  --pc:#0e9a7f; --pc-soft:#e6f6f2;   /* C 메이크업: 그린 */", "  --pc:#c4932c; --pc-soft:#faf3e3;   /* C 메이크업: 오커 */", 1),
    ("  --pe:#8b4fd8; --pe-soft:#f4edfd;   /* D 건조·휴대: 퍼플 */", "  --pe:#8f72cf; --pe-soft:#f3effb;   /* D 건조·휴대: 라벤더 */", 1),
    ("  --moist:#3d63d6; --calm:#d4952a;   /* 데이터 전용: 보습(네이비) / 진정(스카이) */", "  --moist:#5b7fd6; --calm:#d9a441;   /* 데이터 전용: 보습(소프트 블루) / 진정(샌드) */", 1),
    ("--barrier:#eef0f4;--barrier-soft:#171a21;", "--barrier:#5cc2b5;--barrier-soft:#12302c;", 2),
    ("--pa:#7d9bff;--pa-soft:#1a2244;--pb:#ff7f87;--pb-soft:#3b1c21;--pc:#3fcfb2;--pc-soft:#10302a;--pe:#c29cff;--pe-soft:#2a1f42;",
     "--pa:#6585d8;--pa-soft:#1a2240;--pb:#c75a6c;--pb-soft:#361c22;--pc:#a69233;--pc-soft:#2f2a14;--pe:#9078cc;--pe-soft:#261f3d;", 2),
    ("--moist:#6b88ee;--calm:#b9822a;", "--moist:#7090e0;--calm:#b38331;", 2),
    ("--skin1:#2b303b;--skin2:#6b7280;--skin3:#a9afba;", "--skin1:#1f5f59;--skin2:#3f9a8f;--skin3:#7ab5ab;", 1),
    ("--skin1:#e3e6ec;--skin2:#9aa1ad;--skin3:#5a606c;", "--skin1:#c5ebe5;--skin2:#6fc1b5;--skin3:#2f7d73;", 2),
]
for a, b, n in R:
    c = s.count(a)
    print(c, "/", n, a.strip()[:44])
    assert c == n, a
    s = s.replace(a, b)
f.write_text(s, encoding="utf-8")

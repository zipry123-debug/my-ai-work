"""퍼소나 E → D 표기 변경 (보이는 글자만)."""
from pathlib import Path

f = Path(__file__).parent / "index.html"
s = f.read_text(encoding="utf-8")
pairs = [
    ('<span class="L">E</span>', '<span class="L">D</span>'),
    ("E 건조", "D 건조"),
    ("A·B·C·E", "A·B·C·D"),
    ('href="#pe"', 'href="#pd"'),
    ('id="pe"', 'id="pd"'),
    ("<!-- E -->", "<!-- D -->"),
]
for a, b in pairs:
    print(a, "->", b, s.count(a))
    s = s.replace(a, b)
f.write_text(s, encoding="utf-8")

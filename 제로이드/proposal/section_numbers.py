"""섹션 라벨(.tag)을 큰 번호 헤더(.sec-no)로 교체하고 01~08로 재번호."""
from pathlib import Path

f = Path(__file__).parent / "index.html"
s = f.read_text(encoding="utf-8")
MAP = [
    ('<span class="tag">Summary</span>', "01", "Summary", "요약"),
    ('<span class="tag">01 · Why now</span>', "02", "Why now", "왜 지금"),
    ('<span class="tag">02 · Strength</span>', "03", "Strength", "브랜드 강점"),
    ('<span class="tag">03 · Customer data</span>', "04", "Customer data", "고객 데이터"),
    ('<span class="tag">04 · Persona</span>', "05", "Persona", "퍼소나"),
    ('<span class="tag">05 · Pop-up plan</span>', "06", "Pop-up plan", "팝업 운영안"),
    ('<span class="tag">06 · Risk</span>', "07", "Risk", "리스크"),
    ('<span class="tag">07 · Next</span>', "08", "Next", "지표와 다음 단계"),
]
for old, no, en, ko in MAP:
    new = f'<div class="sec-no"><b>{no}</b><span><em>{en}</em>{ko}</span></div>'
    print(old, s.count(old))
    s = s.replace(old, new)
f.write_text(s, encoding="utf-8")

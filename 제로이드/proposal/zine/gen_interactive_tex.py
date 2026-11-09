"""인터랙티브 버전 전용 조각: 페르소나 탭 카드 5장(찢김 모양이 모두 다름)."""
from zine_assets import piece

for i, (k, col) in enumerate([("a", "white"), ("b", "white"), ("c", "white"), ("d", "white"), ("e", "paper")]):
    print(piece(f"t_card_{k}", 1560, 720, col, 4000 + i * 23, "trbl", 14))

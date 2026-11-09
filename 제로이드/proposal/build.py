"""index.html의 img/*.jpg를 data URI로 넣어 단일 파일 제안서를 만든다."""
import base64, re
from pathlib import Path

D = Path(__file__).parent
src = (D / "index.html").read_text(encoding="utf-8")
cache = {}


def inline(m):
    p = m.group(1)
    if p not in cache:
        cache[p] = "data:image/jpeg;base64," + base64.b64encode((D / p).read_bytes()).decode()
    return f'src="{cache[p]}"'


out = re.sub(r'src="(img/[^"]+)"', inline, src)
dst = D / "제로이드_무신사뷰티_성수팝업_제안서.html"
dst.write_text(out, encoding="utf-8")
print(dst.name, round(len(out) / 1024), "KB", len(cache), "images")

# 아티팩트용: 문서 골격 태그 제거 + 실습용 표기(실제 기업 명의로 보이지 않게)
NOTICE = ('<p class="src" style="padding-block:10px;border-bottom:1px solid var(--line)">'
          '교육 실습 과제로 작성한 가상 입점 제안서입니다. 제로이드(네오팜)·무신사와 무관하며 실제 제안이 아닙니다. '
          '수치와 리뷰는 공개된 공식 홈페이지·올리브영 페이지에서 수집했습니다.</p>')
art = out
art = re.sub(r"<!doctype html>\s*<html[^>]*>\s*<head>\s*", "", art, flags=re.I)
art = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>\s*', "", art)
art = re.sub(r"</head>\s*<body>\s*", "", art)
art = re.sub(r"\s*</body>\s*</html>\s*$", "\n", art)
art = art.replace("<span>제로이드 영업 MD</span>", "<span>실습 과제 · 영업 MD 직무 실습</span>")
art = art.replace('<main class="wrap">', '<main class="wrap">\n' + NOTICE, 1)
art = art.replace('<span class="eyebrow src">출처</span>',
                  '<span class="eyebrow src">출처</span>\n  <p class="src">· 본 문서는 교육 실습용 가상 제안서로, 언급된 기업의 공식 문서가 아닙니다.</p>', 1)
(D / "artifact.html").write_text(art, encoding="utf-8")
print("artifact.html", round(len(art) / 1024), "KB")

"""conti.json(대사·장면의 단일 원본)을 사람이 읽는 conti.md로 바꾸고, 기본 규칙을 검사한다.

사용법:
    python render_conti.py output/날짜_주제/conti.json

검사 항목: 사실마다 출처 2개 이상, 컷당 말풍선 3개 이하, 말풍선 두 줄 이하, 알 수 없는 type, 빈 칸.
"""
import json
import sys
from pathlib import Path

TYPES = {"speech": "말풍선", "thought": "속마음", "narration": "내레이션", "info": "정보 박스", "title": "표지 제목"}
MAX_CUTS = 10
MAX_BUBBLES = 3


def main():
    if len(sys.argv) != 2:
        sys.exit("사용법: python render_conti.py <conti.json>")
    src = Path(sys.argv[1])
    d = json.loads(src.read_text(encoding="utf-8"))
    warns = []
    md = [f"# {d.get('title', '')}", ""]
    md += [f"- 형식: {d.get('format', '')}", f"- 날짜: {d.get('date', '')}", f"- 컷 수: {len(d['cuts'])}", ""]
    if len(d["cuts"]) > MAX_CUTS:
        warns.append(f"컷이 {len(d['cuts'])}개 (최대 {MAX_CUTS})")

    md += ["## 컷별 콘티", ""]
    for i, cut in enumerate(d["cuts"], 1):
        md.append(f"### 컷 {i} · {cut.get('role', '')} (`{cut['image']}`)")
        for key, label in (("scene", "장면"), ("bubble_area", "말풍선 자리")):
            if not cut.get(key):
                warns.append(f"컷 {i}: '{label}'이 비어 있음")
            md.append(f"- {label}: {cut.get(key, '')}")
        expr = cut.get("expression", {})
        md.append("- 표정: " + (", ".join(f"{k} {v}" for k, v in expr.items()) if expr else "(없음)"))
        bubbles = cut.get("bubbles", [])
        if len([b for b in bubbles if b.get("type") != "title"]) > MAX_BUBBLES:
            warns.append(f"컷 {i}: 말풍선·박스 {len(bubbles)}개 (권장 {MAX_BUBBLES}개 이하)")
        md.append("- 대사·텍스트:")
        for b in bubbles:
            t = b.get("type", "speech")
            if t not in TYPES:
                warns.append(f"컷 {i}: 알 수 없는 type '{t}'")
            if b["text"].count("\n") + 1 > 2:
                warns.append(f"컷 {i}: 두 줄을 넘는 텍스트 — {b['text'][:20]}…")
            who = f" {b['speaker']}" if b.get("speaker") else ""
            md.append(f"  - [{TYPES.get(t, t)}{who}] {b['text'].replace(chr(10), ' / ')}")
        md.append("")

    md += ["## 확인한 사실과 출처", ""]
    for f in d.get("facts", []):
        srcs = f.get("sources", [])
        if len(set(srcs)) < 2:
            warns.append(f"출처 2개 미만: {f['fact']}")
        md.append(f"- {f['fact']}")
        md += [f"  - {u}" for u in srcs]
    if d.get("unconfirmed"):
        md += ["", "## 확인 필요", ""]
        md += [f"- {u}" for u in d["unconfirmed"]]

    out = src.with_suffix(".md")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{src} -> {out}")
    for w in warns:
        print(f"  ⚠ {w}")
    if not warns:
        print("  검사 통과")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

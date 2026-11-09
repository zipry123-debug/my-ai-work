"""퍼소나별 인용 후보: 상품·키워드 조건에 맞는 짧은 올리브영 리뷰."""
import json, re

D = json.load(open("zeroid_data/oliveyoung.json", encoding="utf-8"))
Q = {
    "A 시술후": ("인텐시브 크림|포밍 클렌저|데일리 선크림", r"레이저|시술|피부과|처방|장벽"),
    "B 트러블": ("핌프로브", r"트러블|붉|여드름|진정"),
    "C 메이크업": ("선크림|수딩", r"화장|메이크업|베이스|밀림|들뜸|톤업|백탁"),
    "E 건조/휴대": ("미스트|크림 마스크|인텐시브 크림", r"휴대|수시로|뿌리|건조|사무실|외출|가방|들고"),
    "콜라보": ("누렁이", r"누렁이|파우치|키링|귀여"),
}
for k, (pn, pat) in Q.items():
    print("\n==", k)
    n = 0
    for g, v in D.items():
        if not re.search(pn, v["name"]):
            continue
        for r in v["reviews"]:
            c = r["content"].replace("\n", " ")
            if re.search(pat, c) and 25 < len(c) < 120 and r["createdDateTime"] >= "2026":
                print(f"  [{v['name'][:22]}|{r['createdDateTime']}|{r['reviewScore']}] {c}")
                n += 1
                if n >= 9:
                    break
        if n >= 9:
            break

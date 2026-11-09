"""제로이드 공식 홈페이지 수집기: 제품 상세(텍스트·이미지 alt·영상·전성분)와 구매자 리뷰를 JSON + 이미지로 저장."""
import json, re, sys, html, time, urllib.request, urllib.parse
from pathlib import Path
from html.parser import HTMLParser

BASE = "https://www.zeroid.co.kr"
OUT = Path(__file__).parent / "zeroid_data"
CATES = {307: "인텐시브", 308: "수딩", 309: "핌프로브", 310: "루트힐", 311: "더마뉴얼",
         312: "선케어", 313: "의료기기(MD)", 347: "써지엔젤 플러스"}
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, data=None):
    url = urllib.parse.quote(url, safe=":/?&=%")
    req = urllib.request.Request(url, data=data, headers=UA)
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:
            err = e
            time.sleep(1)
    raise err


def text(url, data=None):
    return get(url, data).decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<br\s*/?>|</p>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t ]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


KNOWN = {307: [359, 363, 319, 320, 321, 322, 315, 365, 366, 370, 372], 308: [325, 324, 323, 344, 367, 368, 369],
         309: [327, 326, 345, 328, 329, 340], 310: [336], 311: [334, 331, 332, 358], 312: [341, 343],
         313: [316, 317, 318, 361, 346], 347: [348]}


def product_list():
    return [{"line": CATES[c], "cate": c, "idx": i, "thumb": ""} for c, ids in KNOWN.items() for i in ids]


def _unused_product_list():
    prods = []
    for c, line in CATES.items():
        body = urllib.parse.urlencode({"cate": c}).encode()
        h = text(f"{BASE}/web/product/product_list.ajax.asp", body)
        for li in re.findall(r"<li[\s\S]*?</li>", h):
            m = re.search(r"product_detail\.asp\?idx=(\d+)", li)
            img = re.search(r'<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"', li) or re.search(r'<img[^>]+alt="([^"]*)"[^>]*src="([^"]+)"', li)
            if not m:
                continue
            prods.append({"line": line, "cate": c, "idx": int(m.group(1)),
                          "list_text": clean(li), "thumb": BASE + re.search(r'src="([^"]+)"', li).group(1) if 'src="' in li else ""})
    seen, out = set(), []
    for p in prods:
        if p["idx"] not in seen:
            seen.add(p["idx"]); out.append(p)
    return out


def product_detail(p):
    h = text(f"{BASE}/web/product/product_detail.asp?idx={p['idx']}&cate={p['cate']}")
    name = re.search(r"getReviewList[\s\S]*?Name=([^&]+)&", h)
    p["name"] = name.group(1).strip() if name else ""
    imgs = []
    for tag in re.findall(r"<img[^>]+>", h):
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            continue
        s = src.group(1)
        if "cdn.neopharmshop" not in s and "/data/rental/" not in s:
            continue
        alt = re.search(r'alt="([^"]*)"', tag)
        imgs.append({"src": urllib.parse.urljoin(BASE, s).replace("http://", "https://"),
                     "alt": html.unescape(alt.group(1)) if alt else ""})
    p["detail_images"] = imgs
    p["videos"] = sorted(set(re.findall(r'(?:src|href)="((?:https?:)?//(?:www\.)?(?:youtube\.com|youtu\.be|player\.vimeo)[^"]+)"', h)))
    ing = re.search(r"전성분</[\s\S]{0,400}?<(?:p|div|dd)[^>]*>([\s\S]*?)</(?:p|div|dd)>", h)
    m = re.search(r"전성분([\s\S]{0,4000}?)상품정보", clean(h))
    p["ingredients"] = clean(m.group(1)) if m else ""
    vol = re.search(r"용량\s*:\s*([^<\n]+)", h)
    p["volume"] = clean(vol.group(1)) if vol else ""
    rc = re.search(r"전체\s*\((\d+)\)", clean(h))
    p["review_count"] = int(rc.group(1)) if rc else 0
    return p


def reviews(p):
    out, seen = [], set()
    for page in range(1, 60):
        q = urllib.parse.urlencode({"cate": p["idx"], "mode": "", "guid": p["idx"], "Name": p["name"], "page": page})
        h = text(f"{BASE}/web/product/product_review.ajax.asp?{q}")
        blocks = re.split(r'<div class="listone">', h)[1:]
        new = 0
        for b in blocks:
            uid = re.search(r"Uid=(\d+)", b)
            if not uid or uid.group(1) in seen:
                continue
            seen.add(uid.group(1)); new += 1
            w = re.findall(r"<span[^>]*>([^<]*)</span>", re.search(r'class="writer">([\s\S]*?)</div>', b).group(1))
            photo = re.search(r"background-image:url\('([^']+)'\)", b)
            ph = urllib.parse.urljoin(BASE, photo.group(1)) if photo else ""
            out.append({
                "uid": int(uid.group(1)),
                "stars": len(re.findall(r'class="star_navy\s*"', b)) or b.count("star_navy"),
                "writer": w[0] if w else "", "skin": w[1] if len(w) > 2 else "", "date": w[-1] if w else "",
                "title": clean(re.search(r"<h4>([\s\S]*?)</h4>", b).group(1)) if "<h4>" in b else "",
                "text": clean(re.search(r'class="ment">([\s\S]*?)</div>', b).group(1)) if 'class="ment"' in b else "",
                "photo": ph if ph and ph != p.get("thumb") and "/data/rental/brand/" not in ph else "",
            })
        if new == 0:
            break
    return out


def brand_pages():
    pages = {}
    for key in ["brand/brand_story.asp", "brand/brand_science.asp"]:
        h = text(f"{BASE}/web/{key}")
        body = re.search(r"<body[\s\S]*", h).group(0)
        body = re.sub(r"<(script|style)[\s\S]*?</\1>", "", body)
        imgs = [{"src": urllib.parse.urljoin(BASE, s), "alt": html.unescape(a)} for s, a in
                re.findall(r'<img[^>]+src="([^"]+)"[^>]*?(?:alt="([^"]*)")?', body)]
        pages[key] = {"text": clean(body), "images": imgs,
                      "videos": sorted(set(re.findall(r'(?:src|href)="([^"]*(?:youtube|youtu\.be|\.mp4)[^"]*)"', h)))}
    return pages


def download_images(prods):
    for p in prods:
        d = OUT / "images" / f"{p['idx']}"
        d.mkdir(parents=True, exist_ok=True)
        urls = [p["thumb"]] + [i["src"] for i in p["detail_images"]] + [r["photo"] for r in p["reviews"] if r["photo"]]
        for n, u in enumerate(dict.fromkeys(u for u in urls if u)):
            name = f"{n:02d}_" + re.sub(r"[^\w.-]", "_", urllib.parse.unquote(u.rsplit("/", 1)[-1]))[-60:]
            f = d / name
            if f.exists():
                continue
            try:
                f.write_bytes(get(u.replace("https://cdn", "http://cdn")))
            except Exception as e:
                print("  img fail", u, e)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    prods = product_list()
    print(len(prods), "products")
    def work(p):
        product_detail(p)
        p["reviews"] = reviews(p)
        print(f"{p['idx']} {p['name']}: imgs={len(p['detail_images'])} reviews={len(p['reviews'])}/{p['review_count']}")
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(10) as ex:
        list(ex.map(work, prods))
    (OUT / "products.json").write_text(json.dumps(prods, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "brand.json").write_text(json.dumps(brand_pages(), ensure_ascii=False, indent=1), encoding="utf-8")
    if "--images" in sys.argv:
        download_images(prods)
    print("done")

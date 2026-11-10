// 검색 엔진: 데이터 로드, 색인, 유사도 점수
import fs from 'node:fs';
import path from 'node:path';

const STRIP = /[\s()\[\]{}·・,.\-_/+&'"!~※*:;%]/g;
export const norm = s => String(s ?? '').toLowerCase().replace(STRIP, '');

// 한글 음절을 자모로 풀어 오타에 강하게 비교
function jamo(s) {
  let out = '';
  for (const ch of s) {
    const c = ch.charCodeAt(0);
    if (c >= 0xac00 && c <= 0xd7a3) {
      const i = c - 0xac00;
      out += String.fromCharCode(0x1100 + Math.floor(i / 588), 0x1161 + Math.floor((i % 588) / 28));
      if (i % 28) out += String.fromCharCode(0x11a7 + (i % 28));
    } else out += ch;
  }
  return out;
}
const gramSet = s => { const g = new Set(); for (let i = 0; i < s.length - 1; i++) g.add(s.slice(i, i + 2)); return g; };

function makeKey(text, maker = '') {
  const n = norm(text);
  return { n, m: norm(maker), g: gramSet(jamo(n)) };
}

// 글자 1개 차이(바뀜·빠짐·더해짐)까지 허용하는 부분 일치. 3글자 이상 검색어에만 사용
function nearSubstring(q, n) {
  const L = q.length;
  if (L < 3 || n.length < L - 1) return false;
  for (let i = 0; i + L <= n.length; i++) {           // 1글자 바뀜
    let diff = 0;
    for (let j = 0; j < L && diff < 2; j++) if (n[i + j] !== q[j]) diff++;
    if (diff < 2) return true;
  }
  for (let k = 0; k < L; k++) {                        // 1글자 빠짐/더해짐
    const del = q.slice(0, k) + q.slice(k + 1);
    if (n.includes(del) && del.length >= 3) return true;
  }
  for (let i = 0; i + L + 1 <= n.length; i++) {
    const w = n.slice(i, i + L + 1);
    for (let k = 0; k <= L; k++) if (w.slice(0, k) + w.slice(k + 1) === q) return true;
  }
  return false;
}

function makeQuery(q) {
  const n = norm(q);
  const tokens = q.trim().split(/\s+/).map(norm).filter(t => t.length > 1);
  return { raw: q, n, g: gramSet(jamo(n)), tokens };
}

// 0~1. 0이면 제외
function score(Q, K) {
  if (!Q.n) return 0;
  const { n, g } = K;
  if (n === Q.n) return 1;
  if (n.includes(Q.n)) return 0.9 + 0.08 * (Q.n.length / n.length) + (n.startsWith(Q.n) ? 0.01 : 0);
  let tokenScore = 0;
  if (Q.tokens.length > 1) {
    const inName = Q.tokens.filter(t => n.includes(t)).length;
    if (inName === Q.tokens.length) return 0.85;
    // 회사명까지 포함하면 모든 단어가 맞는 경우 (예: '종근당 락토핏')
    const inAll = Q.tokens.filter(t => n.includes(t) || (K.m && K.m.includes(t))).length;
    if (inName && inAll === Q.tokens.length) return 0.84;
    // 3글자 이상 단어가 일부 겹치는 경우만 비슷한 이름으로 인정
    const strong = Q.tokens.filter(t => t.length >= 3 && n.includes(t)).length;
    if (strong) tokenScore = 0.4 + 0.3 * (strong / Q.tokens.length);
  }
  if (nearSubstring(Q.n, n)) return Math.max(0.75, tokenScore);
  // 오타 대응: 검색어 자모 조각이 이름에 얼마나 들어있는지 + 전체 유사도
  if (Q.g.size < 2) return tokenScore;
  let inter = 0;
  for (const x of Q.g) if (g.has(x)) inter++;
  const coverage = inter / Q.g.size;
  const dice = (2 * inter) / (Q.g.size + g.size);
  const fuzzy = Math.max(dice, coverage * 0.95);
  return Math.max(fuzzy >= 0.72 ? fuzzy * 0.8 : 0, tokenScore);
}

export function loadDB(root) {
  const hfFile = JSON.parse(fs.readFileSync(path.join(root, 'data', 'hf.json'), 'utf8'));
  const sample = JSON.parse(fs.readFileSync(path.join(root, 'data', 'sample.json'), 'utf8'));
  const hf = hfFile.items.map(x => ({ ...x, kind: 'hf' }));
  // 일반식품: 전체 파일에서 만든 data/food.json이 있으면 그것을, 없으면 처음 샘플을 사용
  const foodPath = path.join(root, 'data', 'food.json');
  const foodSrc = fs.existsSync(foodPath) ? JSON.parse(fs.readFileSync(foodPath, 'utf8')).items : sample.food;
  // 식품첨가물 유형: 원본 데이터의 업종이 '식품첨가물제조업'인 제품이 과반인 식품유형 (data/additive-types.json)
  const addPath = path.join(root, 'data', 'additive-types.json');
  const additiveTypes = new Set(fs.existsSync(addPath) ? JSON.parse(fs.readFileSync(addPath, 'utf8')) : []);
  const food = foodSrc.map(x => ({ ...x, kind: 'gf', additive: additiveTypes.has(x.type) }));
  // 해외직구 위해식품 차단정보(I2715). 국내 신고 제품이 아니라 별도 구분 'dj'
  const directPath = path.join(root, 'data', 'direct.json');
  const direct = fs.existsSync(directPath) ? JSON.parse(fs.readFileSync(directPath, 'utf8')).items.map(x => ({ ...x, kind: 'dj' })) : [];
  const products = [...hf, ...food, ...direct];
  for (const p of products) {
    p._key = makeKey(p.name, p.maker);
    p._raw = norm(p.kind === 'hf' ? [p.funcMaterial, p.rawFunc, p.rawEtc].join(',') : p.kind === 'dj' ? p.harmful : (p.raw || []).join(','));
    p._funcRaw = p.kind === 'hf' ? norm(p.funcMaterial + ',' + p.rawFunc) : '';
  }
  const ingredients = sample.ingredients.map((x, idx) => ({ ...x, idx, _key: makeKey(x.name), _ckey: x.component ? makeKey(x.component) : null }));
  const recalls = sample.recalls;
  const recallByNo = new Map(recalls.filter(r => r.reportNo).map(r => [r.reportNo, r]));
  const recallByName = new Map(recalls.map(r => [norm(r.name) + '|' + norm(r.maker), r]));
  const byId = { hf: new Map(hf.map(p => [p.id, p])), gf: new Map(food.map(p => [p.id, p])), dj: new Map(direct.map(p => [p.id, p])) };

  const recallOf = p => recallByNo.get(p.id) || recallByName.get(norm(p.name) + '|' + norm(p.maker)) || null;
  const summary = p => ({
    kind: p.kind, id: p.id, name: p.name, maker: p.maker,
    sub: p.kind === 'hf' ? p.funcMaterial : p.kind === 'dj' ? p.harmful : p.type,
    recall: !!recallOf(p), ended: !!p.ended, date: p.date, additive: !!p.additive,
  });
  const clean = o => Object.fromEntries(Object.entries(o).filter(([k]) => !k.startsWith('_')));

  function searchProducts(q) {
    const Q = makeQuery(q);
    const hits = [];
    for (const p of products) { const s = score(Q, p._key); if (s > 0) hits.push([s, p]); }
    hits.sort((a, b) => b[0] - a[0] || a[1].name.localeCompare(b[1].name, 'ko'));
    return hits.map(h => h[1]);
  }

  function productsWithIngredient(q) {
    const qn = norm(q);
    if (!qn) return [];
    const hits = products.filter(p => p._raw.includes(qn));
    // 기능성 원료로 쓰인 건강기능식품 → 그 밖의 건강기능식품 → 일반식품 → 해외직구 차단 제품
    const rank = p => (p.kind === 'hf' ? (p._funcRaw.includes(qn) ? 0 : 1) : p.kind === 'gf' ? 2 : 3);
    return hits.sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name, 'ko'));
  }

  function searchIngredients(q) {
    const Q = makeQuery(q);
    return ingredients
      .map(x => [Math.max(score(Q, x._key), x._ckey ? score(Q, x._ckey) * 0.9 : 0), x])
      .filter(r => r[0] > 0)
      .sort((a, b) => b[0] - a[0] || a[1].name.length - b[1].name.length)
      .map(r => r[1]);
  }

  const LIMIT = 1000;
  const pack = list => ({
    total: list.length,
    counts: { hf: list.filter(p => p.kind === 'hf').length, gf: list.filter(p => p.kind === 'gf').length, dj: list.filter(p => p.kind === 'dj').length },
    items: list.slice(0, LIMIT).map(summary),
  });

  return {
    meta: { fetchedAt: hfFile.fetchedAt, hf: hf.length, gf: food.length, dj: direct.length, ingredients: ingredients.length },
    search(mode, q, opts = {}) {
      // 제품명 검색과 원료명 검색 모두 같은 규칙: 이름에 '수출'이 들어간 제품은 기본으로 숨김
      const all = mode === 'ingredient' ? productsWithIngredient(q) : searchProducts(q);
      const isExport = p => p.kind !== 'dj' && /수출/.test(p.name);
      const shown = opts.showExport ? all : all.filter(p => !isExport(p));
      return { products: { ...pack(shown), hiddenExport: opts.showExport ? 0 : all.length - shown.length, exportCount: all.filter(isExport).length } };
    },
    product(kind, id) {
      const p = byId[kind]?.get(id);
      return p ? { ...clean(p), recall: recallOf(p) } : null;
    },
    ingredient(idx, q) {
      const x = ingredients[idx];
      if (!x) return null;
      const query = q || x.name.replace(/\(.*$/, '').split('/')[0];
      return { ...clean(x), query, products: pack(productsWithIngredient(query)) };
    },
  };
}

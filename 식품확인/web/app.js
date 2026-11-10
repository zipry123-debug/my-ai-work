(() => {
  'use strict';

  const $ = (s, el = document) => el.querySelector(s);
  const view = $('#view');
  const form = $('#searchForm');
  const input = $('#q');
  const modeEl = $('.sch__mode');

  const EXAMPLES = {
    product: ['락토핏 골드', '루테인 지아잔틴', '홍삼정', '밀크씨슬'],
    ingredient: ['루테인', '프로바이오틱스', '가르시니아', '아연'],
  };
  // 검색창 안내 문구: 괄호 안 예시가 EXAMPLES 순서대로 약 3초마다 바뀜 (입력 중이거나 포커스 상태면 멈춤)
  const PLACEHOLDER = { product: '제품명 입력', ingredient: '원료명 입력' };
  const ROLL_MS = 3000;
  const KIND = { hf: '건강기능식품', gf: '일반식품', dj: '해외직구 차단' };
  // 일반식품 데이터 안의 식품첨가물(향료, 혼합제제 등)은 '식품첨가물'로 표시
  const kindLabel = p => (p.kind === 'gf' && p.additive ? '식품첨가물' : KIND[p.kind]);
  const PAGE = 30;

  let mode = 'product';
  let lastList = '#/';

  /* ---------- 텍스트 ---------- */
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const STRIP = /[\s()\[\]{}·・,.\-_/+&'"!~※*:;%]/;
  const norm = s => [...String(s ?? '').toLowerCase()].filter(c => !STRIP.test(c)).join('');
  const num = n => Number(n || 0).toLocaleString('ko-KR');

  function highlight(name, query) {
    const qn = norm(query);
    if (!qn) return esc(name);
    const chars = [...name], map = [];
    let stripped = '';
    chars.forEach((ch, i) => { if (!STRIP.test(ch)) { stripped += ch.toLowerCase(); map.push(i); } });
    const at = stripped.indexOf(qn);
    if (at < 0) return esc(name);
    const s = map[at], e = map[at + qn.length - 1] + 1;
    return esc(chars.slice(0, s).join('')) + '<mark>' + esc(chars.slice(s, e).join('')) + '</mark>' + esc(chars.slice(e).join(''));
  }

  // 괄호 안 쉼표는 나누지 않음
  function splitRaw(s) {
    if (!s) return [];
    const out = []; let depth = 0, cur = '';
    for (const ch of s) {
      if (ch === '(' || ch === '[') depth++;
      if (ch === ')' || ch === ']') depth = Math.max(0, depth - 1);
      if (ch === ',' && depth === 0) { if (cur.trim()) out.push(cur.trim()); cur = ''; } else cur += ch;
    }
    if (cur.trim()) out.push(cur.trim());
    return out;
  }
  const firstKo = s => String(s || '').replace(/\(영문\)[\s\S]*$/, '').replace(/^\(국문\)\s*/, '').trim();

  /* ---------- 서버 ---------- */
  const cache = new Map();
  async function api(url) {
    if (cache.has(url)) return cache.get(url);
    const res = await fetch(url);
    if (!res.ok && res.status !== 404) throw new Error(res.status);
    const body = res.ok ? await res.json() : null;
    if (cache.size > 50) cache.delete(cache.keys().next().value);
    cache.set(url, body);
    return body;
  }
  let seq = 0;
  async function load(url) {
    const my = ++seq;
    if (!cache.has(url)) view.innerHTML = '<div class="wrap"><p class="loading">불러오는 중…</p></div>';
    const data = await api(url);
    return my === seq ? data : undefined;
  }

  /* ---------- 목록 ---------- */
  // 기능성 원료 구성 요약: 검색어와 관련된 주원료 + 나머지 개수
  const BASIC = /^(비타민|셀레늄|셀렌|아연|구리|철|칼슘|마그네슘|망간|요오드|크롬|몰리브덴|엽산|나이아신|판토텐산|비오틴|칼륨|베타카로틴|식이섬유|단백질|필수\s*지방산)/;
  const cleanMat = m => m
    .replace(/\((기능성원료인정)?제?\s*\d{4}\s*-\s*\d+\s*호\)/g, '')
    .replace(/\(고시형\)/g, '')
    .replace(/^비타민\s+/, '비타민')
    .trim();
  function matSummary(p, q) {
    if (p.kind !== 'hf') return p.sub ? `식품유형 ${p.sub}` : '';
    const mats = [...new Set(splitRaw(p.sub).map(cleanMat).filter(Boolean))];
    if (!mats.length) return '';
    const tokens = String(q).split(/\s+/).map(norm).filter(t => t.length > 1);
    const related = m => tokens.some(t => norm(m).includes(t));
    const main = mats.filter(related);
    const lead = main.length ? main : mats.filter(m => !BASIC.test(m));
    const first = (lead.length ? lead : mats).slice(0, 2);
    const rest = mats.filter(m => !first.includes(m));
    return `기능성 원료 ${mats.length}가지`;
  }

  function productRows(items, q, opts) {
    return items.map(p => {
      const flags = (p.recall ? '<span class="lst__flag f-alert">회수 이력</span>' : '') + (p.ended ? '<span class="lst__flag">생산종료</span>' : '');
      const href = `#/p/${p.kind}/${encodeURIComponent(p.id)}${opts.hl ? '?hl=' + encodeURIComponent(opts.hl) : ''}`;
      return `<a class="lst__row" href="${href}">
        <span class="lst__kind k-${p.kind}">${KIND[p.kind]}</span>
        <span class="lst__name">${opts.mark ? highlight(p.name, q) : esc(p.name)}${flags}</span>
        ${opts.summary ? `<span class="lst__maker">${esc(matSummary(p, q))}</span>` : opts.noMaker ? '' : `<span class="lst__maker">${esc(p.maker)}</span>`}
        ${opts.noSub ? '' : `<span class="lst__sub">${esc(p.sub || '')}</span>`}</a>`;
    }).join('');
  }

  // 같은 이름(띄어쓰기·기호 무시)의 제품을 한 줄로 묶기. 순서는 검색 결과의 첫 등장 순서
  function groupByName(items) {
    const map = new Map();
    for (const p of items) {
      const key = p.kind + '|' + norm(p.name);
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(p);
    }
    return [...map.values()];
  }

  // 가나다순 정렬용: '(주)', '주식회사' 같은 앞뒤 표기는 빼고 비교
  const makerKey = m => String(m || '').replace(/\(주\)|㈜|주식회사|\(유\)|유한회사|농업회사법인|영농조합법인/g, '').trim();

  function groupRows(groups, q, opts) {
    return groups.map(g => {
      const p = g[0];
      const hl = opts.hl ? '?hl=' + encodeURIComponent(opts.hl) : '';
      const name = opts.mark ? highlight(p.name, q) : esc(p.name);
      if (g.length === 1) {
        const flags = (p.recall ? '<span class="lst__flag f-alert">회수 이력</span>' : '');
        return `<a class="lst__row" href="#/p/${p.kind}/${encodeURIComponent(p.id)}${hl}">
          <span class="lst__kind k-${p.kind}">${kindLabel(p)}</span>
          <span class="lst__name">${name}${flags}</span></a>`;
      }
      const recall = g.some(x => x.recall) ? '<span class="lst__flag f-alert">회수 이력 있음</span>' : '';
      return `<details class="grp">
        <summary class="lst__row grp__sum">
          <span class="lst__kind k-${p.kind}">${kindLabel(p)}</span>
          <span class="lst__name">${name}${recall}</span>
          <span class="grp__count">같은 이름 ${g.length}개</span>
        </summary>
        <div class="grp__list">${[...g].sort((a, b) => makerKey(a.maker).localeCompare(makerKey(b.maker), 'ko')).map(x => `<a class="grp__item" href="#/p/${x.kind}/${encodeURIComponent(x.id)}${hl}">
          <span>${esc(x.maker)}</span><span class="grp__date">${esc(x.date || '')} 신고</span></a>`).join('')}</div>
      </details>`;
    }).join('');
  }

  function productTable(pack, q, opts) {
    const tab = opts.tab || 'all';
    const counts = { all: pack.total, ...pack.counts };
    const shown = tab === 'all' ? pack.items : pack.items.filter(p => p.kind === tab);
    const limit = opts.limit || PAGE;
    const filters = [['all', '전체'], ['hf', '건강기능식품'], ['gf', '일반식품'], ['dj', '해외직구 차단']]
      .filter(([k]) => k !== 'dj' || counts.dj)
      .map(([k, label]) => `<button type="button" role="tab" data-tab="${k}" aria-selected="${k === tab}">${label}<b>${num(counts[k])}</b></button>`).join('');
    if (opts.group) {
      const groups = groupByName(shown);
      const gBody = groups.length
        ? `<div class="lst lst--3 lst--grp">${groupRows(groups.slice(0, limit), q, opts)}</div>`
        : '<div class="none">해당하는 제품이 없습니다.</div>';
      const gMore = groups.length > limit
        ? `<button class="more" data-more="${limit + PAGE}">더 보기</button>`
        : (counts[tab] > shown.length ? `<p class="note-s">이름이 가까운 상위 ${num(shown.length)}건까지 표시합니다. 검색어를 더 구체적으로 입력하면 범위가 좁혀집니다.</p>` : '');
      return `<div class="flt" role="tablist">${filters}</div>${gBody}${gMore}`;
    }
    const body = shown.length
      ? `<div class="lst${opts.noSub ? ' lst--3' : ''}" role="table">
          <div class="lst__hd" role="row"><span>구분</span><span>제품명</span><span>업체</span>${opts.noSub ? '' : '<span>기능성 원료 · 식품유형</span>'}</div>
          ${productRows(shown.slice(0, limit), q, opts)}</div>`
      : '<div class="none">해당하는 제품이 없습니다.</div>';
    const more = shown.length > limit
      ? `<button class="more" data-more="${limit + PAGE}">더 보기 (${num(counts[tab] - limit)}건)</button>`
      : (counts[tab] > shown.length ? `<p class="note-s">이름이 가까운 상위 ${num(shown.length)}건까지 표시합니다. 검색어를 더 구체적으로 입력하면 범위가 좁혀집니다.</p>` : '');
    return `<div class="flt" role="tablist">${filters}</div>${body}${more}`;
  }

  /* ---------- 화면 ---------- */
  function setPage(sub) { document.body.classList.toggle('is-sub', sub); }

  function renderHome() {
    setPage(false);
    document.title = '식품확인 - 건강기능식품 신고정보 조회';
    input.value = '';
    view.innerHTML = '';
  }

  async function renderSearch(params) {
    const q = params.get('q') || '';
    const m = params.get('mode') === 'ingredient' ? 'ingredient' : 'product';
    const tab = params.get('tab') || 'all';
    const limit = +params.get('n') || PAGE;
    setMode(m, false);
    input.value = q;
    setPage(true);
    lastList = location.hash;
    document.title = `${q} - 식품확인`;

    const showExport = params.get('export') === '1';
    const data = await load(`/api/search?mode=${m}&q=${encodeURIComponent(q)}${showExport ? '&export=1' : ''}`);
    if (data === undefined) return;

    // 제품명 검색과 원료명 검색은 같은 목록 형식을 씀. 차이: 원료명 검색은 제품명이 아니라 원재료에서 찾으므로 제품명 형광 표시 없음
    const pack = data.products;
    const isProduct = m === 'product';
    const title = isProduct ? `‘${esc(q)}’ 제품명 검색결과` : `‘${esc(q)}’이(가) 원재료에 들어간 제품`;
    view.innerHTML = `<div class="wrap res res--n">
      <div class="res__head"><h2>${title}<span>${num(pack.total)}건</span></h2>${isProduct ? '<span class="res__sort">이름이 가까운 순</span>' : ''}</div>
      ${pack.total ? productTable(pack, q, { tab, limit, mark: isProduct, hl: isProduct ? '' : q, noSub: true, group: true }) : `<div class="none"><strong>찾는 제품이 없습니다</strong>이름 일부만 넣어 보세요.</div>`}
      ${pack.exportCount ? `<p class="note-s export-note">${showExport
        ? `수출용 제품 ${num(pack.exportCount)}건을 함께 보는 중입니다. <button type="button" class="link-btn" data-export="0">다시 숨기기</button>`
        : `제품명에 ‘수출’이 들어간 수출용 제품 ${num(pack.hiddenExport)}건은 숨겼습니다. <button type="button" class="link-btn" data-export="1">함께 보기</button>`}</p>` : ''}
      ${pack.total ? `<p class="note-s scope-note">국내에서 신고된 제품만 찾을 수 있습니다. 해외직구 제품이나 판매 이름이 신고 이름과 다른 제품은 나오지 않을 수 있습니다.<br>일반식품은 현재 일부만 들어 있습니다.</p>` : ''}
    </div>`;
  }

  const crumb = () => `<div class="crumb"><a href="${esc(lastList)}" data-back>검색결과로</a></div>`;
  const rows = list => list.filter(r => r[1]).map(([k, v, cls]) => `<tr><th scope="row">${k}</th><td${cls ? ` class="${cls}"` : ''}>${v}</td></tr>`).join('');
  const rawCell = (s, hl) => {
    const list = Array.isArray(s) ? s : splitRaw(s);
    if (!list.length) return '';
    return list.map(r => (hl && norm(r).includes(hl)) ? `<span class="hit">${esc(r)}</span>` : esc(r)).join(', ');
  };

  // 일반식품 원재료 중 이름 대신 분류만 적힌 항목(원본 C002 그대로). 기준: 아래 4개 + '가공품'으로 끝나는 이름 (2026.11.10 승인)
  const CATEGORY_RAW = /^(식품첨가물|식품첨가물혼합제제|혼합제제|기타혼합제제)$|가공품$/;
  const groupedRawCell = (list, hl) => {
    const mark = r => (hl && norm(r).includes(hl)) ? `<span class="hit">${esc(r)}</span>` : esc(r);
    const named = [], cat = new Map();
    for (const r of list) {
      const t = r.trim();
      if (CATEGORY_RAW.test(t)) cat.set(t, (cat.get(t) || 0) + 1); else named.push(r);
    }
    if (!cat.size) return rawCell(list, hl);
    const others = [...cat].map(([k, n]) => `${mark(k)} ${n}개`).join(', ');
    return (named.length ? `<div>${named.map(mark).join(', ')}</div>` : '')
      + `<div class="raw-etc">그 밖에 ${others}</div>`
      + `<p class="raw-note">‘그 밖에’는 신고 자료에 원료 이름 대신 분류만 적힌 것입니다.<br>정확한 원료 이름은 제품 포장에서 확인하세요.</p>`;
  };

  async function renderProduct(kind, id, params) {
    setPage(true);
    const p = await load(`/api/product/${kind}/${encodeURIComponent(id)}`);
    if (p === undefined) return;
    if (!p) { view.innerHTML = '<div class="wrap res"><div class="none"><strong>제품 정보를 찾지 못했습니다</strong></div></div>'; return; }
    document.title = `${p.name} - 식품확인`;
    const hl = norm(params.get('hl') || '');
    const rec = p.recall;

    // 식품유형 쉬운 설명 47개. 근거: 「식품의 기준 및 규격」(식약처 고시 제2026-55호) 식품유형 정의를
    // 쉽게 풀어 씀. 원문과 항목별 대조, 이웃 유형 대조를 거침 (2026.11.10). 키는 API 데이터 표기 그대로
    // 혼합제제·향료 등 식품첨가물 유형은 원문 미확인으로 설명 없음('?' 없이 이름만 표시)
    const TYPE_DESC = {
      '캔디류': '사탕, 캐러멜, 젤리, 양갱처럼 당분이 많은 원료를 주로 써서 만든 단 식품입니다.',
      '과자': '곡물 가루 등을 굽거나 부풀리거나 튀겨서 만든 비스킷, 쿠키, 스낵 같은 식품입니다.',
      '빵류': '밀가루 등으로 반죽해 만든 식빵, 케이크, 도넛 같은 식품입니다.',
      '떡류': '쌀가루, 찹쌀가루 등을 반죽하거나 익혀서 만든 떡입니다.',
      '기타가공품': '식품공전에 정해진 다른 어떤 종류에도 들어가지 않는 가공식품입니다.',
      '침출차': '잎, 꽃, 뿌리, 곡물 등을 물에 우려서 마시는 차입니다.',
      '액상차': '식물을 우려내거나 농축하는 등의 방법으로 만든, 액체나 시럽 형태의 차입니다.',
      '고형차': '식물을 원료로 만든 가루 같은 고체 형태의 차입니다.',
      '혼합음료': '물이나 동식물 원료에 다른 재료를 더해 마실 수 있게 만든 음료입니다.',
      '음료베이스': '물 등에 섞어 마시도록 만든 음료 재료입니다.',
      '과.채주스': '과일이나 채소의 즙이 95% 이상 들어간 주스입니다.',
      '과.채음료': '과일이나 채소 즙이 10% 이상 들어간 음료입니다.',
      '탄산음료': '물에 탄산가스와 다른 재료를 넣거나, 탄산수에 다른 재료를 넣어 만든 음료입니다.',
      '유산균음료': '우유 제품이나 식물 원료를 유산균으로 발효시킨 음료입니다.',
      '인삼.홍삼음료': '인삼이나 홍삼 성분을 넣어 만든, 그대로 마시는 음료입니다.',
      '가공두유': '두유에 과일즙, 우유, 곡물 가루 등을 더한 두유입니다(가루 형태 포함).',
      '커피': '커피 원두를 가공해 만든 원두커피, 인스턴트커피, 커피음료 등입니다.',
      '체중조절용 조제식품': '체중 조절이 필요한 사람을 위해 식사의 일부나 전부를 대신하도록 영양성분을 조절해 만든 식품입니다.',
      '당류가공품': '설탕, 물엿, 올리고당, 꿀 등을 주원료로 만든 식품입니다.',
      '당절임': '과일 등을 꿀이나 설탕에 절여 만든 식품입니다.',
      '절임식품': '재료를 소금, 장, 식초 등에 절이거나 양념해 만든 식품입니다.',
      '김치': '배추 같은 채소를 절이고 양념해 그대로 또는 발효시킨 식품입니다.',
      '효소식품': '식물 원료에 먹을 수 있는 미생물을 길러 효소를 늘리거나, 효소가 든 부분을 뽑아 만든 식품입니다.',
      '과.채가공품': '과일, 채소, 버섯을 주원료로 만든 가공식품입니다.',
      '곡류가공품': '쌀, 밀, 옥수수 같은 곡물을 주원료로 만든 가공식품입니다.',
      '두류가공품': '콩, 녹두, 팥 같은 콩류를 주원료로 만든 가공식품입니다.',
      '기타 농산가공품': '농산물로 만들었지만 다른 종류에 들어가지 않는 가공식품입니다.',
      '기타 수산물가공품': '생선 같은 수산물을 주원료로 만든 가공식품입니다.',
      '어묵': '생선살을 갈아 반죽해서 만든 식품입니다.',
      '양념젓갈': '젓갈에 고춧가루, 조미료 등을 넣어 양념한 것입니다.',
      '조미건어포': '생선이나 오징어 같은 해산물을 양념해서 말린 식품입니다.',
      '추출가공식품': '먹을 수 있는 동물성 재료를 물로 우려내 만든 식품입니다.',
      '유함유가공품': '우유나 유제품으로 만들었지만 다른 유제품 종류에 들어가지 않는 식품입니다.',
      '기타 식용유지가공품': '식물성이나 동물성 기름을 주원료로 만든 식품입니다.',
      '기타식물성유지': '콩기름, 참기름처럼 따로 정해진 기름에 들어가지 않는, 한 가지 식물에서 얻은 기름입니다.',
      '두부': '콩물을 굳혀서 만든 두부입니다.',
      '소스': '여러 재료에 장, 설탕, 소금, 식초 같은 양념을 섞어 만든 소스입니다.',
      '복합조미식품': '음식에 맛과 향을 내려고 설탕, 소금, 향신료 등을 섞어 가루, 알갱이, 덩어리 형태로 만든 조미료입니다.',
      '잼': '과일이나 채소를 30% 이상 넣고 설탕 등과 함께 굳힌 잼입니다.',
      '기타잼': '과일, 채소, 우유 제품 등을 그대로 또는 설탕 등과 함께 가공한 시럽, 파이 속, 밀크잼 같은 식품입니다.',
      '초콜릿가공품': '견과류, 사탕, 비스킷 등에 초콜릿을 섞거나 입히거나 속에 채워 만든 식품입니다.',
      '맥주': '싹 틔운 보리 같은 곡물과 홉 등을 발효시켜 만든 술입니다.',
      '탁주': '곡물 같은 원료와 누룩, 물로 발효시켜 뿌옇게 만든 술입니다.',
      '기타 주류': '발효주, 증류주, 주정 어디에도 들어가지 않는 술입니다.',
      '신선편의식품': '씻거나 껍질을 벗기거나 잘라서 바로 먹을 수 있게 만든 샐러드, 새싹채소 같은 식품입니다.',
      '즉석섭취식품': '데우거나 조리하지 않고 바로 먹는 도시락, 김밥, 햄버거, 선식 같은 식품입니다.',
      '즉석조리식품': '간단히 데우거나 끓이면 먹을 수 있게 만든 국, 탕, 수프, 순대 같은 식품입니다.',
    };
    const typeChip = t => TYPE_DESC[t]
      ? `<span class="pop">
          <button type="button" class="verdict2__type pop__btn" aria-expanded="false" aria-controls="typePop">종류 · ${esc(t)}<span class="pop__q" aria-hidden="true">?</span></button>
          <span class="pop__box" id="typePop" role="tooltip" hidden><b>${esc(t)}</b>${esc(TYPE_DESC[t])}<small>식품의약품안전처 식품공전의 정의를 쉽게 풀어 쓴 설명입니다</small></span>
        </span>`
      : `<span class="verdict2__type">종류 · ${esc(t)}</span>`;

    const XICON = '<svg width="18" height="18" viewBox="0 0 18 18"><path d="M5 5l8 8M13 5l-8 8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>';
    const verdict = kind === 'dj'
      ? `<div class="verdict2 v2-dj">
          <div class="verdict2__head"><span class="verdict2__icon" aria-hidden="true">${XICON}</span><strong>해외직구 위해식품입니다</strong></div>
          <p>나라에서 국내 반입 차단 목록에 올린 해외 제품입니다</p>
          ${p.harmful ? `<span class="verdict2__type">차단 사유 · ${esc(p.harmful)}</span>` : ''}
        </div>`
      : kind === 'gf'
      ? `<div class="verdict2 v2-gf">
          <div class="verdict2__head"><span class="verdict2__icon" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 18 18"><path d="M5 5l8 8M13 5l-8 8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></span><strong>건강기능식품이 아닙니다</strong></div>
          <p>${p.additive ? '식품첨가물입니다' : '일반 식품입니다'}<br>나라에 건강기능식품으로 신고된 제품이 아닙니다</p>
          ${p.type ? typeChip(p.type) : ''}
        </div>`
      : `<div class="verdict v-hf"><strong>건강기능식품입니다</strong><p>건강기능식품에 관한 법률에 따라 품목제조 신고된 제품입니다.</p></div>`;

    const table = kind === 'dj'
      ? rows([
          ['제조사', esc(p.maker)],
          ['제조국', esc(p.country)],
          ['바코드', esc(p.barcode)],
          ['등록일', esc(p.date)],
        ])
      : kind === 'hf'
      ? rows([
          ['기능성 원료', rawCell(p.rawFunc, hl)],
          ['기타 원료', rawCell(p.rawEtc, hl)],
          ['캡슐 원료', rawCell(p.rawCap, hl)],
          ['보관 방법', esc(p.storage)],
          ['제조업체', esc(p.maker)],
          ['품목제조번호', esc(p.id)],
          ['신고일자', esc(p.date)],
          ['생산 여부', p.ended ? '생산종료' : ''],
        ])
      : rows([
          ['원재료', groupedRawCell(p.raw || [], hl)],
          ['제조업체', esc(p.maker)],
          ['품목제조번호', esc(p.id)],
          ['보고일자', esc(p.date)],
          ['생산 여부', p.ended ? '생산종료' : ''],
        ]);

    view.innerHTML = `<div class="wrap dt">
      <div class="dt-narrow">
      ${crumb('제품 정보')}
      <div class="dt__kind k-${kind}">${kindLabel(p)}</div>
      <h1>${esc(p.name)}</h1>
      ${verdict}
      ${rec ? `<div class="recall"><strong>회수·판매중지 이력 (${esc(rec.date)})</strong><p>${esc(rec.reason)}${rec.grade ? ` / ${esc(rec.grade)}` : ''}</p></div>` : ''}
      ${kind === 'dj' && p.images && p.images.length ? `<div class="dj-photos">${p.images.slice(0, 2).map(u => `<img src="${esc(u)}" alt="${esc(p.name)} 제품 사진" loading="lazy" onerror="this.remove()">`).join('')}</div>` : ''}
      <table class="spec"><tbody>${table}</tbody></table>
      <p class="src">자료: 식품의약품안전처 ${kind === 'hf' ? '「건강기능식품 품목제조 신고사항 현황」' : kind === 'dj' ? '「해외직구 위해식품 차단정보」' : '「식품(첨가물)품목제조보고」'}</p>
    </div></div>`;
    window.scrollTo(0, 0);
  }

  async function renderIngredient(idx, params) {
    setPage(true);
    const x = await load(`/api/ingredient/${idx}?q=${encodeURIComponent(params.get('q') || '')}`);
    if (x === undefined) return;
    if (!x) { view.innerHTML = '<div class="wrap res"><div class="none"><strong>원료 정보를 찾지 못했습니다</strong></div></div>'; return; }
    document.title = `${x.name} - 식품확인`;
    const q = x.query;
    const dose = x.kind === '고시형'
      ? (x.low || x.high ? `${x.low || ''}${x.low && x.high ? ' ~ ' : ''}${x.high || ''} ${x.unit || ''}`.trim() : '')
      : x.dose;
    const tab = params.get('tab') || 'all';
    const limit = +params.get('n') || PAGE;

    view.innerHTML = `<div class="wrap dt">
      ${crumb('원료 정보')}
      <div class="dt__kind">기능성 원료 · ${esc(x.kind)}</div>
      <h1>${esc(x.name)}</h1>
      <table class="spec" style="max-width:880px"><tbody>${rows([
        ['기능성 내용', esc(firstKo(x.func)), 'strong'],
        ['1일 섭취량', esc(dose)],
        ['섭취 시 주의사항', esc((x.caution || '').replace(/^-/gm, '· '))],
        ['기능·지표성분', esc(x.component)],
        ['구분', x.kind === '고시형' ? '고시형 원료 (건강기능식품 공전에 등재)' : '개별인정형 원료 (업체 신청으로 개별 인정)'],
        ['인정번호', esc(x.no)],
        ['인정일자', esc(x.date)],
        ['신청업체', esc(x.maker)],
      ])}</tbody></table>
      <p class="src">자료: 식품의약품안전처 「건강기능식품 품목분류정보」, 「건강기능식품 기능성 원료인정현황」</p>
      <h2 class="h2">원재료에 ‘${esc(q)}’이(가) 들어간 제품 <span style="color:var(--gray);font-weight:500">${num(x.products.total)}건</span></h2>
      ${x.products.total ? productTable(x.products, q, { tab, limit, hl: q }) : '<div class="none">원재료에 이 이름이 들어간 제품이 없습니다.</div>'}
    </div>`;
    window.scrollTo(0, 0);
  }

  function renderAbout() {
    setPage(true);
    document.title = '데이터 출처 - 식품확인';
    view.innerHTML = `<div class="wrap about"><div class="dt-narrow">
      <h1>데이터 출처</h1>
      <p>식품의약품안전처가 식품안전나라에 공개한 공공데이터를 내용 수정 없이 옮겨 보여줍니다.</p>
      <table class="tbl" style="margin-top:20px">
        <thead><tr><th scope="col">항목</th><th scope="col">원본 데이터</th></tr></thead>
        <tbody>
          <tr><td>건강기능식품 제품</td><td>건강기능식품 품목제조 신고사항 현황 (I0030)</td></tr>
          <tr><td>일반식품 제품</td><td>식품(첨가물)품목제조보고 (I1250)</td></tr>
          <tr><td>일반식품 원재료</td><td>식품(첨가물)품목제조보고(원재료) (C002)</td></tr>
          <tr><td>기능성 원료</td><td>건강기능식품 품목분류정보 (I2710), 건강기능식품 기능성 원료인정현황 (I-0040)</td></tr>
          <tr><td>회수·판매중지</td><td>회수·판매중지 정보 (I0490)</td></tr>
        </tbody>
      </table>
      <h2 class="h2">이용 시 참고</h2>
      <ul>
        <li>국내에서 신고·보고된 제품이 대상입니다. 해외직구 제품은 신고 자료가 없을 수 있습니다.</li>
        <li>판매처에 표시된 이름과 신고된 제품명이 다를 수 있습니다. 이름 일부나 업체명을 함께 넣어 검색해 보세요.</li>
        <li>일반식품은 현재 일부 제품만 수록되어 있습니다.</li>
      </ul>
    </div></div>`;
  }

  /* ---------- 검색창 ---------- */
  function renderExamples() {
    $('#examples').innerHTML = '예) ' + EXAMPLES[mode].map(e => `<button type="button" data-ex="${esc(e)}">${esc(e)}</button>`).join('');
  }
  function setMode(m, rerun = true) {
    mode = m;
    modeEl.querySelectorAll('button').forEach(b => b.setAttribute('aria-checked', String(b.dataset.mode === m)));
    rollIdx = 0;
    setPh();
    renderExamples();
    if (rerun && input.value.trim()) go(input.value.trim());
  }
  let rollIdx = 0;
  const setPh = () => { input.placeholder = `${PLACEHOLDER[mode]} (예: ${EXAMPLES[mode][rollIdx % EXAMPLES[mode].length]})`; };
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  setInterval(() => {
    if (document.hidden || document.activeElement === input || input.value) return;
    rollIdx++;
    if (reduceMotion.matches) { setPh(); return; }
    input.classList.add('ph-out');                       // 흐려졌다가 다음 예시로 바뀌며 다시 나타남
    setTimeout(() => { setPh(); input.classList.remove('ph-out'); }, 250);
  }, ROLL_MS);
  setPh();
  function go(q) { location.hash = '#/search?' + new URLSearchParams({ mode, q }).toString(); }

  modeEl.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (b && b.dataset.mode !== mode) { setMode(b.dataset.mode); input.focus(); }
  });
  modeEl.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      setMode(mode === 'product' ? 'ingredient' : 'product');
      modeEl.querySelector(`[data-mode="${mode}"]`).focus();
    }
  });
  form.addEventListener('submit', e => {
    e.preventDefault();
    const q = input.value.trim();
    if (q) { go(q); input.blur(); }
  });
  $('#examples').addEventListener('click', e => {
    const b = e.target.closest('[data-ex]');
    if (b) { input.value = b.dataset.ex; go(b.dataset.ex); }
  });

  // 식품유형 설명 팝오버: 누르면 열고, 다시 누르거나 바깥을 누르거나 Esc로 닫기
  const closePops = except => document.querySelectorAll('.pop__btn[aria-expanded="true"]').forEach(b => {
    if (b === except) return;
    b.setAttribute('aria-expanded', 'false');
    b.nextElementSibling.hidden = true;
  });
  document.addEventListener('click', e => {
    const b = e.target.closest('.pop__btn');
    closePops(b);
    if (b) {
      const open = b.getAttribute('aria-expanded') !== 'true';
      b.setAttribute('aria-expanded', String(open));
      b.nextElementSibling.hidden = !open;
    }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closePops(); });

  view.addEventListener('click', e => {
    const t = e.target.closest('[data-tab],[data-more],[data-more-ing],[data-back],[data-export]');
    if (!t) return;
    if (t.dataset.back !== undefined) {
      if (lastList !== '#/' && history.length > 1) { e.preventDefault(); history.back(); }
      return;
    }
    const [path, qs] = location.hash.split('?');
    const p = new URLSearchParams(qs || '');
    if (t.dataset.tab) { p.set('tab', t.dataset.tab); p.delete('n'); }
    if (t.dataset.export) { if (t.dataset.export === '1') p.set('export', '1'); else p.delete('export'); p.delete('n'); }
    if (t.dataset.more) p.set('n', t.dataset.more);
    if (t.dataset.moreIng) p.set('in', t.dataset.moreIng);
    const y = window.scrollY;
    history.replaceState(null, '', path + '?' + p.toString());
    route().then(() => window.scrollTo(0, y));
  });

  /* ---------- 라우팅 ---------- */
  async function route() {
    const [path, qs] = (location.hash || '#/').slice(1).split('?');
    const params = new URLSearchParams(qs || '');
    const parts = path.split('/').filter(Boolean);
    try {
      if (parts[0] === 'search' && params.get('q')) return await renderSearch(params);
      if (parts[0] === 'p') return await renderProduct(parts[1], decodeURIComponent(parts[2] || ''), params);
      if (parts[0] === 'i') return await renderIngredient(+parts[1], params);
      if (parts[0] === 'about') return renderAbout();
      renderHome();
    } catch {
      view.innerHTML = '<div class="wrap res"><div class="none"><strong>정보를 불러오지 못했습니다</strong>잠시 후 다시 시도해 주세요.</div></div>';
    }
  }

  window.addEventListener('hashchange', route);
  renderExamples();
  api('/api/meta').then(m => {
    $('#fetchedAt').textContent = m.fetchedAt.replaceAll('-', '.');
  }).catch(() => {});
  route();
})();

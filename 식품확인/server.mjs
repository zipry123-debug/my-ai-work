// 로컬 서버: 화면(web/) + 검색 API
// 실행: node server.mjs
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadDB } from './search.mjs';

const root = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.join(root, 'web');
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
const port = +process.env.PORT || 5178;

const t0 = Date.now();
const db = loadDB(root);
console.log(`데이터 로드 ${Date.now() - t0}ms`, db.meta);

const json = (res, code, body) => {
  res.writeHead(code, { 'Content-Type': types['.json'], 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
};

http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  const p = decodeURIComponent(url.pathname);

  if (p.startsWith('/api/')) {
    const parts = p.split('/').filter(Boolean); // ['api', ...]
    try {
      if (parts[1] === 'meta') return json(res, 200, db.meta);
      if (parts[1] === 'search') {
        const q = (url.searchParams.get('q') || '').slice(0, 100);
        if (!q.trim()) return json(res, 400, { error: '검색어가 없습니다' });
        return json(res, 200, db.search(url.searchParams.get('mode'), q, { showExport: url.searchParams.get('export') === '1' }));
      }
      if (parts[1] === 'product') {
        const r = db.product(parts[2], parts[3]);
        return r ? json(res, 200, r) : json(res, 404, { error: '제품을 찾지 못했습니다' });
      }
      if (parts[1] === 'ingredient') {
        const r = db.ingredient(+parts[2], url.searchParams.get('q') || '');
        return r ? json(res, 200, r) : json(res, 404, { error: '원료를 찾지 못했습니다' });
      }
      return json(res, 404, { error: 'not found' });
    } catch (e) {
      console.error(e);
      return json(res, 500, { error: '서버 오류' });
    }
  }

  let fp = p.endsWith('/') ? p + 'index.html' : p;
  const file = path.join(webRoot, path.normalize(fp));
  if (!file.startsWith(webRoot)) { res.writeHead(403).end(); return; }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404).end('not found'); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(data);
  });
}).listen(port, () => console.log(`http://localhost:${port}`));

import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root = fileURLToPath(new URL('../dist/',import.meta.url));
const index = process.argv.indexOf('--port');
const port = Number(index >= 0 ? process.argv[index+1] : process.env.PORT || 5173);
if (!Number.isInteger(port) || port<1 || port>65535) throw new Error('올바른 포트 번호가 필요합니다. 예: npm start -- --port 5174');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.ico':'image/x-icon','.woff2':'font/woff2'};
const server=http.createServer(async(req,res)=>{
  if (!['GET','HEAD'].includes(req.method)) {res.writeHead(405,{Allow:'GET, HEAD'});res.end();return;}
  try {
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    let target=path.resolve(root,'.'+pathname);
    if (path.relative(root,target).startsWith('..') || path.isAbsolute(path.relative(root,target))) {res.writeHead(403);res.end('Forbidden');return;}
    const info=await fs.stat(target);
    if (info.isDirectory()) target=path.join(target,'index.html');
    const body=await fs.readFile(target);
    res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream','Cache-Control':'no-store','Content-Length':body.length});
    res.end(req.method==='HEAD'?undefined:body);
  } catch(error) {
    res.writeHead(error instanceof URIError?400:404,{'Content-Type':'text/plain; charset=utf-8'});res.end('파일을 찾을 수 없습니다.');
  }
});
server.on('error',error=>{console.error(error.code==='EADDRINUSE'?'포트를 이미 사용 중입니다. npm start -- --port 5174 로 실행하세요.':error.message);process.exitCode=1;});
server.listen(port,'127.0.0.1',()=>{console.log('Local: http://localhost:'+port+'/');console.log('종료: Ctrl+C | HTML 수정 후 브라우저 새로고침');});

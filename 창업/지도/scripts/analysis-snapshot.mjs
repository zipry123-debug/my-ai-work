import vm from 'node:vm';
import {createHash} from 'node:crypto';
export function snapshot(html,REGION) {
  const start=html.indexOf('// ---------- 설정');
  const end=html.indexOf('// ---------- 지도',start);
  if(start<0 || end<0) throw new Error('설정/지도 섹션을 찾지 못했습니다. 소스를 분리했다면 검증 스크립트도 함께 수정하세요.');
  const data=vm.runInNewContext(html.slice(start,end)+
    ';addRegion(REGION);const scenarios=[];'+
    'for(const mode of ["required","optional","off"]) for(const key of Object.keys(CHECKS)){state=structuredClone(DEFAULTS);state.modes[key]=mode;scenarios.push({name:key+":"+mode,results:cells.map(cell=>evaluate(cell))});}'+
    'state=structuredClone(DEFAULTS);JSON.stringify({cellSize:CELL_M,cellCount:cells.length,defaultResults:cells.map(c=>evaluate(c)),scenarios})',
    {structuredClone,REGION},{timeout:120000});
  const parsed=JSON.parse(data);
  const hash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');
  return {cellSize:parsed.cellSize,cellCount:parsed.cellCount,
    defaultMatches:parsed.defaultResults.filter(e=>e.requiredOk&&e.passed===e.total).length,
    defaultHash:hash(parsed.defaultResults),
    scenarios:parsed.scenarios.map(s=>({name:s.name,hash:hash(s.results)}))};
}

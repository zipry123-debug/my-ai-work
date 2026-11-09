import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {snapshot} from './analysis-snapshot.mjs';
const html=await fs.readFile(new URL('../dist/index.html',import.meta.url),'utf8');
for(const block of html.split('<script>').slice(1)) {
  const end=block.indexOf('</script>');
  assert.ok(end>=0,'닫히지 않은 script 태그가 있습니다.');
  new vm.Script(block.slice(0,end));
}
console.log('PASS: inline JavaScript syntax');
const baseline=JSON.parse(await fs.readFile(new URL('../reference/analysis-baseline.json',import.meta.url),'utf8'));
const region=JSON.parse(await fs.readFile(new URL('../dist/data/regions/41270.json',import.meta.url),'utf8'));
const current=snapshot(html,region);
assert.deepEqual(current,baseline.snapshot,'분석 결과가 검증된 기준과 다릅니다. 의도한 변경인지 확인하세요.');
console.log(`PASS: ${current.cellCount.toLocaleString('en-US')} cells / ${current.scenarios.length} filter-mode scenarios / ${current.defaultMatches} default matching cells`);
console.log('브라우저 표시와 NAVER 인증은 별도로 실제 화면에서 확인하세요.');
// 100m 칸: 같은 화면 코드로 안산 100m 자료를 판정해 기준과 비교한다.
const region100=JSON.parse(await fs.readFile(new URL('../dist/data/regions/41270_100.json',import.meta.url),'utf8'));
const current100=snapshot(html,region100);
assert.equal(current100.cellSize,100,'100m 자료의 칸 크기가 100이 아닙니다.');
assert.deepEqual(current100,baseline.snapshot100,'100m 분석 결과가 검증된 기준과 다릅니다. 의도한 변경인지 확인하세요.');
console.log(`PASS(100m): ${current100.cellCount.toLocaleString('en-US')} cells / ${current100.scenarios.length} filter-mode scenarios / ${current100.defaultMatches} default matching cells`);

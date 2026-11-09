# Claude Code + OpenAI GPT Image MCP 자동 설치 스크립트 (Windows)
# install.bat 을 더블클릭해서 실행하세요.

$ErrorActionPreference = 'Stop'
$ServerName  = 'openai-gpt-image'
$PackageName = 'openai-gpt-image-mcp-server@1.4.0'   # 동작을 확인한 버전으로 고정

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    [!] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "    [X] $msg" -ForegroundColor Red; exit 1 }

# 예상하지 못한 오류도 창이 닫히기 전에 내용을 보여줌 (대기는 install.bat 의 pause 가 담당)
trap { Write-Host "`n    [X] 예상하지 못한 오류: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
}

# 임시 JS 파일로 node 실행. 설치 경로와 무관하게 동작하도록 TEMP 에 만들었다가 지움
function Run-Js($name, $code) {
    $jsFile = Join-Path $env:TEMP $name
    Set-Content -Path $jsFile -Value $code -Encoding ASCII
    try { node $jsFile; $script:JsExit = $LASTEXITCODE } finally { Remove-Item $jsFile -Force -ErrorAction SilentlyContinue }
}

# 1. Node.js 확인/설치
Step "Node.js 확인"
Refresh-Path
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Warn "Node.js가 없습니다. winget으로 설치합니다 (관리자 승인 창이 뜰 수 있음)."
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail "winget이 없습니다. https://nodejs.org 에서 LTS를 직접 설치한 뒤 다시 실행하세요."
    }
    winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
    Refresh-Path
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Fail "Node.js 설치 후에도 인식되지 않습니다. 창을 닫고 install.bat을 다시 실행하세요."
    }
}
$nodeVer = (node -v).TrimStart('v')
if ([int]($nodeVer.Split('.')[0]) -lt 22) { Fail "Node.js $nodeVer 은 너무 낮습니다. https://nodejs.org 에서 LTS를 설치한 뒤 다시 실행하세요." }
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) { Fail "npx를 찾지 못했습니다. https://nodejs.org 에서 Node.js LTS를 다시 설치하세요." }
Ok "Node.js v$nodeVer"

# 2. Claude 종료 확인 (켜져 있으면 설정 변경이 덮어써지거나 새 PATH를 못 읽을 수 있음)
Step "Claude 종료 확인"
$claudeDir  = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { $env:USERPROFILE }
$claudeJson = Join-Path $claudeDir '.claude.json'
while (Get-Process -Name claude -ErrorAction SilentlyContinue) {
    Warn "Claude가 실행 중입니다. 창을 닫고, 작업 표시줄 오른쪽 아래 트레이 아이콘에서도 종료해 주세요."
    $ans = Read-Host "    종료했으면 엔터 (그대로 진행하려면 s 입력 후 엔터)"
    if ($ans -match '^[sSㄴ]') { Warn "Claude가 켜진 채로 진행합니다."; break }
}
Ok "확인 완료"

# 3. API 키 입력 및 검증
Step "OpenAI API 키 입력"
Write-Host "    platform.openai.com 에서 발급받은 키(sk-로 시작)를 붙여넣고 엔터"
Write-Host "    (Ctrl+V 또는 마우스 오른쪽 클릭. 키는 별표(*)로 표시되거나 아무것도 안 보일 수 있습니다)"
$apiKey = $null
for ($i = 0; $i -lt 5; $i++) {
    $sec = Read-Host "    API 키" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    $candidate = ([Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)).Trim()
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

    if ($candidate -eq '') { Warn "입력된 값이 없습니다. Ctrl+V 또는 마우스 오른쪽 클릭으로 붙여넣고 엔터를 누르세요."; continue }
    if ($candidate -notmatch '^sk-[\x21-\x7e]+$') { Warn "API 키 형식이 아닙니다. sk- 로 시작하고 한글·공백이 없어야 합니다. 다시 입력하세요."; continue }

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-RestMethod -Uri 'https://api.openai.com/v1/models' -Headers @{ Authorization = "Bearer $candidate" } -TimeoutSec 20 | Out-Null
        Ok "키 인증 성공"
        $apiKey = $candidate
        break
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -eq 401) { Warn "OpenAI가 거부한 키입니다 (401). 키를 다시 복사해서 입력하세요."; continue }
        if ($code) { Warn "키 확인 응답 코드 $code. 키 권한 제한일 수 있어 계속 진행하고, 마지막 시험에서 다시 확인합니다." }
        else { Warn "OpenAI에 접속하지 못했습니다 ($($_.Exception.Message)). 계속 진행하고, 마지막 시험에서 다시 확인합니다." }
        $apiKey = $candidate
        break
    }
}
if (-not $apiKey) { Fail "유효한 키를 받지 못했습니다. install.bat을 다시 실행하세요. (설정은 바뀌지 않았습니다)" }

# 4. .claude.json 에 MCP 서버 등록 (백업 후 병합)
Step "Claude Code에 MCP 서버 등록"
if (Test-Path $claudeJson) {
    $backup = "$claudeJson.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $claudeJson $backup
    Ok "기존 설정 백업: $backup"
}

$env:CLAUDE_JSON    = $claudeJson
$env:SERVER_NAME    = $ServerName
$env:PACKAGE_NAME   = $PackageName
$env:MCP_OPENAI_KEY = $apiKey

Run-Js 'merge-claude-mcp.js' @'
const fs = require('fs');
const file = process.env.CLAUDE_JSON;
let cfg = {};
if (fs.existsSync(file)) {
  const raw = (s => s.charCodeAt(0) === 0xFEFF ? s.slice(1) : s)(fs.readFileSync(file, 'utf8'));
  if (raw.trim()) cfg = JSON.parse(raw);
}
cfg.mcpServers = cfg.mcpServers || {};
cfg.mcpServers[process.env.SERVER_NAME] = {
  type: 'stdio',
  command: 'cmd',
  args: ['/c', 'npx', '-y', process.env.PACKAGE_NAME],
  env: { OPENAI_API_KEY: process.env.MCP_OPENAI_KEY }
};
// write to a temp file first so a crash can never leave a half-written config
const tmp = file + '.tmp-install';
fs.writeFileSync(tmp, JSON.stringify(cfg, null, 2), 'utf8');
try { fs.renameSync(tmp, file); } catch (e) { fs.unlinkSync(tmp); throw e; }
const check = JSON.parse(fs.readFileSync(file, 'utf8')).mcpServers[process.env.SERVER_NAME];
if (check.env.OPENAI_API_KEY !== process.env.MCP_OPENAI_KEY) process.exit(1);
'@
if ($JsExit -ne 0) { Fail "설정 파일 수정 실패. 기존 설정은 백업 파일로 남아 있습니다. Claude를 완전히 종료한 뒤 다시 실행하세요." }
Ok "'$ServerName' 등록 완료"

# 5. 이미지 도구 권한 허용 (선택)
Step "권한 설정 (선택)"
$ans = Read-Host "    이미지 생성 도구를 매번 묻지 않고 허용할까요? 그냥 엔터 = 예 (Y/n)"
if ($ans -eq '' -or $ans -match '^[Yyㅛ]') {
    $env:CLAUDE_SETTINGS = Join-Path (Join-Path $claudeDir '.claude') 'settings.json'
    if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_SETTINGS = Join-Path $claudeDir 'settings.json' }
    Run-Js 'merge-claude-settings.js' @'
const fs = require('fs'), path = require('path');
const file = process.env.CLAUDE_SETTINGS;
fs.mkdirSync(path.dirname(file), { recursive: true });
let s = {};
if (fs.existsSync(file)) {
  const raw = (t => t.charCodeAt(0) === 0xFEFF ? t.slice(1) : t)(fs.readFileSync(file, 'utf8'));
  if (raw.trim()) s = JSON.parse(raw);
}
s.permissions = s.permissions || {};
s.permissions.allow = s.permissions.allow || [];
const rule = 'mcp__' + process.env.SERVER_NAME;
if (!s.permissions.allow.includes(rule)) s.permissions.allow.push(rule);
fs.writeFileSync(file, JSON.stringify(s, null, 2), 'utf8');
'@
    if ($JsExit -eq 0) { Ok "매번 묻지 않도록 허용 추가" } else { Warn "권한 설정 실패 (이미지 생성에는 영향 없고, 사용할 때마다 허용 여부를 묻습니다)" }
} else {
    Ok "건너뜀"
}

# 6. 실제 동작 시험: 패키지 다운로드 → MCP 서버 연결 → (선택) 이미지 1장 생성
Step "MCP 서버 다운로드 및 연결 시험 (처음엔 몇 분 걸릴 수 있습니다)"
$ans = Read-Host "    시험용 이미지도 1장 만들까요? OpenAI 크레딧이 소량 차감됩니다. 그냥 엔터 = 예 (Y/n)"
$env:MCP_TEST_IMAGE = if ($ans -eq '' -or $ans -match '^[Yyㅛ]') { '1' } else { '0' }

$selfTestJs = @'
const { spawn, spawnSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const started = Date.now();
const child = spawn('cmd', ['/c', 'npx', '-y', process.env.PACKAGE_NAME], {
  env: { ...process.env, OPENAI_API_KEY: process.env.MCP_OPENAI_KEY }, stdio: ['pipe', 'pipe', 'pipe']
});
let buf = '', errTail = '', finished = false;
const mask = s => String(s).replace(/sk-[A-Za-z0-9_\-*]+/g, 'sk-***').replace(/\s+/g, ' ').slice(-400);
const finish = (result, detail) => {
  if (finished) return;
  finished = true;
  console.log('RESULT=' + result);
  if (detail) console.log('DETAIL=' + mask(detail));
  spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
  process.exit(0);
};
const send = m => child.stdin.write(JSON.stringify(m) + '\n');
const classify = text => {
  const t = text.toLowerCase();
  if (t.includes('verif')) return 'ORG';
  if (t.includes('quota') || t.includes('billing') || t.includes('429')) return 'CREDIT';
  if (t.includes('401') || t.includes('api key')) return 'KEY';
  if (t.includes('403') || t.includes('permission') || t.includes('scope')) return 'PERM';
  if (t.includes('connect') || t.includes('network') || t.includes('timeout') || t.includes('fetch')) return 'NET';
  return 'GENFAIL';
};
child.stdout.on('data', d => {
  buf += d;
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
    let m;
    try { m = JSON.parse(line); } catch { continue; }
    if (m.id === 1) {
      send({ jsonrpc: '2.0', method: 'notifications/initialized' });
      send({ jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name: 'list_history', arguments: {} } });
    } else if (m.id === 2) {
      if (m.error || (m.result && m.result.isError)) return finish('DBFAIL', JSON.stringify(m.error || m.result));
      if (process.env.MCP_TEST_IMAGE !== '1') return finish('CONNECTED');
      console.log('CONNECTED');
      send({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: 'generate_image', arguments: {
        prompt: 'a cute cat character, white background, simple webtoon style',
        size: '1024x1024', quality: 'low', output_path: 'install-test.png' } } });
    } else if (m.id === 3) {
      const text = JSON.stringify(m.error || m.result);
      if (m.error || m.result.isError) return finish(classify(text), text);
      const dir = process.env.OPENAI_IMAGE_OUTPUT_DIR || path.join(os.homedir(), 'Downloads', 'openai-images');
      const made = fs.existsSync(dir) && fs.readdirSync(dir).some(f =>
        /\.(png|jpe?g|webp)$/i.test(f) && fs.statSync(path.join(dir, f)).mtimeMs >= started && fs.statSync(path.join(dir, f)).size > 0);
      finish(made ? 'IMAGE_OK' : 'NOFILE', dir);
    }
  }
});
child.stderr.on('data', d => { errTail = (errTail + d).slice(-2000); });
child.on('exit', () => finish('NOSTART', errTail));
child.on('error', e => finish('NOSTART', e.message));
send({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'installer', version: '1' } } });
setTimeout(() => finish('TIMEOUT', errTail), 480000);
'@
$jsFile = Join-Path $env:TEMP 'mcp-self-test.js'
Set-Content -Path $jsFile -Value $selfTestJs -Encoding ASCII
try { $output = node $jsFile } finally { Remove-Item $jsFile -Force -ErrorAction SilentlyContinue }
Remove-Item Env:MCP_OPENAI_KEY

$output = @($output)
$result = ($output | Where-Object { $_ -like 'RESULT=*' } | Select-Object -Last 1) -replace '^RESULT=',''
$detail = ($output | Where-Object { $_ -like 'DETAIL=*' } | Select-Object -Last 1) -replace '^DETAIL=',''
if ($output -contains 'CONNECTED' -or $result -eq 'CONNECTED') { Ok "MCP 서버 연결 성공" }

$imgDir = Join-Path $env:USERPROFILE 'Downloads\openai-images'
switch ($result) {
    'IMAGE_OK'  { Ok "시험 이미지 생성 성공: $imgDir" }
    'CONNECTED' { Warn "이미지 시험은 건너뛰었습니다." }
    'ORG'       { Fail "연결은 됐지만 이미지 생성이 거부됐습니다: 조직 인증 필요. platform.openai.com 의 Verify Organization 을 끝낸 뒤 Claude에서 다시 시도하세요. (재설치 불필요)" }
    'CREDIT'    { Fail "연결은 됐지만 크레딧이 부족합니다. platform.openai.com 의 Billing 에서 충전한 뒤 Claude에서 다시 시도하세요. (재설치 불필요)" }
    'KEY'       { Fail "OpenAI가 키를 거부했습니다. 새 키를 발급받아 install.bat을 다시 실행하세요." }
    'PERM'      { Fail "이 키에 이미지 생성 권한이 없습니다. 키 권한을 All로 해서 새로 발급받아 install.bat을 다시 실행하세요." }
    'NET'       { Fail "OpenAI 접속에 실패했습니다. 회사 방화벽·VPN을 확인한 뒤 install.bat을 다시 실행하세요. 내용: $detail" }
    'NOSTART'   { Fail "MCP 서버를 받거나 켜지 못했습니다. 인터넷·회사 방화벽을 확인한 뒤 다시 실행하세요. 내용: $detail" }
    'DBFAIL'    { Fail "MCP 서버 내부 부품 오류입니다. Node.js LTS를 다시 설치한 뒤 다시 실행하세요. 내용: $detail" }
    'TIMEOUT'   { Fail "시간이 너무 오래 걸려 중단했습니다. 인터넷 상태를 확인한 뒤 다시 실행하세요. 내용: $detail" }
    default     { Fail "시험에 실패했습니다 ($result). 내용: $detail" }
}

Write-Host "`n설치 완료." -ForegroundColor Green
Write-Host "이제 Claude 앱을 실행하세요. (Claude를 켜 둔 채 설치했다면 완전히 종료 후 다시 실행)"
Write-Host "만든 이미지는 $imgDir 에 저장됩니다."

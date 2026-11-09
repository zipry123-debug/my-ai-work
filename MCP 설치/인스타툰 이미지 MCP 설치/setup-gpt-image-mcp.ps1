# Claude Code + OpenAI GPT Image MCP 자동 설치 스크립트 (Windows)
# install.bat 을 더블클릭해서 실행하세요.

$ErrorActionPreference = 'Stop'
# tell install.bat the script really started; if this never runs, policy or antivirus blocked the script
if ($env:GPTIMG_MARK) { Set-Content -LiteralPath $env:GPTIMG_MARK -Value 'started' -ErrorAction SilentlyContinue }
# company PCs with AppLocker/WDAC run scripts in Constrained Language Mode, where this installer cannot work
if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') {
    Write-Host "    [X] 이 컴퓨터는 보안 정책 때문에 PowerShell이 제한 모드로 실행되어 설치할 수 없습니다. IT 담당자에게 문의하세요." -ForegroundColor Red
    exit 1
}
# a global NODE_OPTIONS (e.g. a --require left by another tool) would break every node call below
Remove-Item Env:NODE_OPTIONS -ErrorAction SilentlyContinue
$ServerName        = 'openai-gpt-image'
$AllowedNodeMajors = @(22, 24, 26)   # 실제로 설치·실행을 확인한 버전만 허용
$PackageDir        = Join-Path $PSScriptRoot 'server'
$InstallDir        = Join-Path $env:LOCALAPPDATA 'openai-gpt-image-mcp'
$ServerEntry       = Join-Path $InstallDir 'node_modules\openai-gpt-image-mcp-server\dist\index.js'
# image history database on the local disk: SQLite (WAL) breaks on network folders and can lock up under OneDrive sync
$HistoryDb         = Join-Path $env:LOCALAPPDATA 'openai-gpt-image-mcp-data\openai-gpt-image.db'
$WorkDir           = Join-Path $env:TEMP 'gpt-image-mcp-install'
$PidFile           = Join-Path $WorkDir 'pids.txt'
$ClaudeDir         = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { $env:USERPROFILE }
$ClaudeJson        = Join-Path $ClaudeDir '.claude.json'
$SettingsJson      = if ($env:CLAUDE_CONFIG_DIR) { Join-Path $ClaudeDir 'settings.json' } else { Join-Path (Join-Path $ClaudeDir '.claude') 'settings.json' }

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    [!] $msg" -ForegroundColor Yellow }

function Remove-WorkDir {
    if (Test-Path -LiteralPath $WorkDir) { Remove-Item -LiteralPath $WorkDir -Recurse -Force -ErrorAction SilentlyContinue }
}
function Fail($msg) {
    Write-Host "    [X] $msg" -ForegroundColor Red
    Remove-WorkDir
    exit 1
}

# 예상하지 못한 오류도 창이 닫히기 전에 내용을 보여줌 (대기는 install.bat 의 pause 가 담당)
trap {
    Write-Host "`n    [X] 예상하지 못한 오류: $($_.Exception.Message)" -ForegroundColor Red
    Remove-WorkDir
    exit 1
}

function Refresh-Path {
    # drop empty entries: a PATH starting with ';' makes cmd unable to find npm
    $env:Path = (@([Environment]::GetEnvironmentVariable('Path','Machine') -split ';') + @([Environment]::GetEnvironmentVariable('Path','User') -split ';') | Where-Object { $_ }) -join ';'
}

# 임시 JS 파일로 node 실행. 결과는 한글 경로가 깨지지 않도록 UTF-8 파일로 주고받는다
function Run-Js($name, $code) {
    $jsFile = Join-Path $WorkDir $name
    $resultFile = Join-Path $WorkDir "$name.result"
    if (Test-Path -LiteralPath $resultFile) { Remove-Item -LiteralPath $resultFile -Force }
    Set-Content -LiteralPath $jsFile -Value ($JsPrelude + "`n" + $code) -Encoding ASCII
    $env:MCP_RESULT = $resultFile
    node $jsFile
    $script:JsExit = $LASTEXITCODE
    $script:JsOut = if (Test-Path -LiteralPath $resultFile) { [IO.File]::ReadAllLines($resultFile, [Text.Encoding]::UTF8) } else { @() }
}
function Get-Value($prefix) {
    $line = $script:JsOut | Where-Object { $_.StartsWith("$prefix=") } | Select-Object -Last 1
    if ($line) { return $line.Substring($prefix.Length + 1) }
    return ''
}

$JsPrelude = @'
const fs = require('fs');
const say = line => fs.appendFileSync(process.env.MCP_RESULT, line + '\n', 'utf8');
const mask = s => String(s).replace(/sk-[A-Za-z0-9_\-*]+/g, 'sk-***').replace(/\s+/g, ' ').slice(-400);
const sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const LOCK_CODES = ['EPERM', 'EBUSY', 'EACCES', 'ENOTEMPTY'];
const retry = f => { for (let i = 0; ; i++) { try { return f(); } catch (e) { if (i >= 4 || !LOCK_CODES.includes(e.code)) throw e; sleep(2000); } } };
// numbers are kept exactly as written: a plain parse would round big integers and long decimals when the file is saved back
const keepNumber = (k, v, c) => (typeof v === 'number' && c && typeof c.source === 'string' && String(v) !== c.source && typeof JSON.rawJSON === 'function') ? JSON.rawJSON(c.source) : v;
const readJson = file => JSON.parse((s => s.charCodeAt(0) === 0xFEFF ? s.slice(1) : s)(fs.readFileSync(file, 'utf8')) || '{}', keepNumber);
const isObj = v => !!v && typeof v === 'object' && !Array.isArray(v);
// write through a temp file so a crash cannot leave half a file; a hard-linked file (settings sync tools) is written in place so the link survives
const saveJson = (file, obj) => {
  const text = JSON.stringify(obj, null, 2);
  let links = 1; try { links = fs.statSync(file).nlink; } catch {}
  if (links > 1) { retry(() => fs.writeFileSync(file, text, 'utf8')); return; }
  const tmp = file + '.tmp-install';
  fs.writeFileSync(tmp, text, 'utf8');
  try { retry(() => fs.renameSync(tmp, file)); } catch (e) { try { fs.unlinkSync(tmp); } catch {} throw e; }
};
// own recursive delete: fs.rmSync in Node 24.0.x crashes the process (0xC0000409) on paths with Korean or other non-ASCII characters
// anything that disappears while deleting (antivirus, a finishing process) counts as deleted
const gone = f => { try { f(); } catch (e) { if (e.code !== 'ENOENT') throw e; } };
const rmrf = p => {
  let st; try { st = fs.lstatSync(p); } catch (e) { if (e.code === 'ENOENT') return; throw e; }
  if (st.isDirectory() && !st.isSymbolicLink()) {
    let names = []; gone(() => { names = fs.readdirSync(p); });
    for (const n of names) rmrf(require('path').join(p, n));
    gone(() => fs.rmdirSync(p)); return;
  }
  try { fs.unlinkSync(p); } catch (e) {
    if (e.code === 'ENOENT') return;
    if (e.code === 'EPERM' && !st.isSymbolicLink()) { gone(() => fs.chmodSync(p, 0o666)); gone(() => fs.unlinkSync(p)); }
    else if (st.isSymbolicLink()) gone(() => fs.rmdirSync(p));
    else throw e;
  }
};
// absolute paths: a PATH without System32 must not stop cmd or taskkill
const sys32 = exe => { const p = require('path').join(process.env.SystemRoot || 'C:\\Windows', 'System32', exe); return fs.existsSync(p) ? p : exe; };
'@

# 실제 다운로드 폴더 (OneDrive 등으로 옮겨진 경우 포함)
function Get-DownloadsFolder {
    try {
        $p = (New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    } catch { }
    try {
        $p = (Get-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders').'{374DE290-123F-4565-9164-39C4925E467B}'
        if ($p) { $p = [Environment]::ExpandEnvironmentVariables($p); if (Test-Path -LiteralPath $p) { return $p } }
    } catch { }
    return (Join-Path $env:USERPROFILE 'Downloads')
}

# 파일 복사도 Claude·OneDrive·백신이 잠그고 있을 수 있어 재시도
function Copy-WithRetry($from, $to) {
    for ($i = 0; $i -lt 5; $i++) {
        try { Copy-Item -LiteralPath $from -Destination $to -Force; return $true }
        catch { if ($i -lt 4) { Start-Sleep -Seconds 2 } }
    }
    return $false
}
# only backups this installer made (prefix + yyyyMMdd-HHmmss) are rotated; a user's own "backup-mine" is never touched
function Keep-NewestBackups($dir, $prefix, $keep) {
    $pattern = '^' + [regex]::Escape($prefix) + '\d{8}-\d{6}$'
    Get-ChildItem -LiteralPath $dir -Force -File -Filter "$prefix*" | Where-Object { $_.Name -match $pattern } | Sort-Object Name -Descending | Select-Object -Skip $keep |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
}
# fixed digits whatever the display language (a Thai setting would otherwise write year 2569 and break the order)
function Get-Stamp { (Get-Date).ToString('yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture) }
# a folder that policy makes read-only would otherwise fail later as "file in use"
function Test-Writable($dir) {
    try {
        [void][IO.Directory]::CreateDirectory($dir)
        $probe = Join-Path $dir ".write-test-$PID"
        [IO.File]::WriteAllText($probe, 'x'); Remove-Item -LiteralPath $probe -Force
        return $true
    } catch [UnauthorizedAccessException] { return $false }
    catch { return $true }
}
$NoWriteMessage = "이 폴더에 파일을 쓸 권한이 없습니다. 회사 PC라면 보안 정책 때문일 수 있으니 IT 담당자에게 문의하세요."

$LockedMessage = "다른 프로그램이 파일을 사용 중이거나 파일이 읽기 전용입니다. Claude를 트레이까지 완전히 종료하고, OneDrive 동기화 일시 중지와 백신 검사 완료, 파일 속성의 읽기 전용 해제를 확인한 뒤 install.bat을 다시 실행하세요."

# 0. 사람이 직접 입력할 수 있는 환경인지 확인
$cmdArgs = [Environment]::GetCommandLineArgs()
if ([Console]::IsInputRedirected -or -not [Environment]::UserInteractive -or ($cmdArgs | Where-Object { $_ -match '^-noni' })) {
    Write-Host "    [X] 직접 입력할 수 없는 환경입니다. 파일 탐색기에서 install.bat을 더블클릭해서 실행하세요." -ForegroundColor Red
    exit 1
}

# 창을 두 개 열면 서로의 임시 폴더와 설치 폴더를 건드리므로 하나만 실행 (창이 닫히면 자동 해제)
$SetupMutex = New-Object Threading.Mutex($false, 'Local\openai-gpt-image-mcp-setup')
try { $gotMutex = $SetupMutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $gotMutex = $true }
if (-not $gotMutex) {
    Write-Host "    [X] 설치 또는 제거 창이 이미 열려 있습니다. 그 창이 끝난 뒤 다시 실행하세요." -ForegroundColor Red
    exit 1
}

# 이전 실행이 남긴 시험 프로세스와 임시 파일 정리 (기록된 PID 중 이 설치의 프로세스만 종료)
if (Test-Path -LiteralPath $PidFile) {
    foreach ($oldPid in (Get-Content -LiteralPath $PidFile)) {
        if ($oldPid -notmatch '^\d+$') { continue }
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$oldPid" -ErrorAction SilentlyContinue
        if ($proc -and $proc.CommandLine -like '*gpt-image-mcp-install*') { Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue }
    }
}
Remove-WorkDir
foreach ($leftover in "$ClaudeJson.tmp-install", "$SettingsJson.tmp-install") {
    if (Test-Path -LiteralPath $leftover) { Remove-Item -LiteralPath $leftover -Force -ErrorAction SilentlyContinue }
}
if (-not (Test-Writable $WorkDir)) { Write-Host "    [X] 임시 폴더($env:TEMP)에 $NoWriteMessage" -ForegroundColor Red; exit 1 }

# 1. ARM 윈도우 차단 (이 패키지의 sharp 버전에 ARM용 파일이 없음)
Step "컴퓨터 종류 확인"
$arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
$cpuArch = $null
try { $cpuArch = @(Get-CimInstance Win32_Processor -ErrorAction Stop | ForEach-Object { $_.Architecture }) } catch { }
if ($arch -match 'ARM' -or $cpuArch -contains 12) { Fail "ARM 윈도우(스냅드래곤 등)는 현재 지원하지 않습니다. 이미지 생성 부품에 ARM용 파일이 없습니다." }
if (-not (Test-Path -LiteralPath (Join-Path $PackageDir 'package-lock.json'))) { Fail "server 폴더를 찾지 못했습니다. ZIP 압축을 푼 폴더 안에서 install.bat을 실행하세요." }
# the image library cannot load its DLLs from a folder whose path contains ';'
if ($InstallDir.Contains(';')) { Fail "설치 위치 경로에 ';' 문자가 있어 이미지 부품이 동작하지 않습니다: $InstallDir" }
# Windows cannot start a program inside a folder whose path passes 260 characters; npm and the parts downloader start in
# "<install>.new" and "<install>.new\node_modules\better-sqlite3" (about 35 characters more), so keep a margin
if ($InstallDir.Length -gt 200) { Fail "설치 위치 경로가 너무 깁니다 ($($InstallDir.Length)자): $InstallDir" }
if (-not (Test-Writable $env:LOCALAPPDATA)) { Fail "설치 위치($env:LOCALAPPDATA)에 $NoWriteMessage" }

# running elevated as another account would install into that account's profile, not the signed-in user's Claude
$me = [Security.Principal.WindowsIdentity]::GetCurrent()
if ((New-Object Security.Principal.WindowsPrincipal($me)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $DesktopUserOverride = $null
    $desk = $DesktopUserOverride
    if (-not $desk) {
        try {
            $sid = (Get-Process -Id $PID).SessionId
            $ex = Get-CimInstance Win32_Process -Filter "Name='explorer.exe' AND SessionId=$sid" -ErrorAction Stop | Select-Object -First 1
            if ($ex) { $desk = (Invoke-CimMethod -InputObject $ex -MethodName GetOwner -ErrorAction Stop).User }
        } catch { }
    }
    if ($desk -and $desk -ne $env:USERNAME) { Fail "다른 계정($env:USERNAME)의 관리자 권한으로 실행됐습니다. 이대로면 지금 로그인한 사용자($desk)의 Claude에 연결되지 않습니다. install.bat을 오른쪽 클릭 '관리자 권한으로 실행' 없이 그냥 더블클릭하세요." }
}

# Smart App Control may block the unsigned image parts; warn now so a later load failure makes sense
$SacOverride = $null
$sac = $SacOverride
if (-not $sac) { try { $sac = (Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' -ErrorAction Stop).VerifiedAndReputablePolicyState } catch { } }
$SacOn = "$sac" -eq '1'
if ($SacOn) { Warn "스마트 앱 컨트롤이 켜져 있습니다. 이미지 부품(서명 없는 파일)이 차단되면 '서버 부품을 불러오지 못했습니다'로 멈출 수 있습니다." }

# a full disk fails midway with confusing npm errors, so check first (install about 60MB, plus download cache)
$NeedMB = 500
foreach ($p in @($env:LOCALAPPDATA, $env:TEMP)) {
    try { $root = [IO.Path]::GetPathRoot($p); $freeMB = [math]::Floor((New-Object IO.DriveInfo($root)).AvailableFreeSpace / 1MB) } catch { continue }
    if ($freeMB -lt $NeedMB) { Fail "디스크 공간이 부족합니다 ($root 남은 공간 ${freeMB}MB). ${NeedMB}MB 이상 비운 뒤 다시 실행하세요." }
}
Ok "지원하는 컴퓨터입니다"

# 2. Node.js 확인/설치
Step "Node.js 확인"
Refresh-Path
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Warn "Node.js가 없습니다. winget으로 설치를 시도합니다 (관리자 승인 창이 뜰 수 있음)."
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail "winget이 없어 자동 설치를 못 합니다. https://nodejs.org/dist/latest-v24.x/ 에서 x64 msi를 직접 설치한 뒤 다시 실행하세요."
    }
    winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
    Refresh-Path
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Fail "자동 설치에 실패했습니다. 관리자 권한이 없거나 승인을 거절했을 수 있습니다. https://nodejs.org/dist/latest-v24.x/ 에서 x64 msi를 직접 설치한 뒤 다시 실행하세요. (회사 노트북이면 IT 담당자에게 요청)"
    }
}
# a broken node or wrapper in PATH prints nothing; say so instead of crashing on an empty version
$nodeVer = "$(node -v)".Trim().TrimStart('v')
if ($nodeVer -notmatch '^\d+\.') { Fail "Node.js가 실행되지 않습니다 ($((Get-Command node).Source)). https://nodejs.org/dist/latest-v24.x/ 에서 x64 msi로 Node.js를 다시 설치한 뒤 다시 실행하세요." }
$nodeMajor = [int]($nodeVer.Split('.')[0])
if ($AllowedNodeMajors -notcontains $nodeMajor) {
    Fail "Node.js $nodeVer ($((Get-Command node).Source)) 은 지원하지 않습니다. 설치와 실행을 확인한 버전은 22, 24, 26 뿐입니다. https://nodejs.org/dist/latest-v24.x/ 에서 Node.js 24를 설치한 뒤 다시 실행하세요. 이미 설치했는데도 이 메시지가 나오면 위 경로의 예전 Node.js를 제거하세요."
}
$nodeArch = "$(node -p "process.arch")".Trim()
if ($nodeArch -ne 'x64') { Fail "Node.js $nodeVer ($nodeArch) 은 지원하지 않습니다. 64비트(x64)용만 지원합니다. https://nodejs.org/dist/latest-v24.x/ 에서 x64 msi를 설치한 뒤 다시 실행하세요." }
# the real node.exe, not a wrapper such as node.cmd that comes first in PATH (Claude cannot start a .cmd directly)
$NodeExe = "$(node -p "process.execPath")".Trim()
if (-not $NodeExe -or -not (Test-Path -LiteralPath $NodeExe)) { $NodeExe = (Get-Command node).Source }
# npm is run from this node's own folder; any npm in PATH is only a fallback
if (-not (Test-Path -LiteralPath (Join-Path (Split-Path $NodeExe) 'node_modules\npm\bin\npm-cli.js')) -and -not (Get-Command npm -ErrorAction SilentlyContinue)) { Fail "npm을 찾지 못했습니다. https://nodejs.org/dist/latest-v24.x/ 에서 Node.js를 다시 설치하세요." }
Ok "Node.js v$nodeVer"

# 3. Claude 종료 확인 (켜져 있으면 설정 변경이 덮어써지거나 서버 파일이 잠길 수 있음)
Step "Claude 종료 확인"
while (Get-Process -Name claude -ErrorAction SilentlyContinue) {
    Warn "Claude가 실행 중입니다. 창을 닫고, 작업 표시줄 오른쪽 아래 트레이 아이콘에서도 종료해 주세요."
    $ans = Read-Host "    종료했으면 엔터 (Claude Code 안에서 실행 중이거나 그대로 진행하려면 s 입력 후 엔터)"
    if ($ans -match '^[sSㄴ]') { Warn "Claude가 켜진 채로 진행합니다. 끝나면 Claude를 완전히 종료 후 다시 실행하세요."; break }
}
Ok "확인 완료"

# 4. 접속 확인
Step "인터넷 접속 확인"
Run-Js 'preflight.js' @'
const https = require('https');
// resolves to '' when reachable, otherwise the reason, so a certificate problem is not reported as a firewall
const check = host => new Promise(done => {
  const req = https.request({ host, port: 443, method: 'HEAD', path: '/', timeout: 12000 }, res => { res.resume(); done(''); });
  req.on('timeout', () => { done('TIMEOUT'); req.destroy(); });
  req.on('error', e => done(e.code || 'ERROR'));
  req.end();
});
(async () => {
  // release-assets.githubusercontent.com serves the image part download that github.com redirects to
  for (const host of ['registry.npmjs.org', 'github.com', 'release-assets.githubusercontent.com', 'api.openai.com']) {
    const why = (await check(host)) && (await check(host));
    if (why) say('BLOCKED=' + host + ' ' + why);
  }
  say('DONE=1');
})();
'@
if ((Get-Value 'DONE') -ne '1') { Fail "접속 확인을 실행하지 못했습니다. Node.js를 다시 설치한 뒤 다시 실행하세요." }
$blocked = @($script:JsOut | Where-Object { $_ -like 'BLOCKED=*' } | ForEach-Object { $_.Substring(8) })
if ($blocked.Count -gt 0) {
    foreach ($h in $blocked) { Write-Host "    [X] 접속 불가: $h" -ForegroundColor Red }
    if ($blocked -match 'CERT|UNABLE_TO_VERIFY') { Fail "보안 연결 검사에서 막혔습니다. 카페·호텔 같은 공용 와이파이라면 브라우저에서 와이파이 로그인 화면을 먼저 끝내세요. 아니라면 컴퓨터의 날짜와 시간이 맞는지 확인하고, 맞다면 백신의 HTTPS(웹) 검사나 회사 보안 장비가 연결을 가로채는 경우입니다. 백신의 해당 기능을 끄거나 IT 담당자에게 문의한 뒤 다시 실행하세요." }
    Fail "위 주소에 접속하지 못해 중단합니다. 인터넷 연결을 확인하세요. 회사 방화벽·프록시·VPN이 막고 있다면 IT 담당자에게 허용을 요청하세요. (프록시 환경은 지원이 확인되지 않았습니다)"
}
Ok "registry.npmjs.org, github.com, githubusercontent.com, api.openai.com 접속 가능"

# 5. 고정된 버전으로 MCP 서버 설치 (package-lock.json 기준 npm ci)
Step "MCP 서버 설치 (처음엔 1~2분 걸릴 수 있습니다)"
$env:MCP_SRC  = $PackageDir
$env:MCP_DEST = $InstallDir
$env:MCP_WORK = $WorkDir
Run-Js 'install-server.js' @'
const path = require('path'), { spawnSync } = require('child_process');
const src = process.env.MCP_SRC, dest = process.env.MCP_DEST, neu = dest + '.new', old = dest + '.old';
const entry = d => path.join(d, 'node_modules', 'openai-gpt-image-mcp-server', 'dist', 'index.js');
const same = (a, b) => { try { return fs.readFileSync(a).equals(fs.readFileSync(b)); } catch { return false; } };
const LOAD = "const {createRequire}=require('module');const r=createRequire(process.env.D+'/x.js');const S=r('better-sqlite3');new S(':memory:').close();r('sharp');";
const loads = d => spawnSync(process.execPath, ['-e', LOAD], { env: { ...process.env, D: d }, encoding: 'utf8' }).status === 0;
// a missing dependency only shows when the server really starts, so ask it to answer one handshake
const HELLO = JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'installer', version: '1' } } }) + '\n';
const answers = d => /"id":1\b/.test(spawnSync(process.execPath, [entry(d)], { input: HELLO, encoding: 'utf8', timeout: 60000,
  env: { ...process.env, OPENAI_API_KEY: 'sk-install-check', OPENAI_IMAGE_OUTPUT_DIR: path.join(process.env.MCP_WORK, 'server-check'), HISTORY_DB_PATH: path.join(process.env.MCP_WORK, 'server-check', 'check.db') } }).stdout || '');
const healthy = d => fs.existsSync(entry(d)) && loads(d) && answers(d);
// removing a leftover folder must never replace the real result with a lock message
const tidy = d => { try { retry(() => rmrf(d)); } catch {} };
// the package hardcodes gpt-image-1 as its default, which OpenAI has shut down; change the installed copy only
const setDefaultModel = d => {
  const root = path.join(d, 'node_modules', 'openai-gpt-image-mcp-server', 'dist');
  const edits = [
    ['tools/generate.js', "model = 'gpt-image-1',", "model = 'gpt-image-2',"],
    ['tools/edit.js', "model = 'gpt-image-1',", "model = 'gpt-image-2',"],
    ['tools/transform.js', "model = 'gpt-image-1',", "model = 'gpt-image-2',"],
    ['utils/image.js', "model = 'gpt-image-1')", "model = 'gpt-image-2')"],
    ['utils/cost.js', "params.model || 'gpt-image-1'", "params.model || 'gpt-image-2'"],
    ['index.js', '(default: gpt-image-1)', '(default: gpt-image-2)']
  ];
  for (const [rel, from, to] of edits) {
    const file = path.join(root, rel);
    const text = fs.readFileSync(file, 'utf8');
    if (text.includes(from)) fs.writeFileSync(file, text.split(from).join(to), 'utf8');
    else if (!text.includes(to)) throw new Error('default model text not found: ' + rel);
  }
};
try {
  if (same(path.join(src, 'package-lock.json'), path.join(dest, 'package-lock.json')) && healthy(dest)) {
    setDefaultModel(dest);
    tidy(old); tidy(neu);
    say('RESULT=ALREADY'); process.exit(0);
  }
  retry(() => rmrf(neu));
  retry(() => rmrf(old));
  fs.mkdirSync(neu, { recursive: true });
  for (const f of ['package.json', 'package-lock.json']) fs.copyFileSync(path.join(src, f), path.join(neu, f));
  const failed = (reason, r) => {
    const log = (r.stdout || '') + (r.stderr || '') + (r.error ? r.error.message : '');
    const lines = log.split(/\r?\n/).filter(l => !/^npm (notice|warn)/.test(l));
    // keep npm's error code lines in front: the shown detail is cut to its last part
    const codes = lines.filter(l => /npm (error|ERR!) (code|errno|syscall)\b/.test(l)).join(' ');
    say('RESULT=NPMFAIL'); say('REASON=' + reason); say('DETAIL=' + mask(codes).slice(0, 150) + ' | ' + mask(lines.join(' ')).slice(-250));
    tidy(neu);
    process.exit(0);
  };
  // no install scripts: a failed native download must not fall back to node-gyp, which can launch Python or Visual Studio tools
  // /d skips cmd AutoRun hooks (conda init etc.), which can change the folder or PATH before npm runs
  // explicit values override user npm settings (global, dry-run, offline, package-lock=false) that would make npm ci fail or install nothing
  // the connection check above went direct and succeeded, so a leftover proxy setting must not send npm or the binary download elsewhere
  // Electron or cross-platform settings in the environment would make prebuild-install fetch the wrong binary
  const direct = env => Object.fromEntries(Object.entries(env).filter(([k]) => !/^(https?_proxy|npm_config_((https_)?proxy|runtime|target|arch|platform|libc|disturl|build_from_source))$/i.test(k)));
  // the registry is the one the connection check reached; os/cpu pin the Windows x64 image parts
  // a user ca/cafile setting that is broken or missing would fail every download; the connection check above trusted Node's own root list, so npm uses the same
  const roots = path.join(process.env.MCP_WORK, 'roots.pem');
  fs.writeFileSync(roots, require('tls').rootCertificates.join('\n'));
  // fetch-timeout/fetch-retries replace extreme user values (1 ms, 0 retries) that fail on any slow or flaky connection
  const FLAGS = ['ci', '--include=optional', '--ignore-scripts', '--global=false', '--dry-run=false', '--offline=false', '--package-lock=true', '--proxy=false', '--https-proxy=false', '--registry=https://registry.npmjs.org/', '--os=win32', '--cpu=x64', '--cafile=' + roots, '--fetch-timeout=300000', '--fetch-retries=5', '--no-audit', '--no-fund', '--loglevel=error'];
  // run the npm that belongs to this node, not whichever npm.cmd comes first in PATH (it may belong to an old Node)
  const npmCli = path.join(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js');
  const npmCi = env => fs.existsSync(npmCli)
    ? spawnSync(process.execPath, [npmCli, ...FLAGS], { cwd: neu, encoding: 'utf8', timeout: 600000, env: direct(env) })
    : spawnSync(sys32('cmd.exe'), ['/d', '/c', 'npm', ...FLAGS], { cwd: neu, encoding: 'utf8', timeout: 600000, env: direct(env) });
  const logOf = r => (r.stdout || '') + (r.stderr || '') + (r.error ? r.error.message : '');
  const NET = /ECONNREFUSED|ENOTFOUND|ETIMEDOUT|ECONNRESET|EAI_AGAIN|SELF_SIGNED|CERT_|network/i;
  const DISK = /ENOSPC|no space left/i;
  const fresh = { ...process.env, npm_config_cache: path.join(process.env.MCP_WORK, 'npm-cache') };
  let r = npmCi(process.env);
  // the connection check passed moments ago, so a network error here is often a short drop: wait and try once more
  if (r.status !== 0 && NET.test(logOf(r))) {
    tidy(path.join(neu, 'node_modules'));
    sleep(15000);
    r = npmCi(process.env);
  }
  // npm's download cache on Windows sometimes fails with EEXIST/EPERM (antivirus, indexer); retry once with a fresh private cache
  if (r.status !== 0 && !NET.test(logOf(r)) && !DISK.test(logOf(r))) {
    tidy(path.join(neu, 'node_modules'));
    r = npmCi(fresh);
  }
  if (r.status !== 0) failed(DISK.test(logOf(r)) ? 'DISK' : NET.test(logOf(r)) ? 'NET' : 'OTHER', r);
  const nm = path.join(neu, 'node_modules');
  // npm silently skips an optional part (sharp's Windows binary) when its download fails, so check the parts and try once more
  const partsOk = () => ['prebuild-install/bin.js', 'better-sqlite3/package.json', '@img/sharp-win32-x64/package.json'].every(p => fs.existsSync(path.join(nm, p)));
  if (!partsOk()) {
    tidy(nm);
    r = npmCi(fresh);
    if (r.status !== 0 || !partsOk()) failed('PARTS', { stdout: 'npm finished but some parts were not downloaded. ' + logOf(r) });
  }
  // GitHub sometimes answers the binary download with a temporary error, which prebuild-install reports as "No prebuilt binaries found";
  // wait and retry, and use the fresh cache last in case the user's npm cache is broken
  let p;
  for (const [wait, env] of [[0, process.env], [10000, process.env], [20000, fresh], [40000, fresh], [60000, fresh]]) {
    if (wait) sleep(wait);
    p = spawnSync(process.execPath, [path.join(nm, 'prebuild-install', 'bin.js'), '--runtime=node', '--target=' + process.versions.node, '--arch=x64', '--platform=win32'], { cwd: path.join(nm, 'better-sqlite3'), encoding: 'utf8', timeout: 300000, env: direct(env) });
    if (p.status === 0) break;
  }
  if (p.status !== 0) failed('NATIVE', p);
  if (!healthy(neu)) {
    say('RESULT=LOADFAIL');
    tidy(neu);
    process.exit(0);
  }
  setDefaultModel(neu);
  if (fs.existsSync(dest)) retry(() => fs.renameSync(dest, old));
  try { retry(() => fs.renameSync(neu, dest)); }
  catch (e) { if (fs.existsSync(old)) fs.renameSync(old, dest); throw e; }
  tidy(old);
  say('RESULT=INSTALLED');
} catch (e) {
  say('RESULT=' + (LOCK_CODES.includes(e.code) ? 'LOCKED' : 'ERROR')); say('DETAIL=' + mask(e.message));
}
'@
switch (Get-Value 'RESULT') {
    'ALREADY'   { Ok "이미 같은 버전이 설치되어 있어 건너뜁니다" }
    'INSTALLED' { Ok "설치 완료: $InstallDir" }
    'LOCKED'    { Fail "설치 폴더를 바꾸지 못했습니다. $LockedMessage" }
    'LOADFAIL'  { Fail ("서버 부품을 불러오지 못했습니다. " + $(if ($SacOn) { "스마트 앱 컨트롤이 서명 없는 부품을 차단했을 가능성이 큽니다. " } else { "" }) + "백신이 부품 파일을 격리했을 수 있으니 백신 검역소를 확인한 뒤 install.bat을 다시 실행하세요. 계속되면 https://nodejs.org/dist/latest-v24.x/ 에서 Node.js를 다시 설치한 뒤 다시 실행하세요.") }
    'NPMFAIL'   {
        $detail = Get-Value 'DETAIL'
        switch (Get-Value 'REASON') {
            'NATIVE' { Fail "이미지 부품(better-sqlite3)을 받지 못했습니다. GitHub의 일시적인 문제일 수 있으니 몇 분 뒤 install.bat을 다시 실행하세요. 계속 실패하면 github.com 의 파일 다운로드가 막힌 것이니, 회사망이면 IT 담당자에게 github.com 과 githubusercontent.com 허용을 요청하세요. 내용: $detail" }
            'PARTS'  { Fail "이미지 부품 일부(sharp)를 받지 못했습니다. 인터넷이 잠깐 끊겼을 수 있으니 install.bat을 다시 실행하세요. 계속되면 회사 방화벽에서 registry.npmjs.org 허용 여부를 확인하세요. 내용: $detail" }
            'DISK'   { Fail "디스크 공간이 부족해 설치하지 못했습니다. C 드라이브에서 500MB 이상 비운 뒤 다시 실행하세요. 내용: $detail" }
            'NET'    { Fail "npm 저장소에서 내려받지 못했습니다. 인터넷·회사 방화벽을 확인한 뒤 다시 실행하세요. 내용: $detail" }
            default  { Fail "npm 설치에 실패했습니다. 인터넷 연결을 확인한 뒤 다시 실행하세요. 계속되면 이 창의 내용을 보내 주세요. 내용: $detail" }
        }
    }
    default     { Fail "서버 설치 중 오류가 났습니다. 내용: $(Get-Value 'DETAIL')" }
}

# 6. API 키 입력 및 검증
Step "OpenAI API 키 입력"
Write-Host "    platform.openai.com 에서 발급받은 키(sk-로 시작)를 붙여넣고 엔터"
Write-Host "    (Ctrl+V 또는 마우스 오른쪽 클릭. 키는 별표(*)로 표시되거나 아무것도 안 보일 수 있습니다)"
$KeyCheckJs = @'
const KEYCHECK = 1;
const https = require('https');
const req = https.request({ host: 'api.openai.com', path: '/v1/models', method: 'GET', timeout: 20000,
  headers: { Authorization: 'Bearer ' + process.env.MCP_KEY_CANDIDATE } }, res => { res.resume(); say('STATUS=' + res.statusCode); res.on('end', () => process.exit(0)); });
req.on('timeout', () => { say('ERR=timeout'); req.destroy(); process.exit(0); });
req.on('error', e => { say('ERR=' + mask(e.code || e.message)); process.exit(0); });
req.end();
'@
$apiKey = $null
for ($i = 0; $i -lt 5; $i++) {
    $sec = Read-Host "    API 키" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    $candidate = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    # text copied from chats or documents can carry invisible characters, quotes or a "Bearer " prefix
    $candidate = ($candidate -replace '[\u200B-\u200D\u2060\uFEFF]', '').Trim().Trim('"', "'", '`', [char]0x201C, [char]0x201D, [char]0x2018, [char]0x2019).Trim()
    # a whole line from a .env file or a shell export
    $candidate = ($candidate -creplace '^(export\s+|set\s+)?OPENAI_API_KEY\s*[=:]\s*', '').Trim().Trim('"', "'").Trim()
    # case-sensitive matching throughout: a Turkish language setting changes how I and i compare without it
    $candidate = ($candidate -creplace '^[Bb][Ee][Aa][Rr][Ee][Rr]\s+', '').Trim()

    if ($candidate -eq '') { Warn "입력된 값이 없습니다. Ctrl+V 또는 마우스 오른쪽 클릭으로 붙여넣고 엔터를 누르세요."; continue }
    if ($candidate.StartsWith('sk-ant-')) { Warn "Anthropic(Claude)의 키입니다. platform.openai.com 에서 발급한 OpenAI 키(sk-로 시작)가 필요합니다."; continue }
    if ($candidate -cmatch '^(org-|proj_)') { Warn "조직 ID 또는 프로젝트 ID입니다. platform.openai.com 의 API keys 메뉴에서 만든, sk- 로 시작하는 키를 붙여넣으세요."; continue }
    if ($candidate.Length -gt 3 -and $candidate.Substring(3).Contains('sk-')) { Warn "키를 두 번 붙여넣은 것 같습니다. 한 번만 붙여넣고 엔터를 누르세요."; continue }
    if ($candidate -cnotmatch '^sk-[\x21-\x7e]+$') { Warn "API 키 형식이 아닙니다. sk- 로 시작하고 한글·공백이 없어야 합니다. 다시 입력하세요."; continue }

    # checked in node with the key in an environment variable: a PowerShell cmdlet parameter would be written to the event log on PCs with module logging
    $env:MCP_KEY_CANDIDATE = $candidate
    Run-Js 'keycheck.js' $KeyCheckJs
    Remove-Item Env:MCP_KEY_CANDIDATE
    $code = Get-Value 'STATUS'
    if ($code -match '^2\d\d$') { Ok "키 인증 성공"; $apiKey = $candidate; break }
    if ($code -eq '401') { Warn "OpenAI가 거부한 키입니다 (401). 키를 다시 복사해서 입력하세요."; continue }
    if ($code) { Warn "키 확인 응답 코드 $code. 키 권한 제한일 수 있어 계속 진행하고, 마지막 시험에서 다시 확인합니다." }
    else { Warn "키를 확인하지 못했습니다 ($(Get-Value 'ERR')). 계속 진행하고, 마지막 시험에서 다시 확인합니다." }
    $apiKey = $candidate
    break
}
if (-not $apiKey) { Fail "유효한 키를 받지 못했습니다. install.bat을 다시 실행하세요. (Claude 설정은 바뀌지 않았습니다)" }

# 7. .claude.json 에 MCP 서버 등록 (백업 후 병합)
Step "Claude Code에 MCP 서버 등록"
if (-not (Test-Writable $ClaudeDir)) { Fail "Claude 설정 폴더($ClaudeDir)에 $NoWriteMessage (Claude 설정은 바뀌지 않았습니다)" }
# a relative OPENAI_IMAGE_OUTPUT_DIR would be resolved against whatever folder Claude starts in, so use only a full path
$ImageDir = Join-Path (Get-DownloadsFolder) 'openai-images'
if ($env:OPENAI_IMAGE_OUTPUT_DIR) {
    if ($env:OPENAI_IMAGE_OUTPUT_DIR -match '^([A-Za-z]:\\|\\\\)') { $ImageDir = $env:OPENAI_IMAGE_OUTPUT_DIR }
    else { Warn "환경변수 OPENAI_IMAGE_OUTPUT_DIR($env:OPENAI_IMAGE_OUTPUT_DIR)이 전체 경로가 아니어서 무시하고 기본 위치를 씁니다: $ImageDir" }
}
# the server cannot start its tools if the image folder cannot be created, so check before changing any setting
try { [void][IO.Directory]::CreateDirectory($ImageDir) } catch { Fail "이미지 저장 폴더를 만들 수 없습니다: $ImageDir  같은 이름의 파일이 있거나 쓰기 권한이 없습니다. 그 파일의 이름을 바꾸거나 지운 뒤 다시 실행하세요. (Claude 설정은 바뀌지 않았습니다)" }
$backup = $null
if (Test-Path -LiteralPath $ClaudeJson) {
    $backup = "$ClaudeJson.backup-$(Get-Stamp)"
    if (-not (Copy-WithRetry $ClaudeJson $backup)) { Fail "기존 설정을 백업하지 못해 아무것도 바꾸지 않았습니다. $LockedMessage" }
    Keep-NewestBackups $ClaudeDir '.claude.json.backup-' 3
    Ok "기존 설정 백업: $backup (키가 든 백업은 최근 3개만 보관)"
}

$env:CLAUDE_JSON    = $ClaudeJson
$env:SERVER_NAME    = $ServerName
$env:MCP_NODE       = $NodeExe
$env:MCP_ENTRY      = $ServerEntry
$env:MCP_IMAGE_DIR  = $ImageDir
$env:MCP_HISTORY_DB = $HistoryDb
$env:MCP_OPENAI_KEY = $apiKey
$env:CLAUDE_SETTINGS_FILE = $SettingsJson

Run-Js 'register.js' @'
const path = require('path');
const file = process.env.CLAUDE_JSON, name = process.env.SERVER_NAME;
let cfg = {};
try {
  if (fs.existsSync(file)) { const raw = retry(() => fs.readFileSync(file, 'utf8')); if (raw.trim()) cfg = readJson(file); }
} catch (e) { if (e instanceof SyntaxError) { say('RESULT=BADJSON'); process.exit(0); } say('RESULT=LOCKED'); process.exit(0); }
// valid JSON of the wrong shape is treated like a damaged file: never overwrite what we do not understand
if (!isObj(cfg) || (cfg.mcpServers != null && !isObj(cfg.mcpServers))) { say('RESULT=BADJSON'); process.exit(0); }
cfg.mcpServers = cfg.mcpServers || {};
const prev = cfg.mcpServers[name];
if (prev && JSON.stringify(prev.args || []).includes('npx')) say('REPLACED=npx');
// a different server the user registered under this name is replaced, so say what it was
else if (prev && !JSON.stringify(prev).includes('openai-gpt-image-mcp')) say('REPLACED=OTHER:' + mask([prev.command].concat(prev.args || []).join(' ')).slice(0, 120));
// the same package under another name would start a second copy and show every tool twice
for (const [k, v] of Object.entries(cfg.mcpServers)) if (k !== name && JSON.stringify(v || {}).includes('openai-gpt-image-mcp')) say('DUP=' + k);
cfg.mcpServers[name] = {
  type: 'stdio',
  command: process.env.MCP_NODE,
  args: [process.env.MCP_ENTRY],
  // NODE_OPTIONS '' keeps a broken global NODE_OPTIONS from stopping the server Claude starts
  env: { OPENAI_API_KEY: process.env.MCP_OPENAI_KEY, OPENAI_IMAGE_OUTPUT_DIR: process.env.MCP_IMAGE_DIR, HISTORY_DB_PATH: process.env.MCP_HISTORY_DB, NODE_OPTIONS: '' }
};
try {
  saveJson(file, cfg);
  const check = readJson(file).mcpServers[name];
  if (check.env.OPENAI_API_KEY !== process.env.MCP_OPENAI_KEY) throw new Error('verify failed');
} catch (e) {
  say('RESULT=' + (LOCK_CODES.includes(e.code) ? 'LOCKED' : 'ERROR')); say('DETAIL=' + mask(e.message)); process.exit(0);
}
// a deny rule in settings.json blocks the tool even though the install succeeds
try {
  const deny = readJson(process.env.CLAUDE_SETTINGS_FILE).permissions.deny;
  for (const r of Array.isArray(deny) ? deny : []) if (typeof r === 'string' && (r === 'mcp__' + name || r.startsWith('mcp__' + name + '__'))) say('DENY=' + r);
} catch {}
// same name in a higher-priority scope makes Claude ignore what we just wrote
for (const [p, v] of Object.entries(cfg.projects || {})) {
  if (v && v.mcpServers && v.mcpServers[name]) say('CONFLICT=LOCAL:' + p);
  try { if (readJson(path.join(p, '.mcp.json')).mcpServers[name]) say('CONFLICT=' + path.join(p, '.mcp.json')); } catch {}
}
say('RESULT=OK');
'@
switch (Get-Value 'RESULT') {
    'OK'      { }
    'BADJSON' { Fail "기존 $ClaudeJson 파일이 손상되었거나 형식이 달라 수정하지 않았습니다. Claude를 실행해 자동 복구되는지 확인한 뒤 다시 실행하세요." }
    'LOCKED'  { Fail "설정 파일을 수정하지 못했습니다. $LockedMessage" }
    default   { Fail "설정 파일 수정 중 오류가 났습니다. 내용: $(Get-Value 'DETAIL')" }
}
if ((Get-Value 'REPLACED') -eq 'npx') { Ok "기존 npx 방식 설정을 새 방식으로 교체했습니다" }
if ((Get-Value 'REPLACED').StartsWith('OTHER:')) { Warn "같은 이름('$ServerName')으로 등록돼 있던 다른 설정을 이 이미지 도구로 교체했습니다. 예전 설정: $((Get-Value 'REPLACED').Substring(6))  (백업: $backup)" }
Ok "'$ServerName' 등록 완료"
foreach ($dup in @($script:JsOut | Where-Object { $_ -like 'DUP=*' } | ForEach-Object { $_.Substring(4) })) {
    Warn "다른 이름('$dup')으로도 같은 이미지 도구가 등록되어 있어 도구가 두 번 보일 수 있습니다. 필요 없으면 지우세요: claude mcp remove $dup"
}
foreach ($rule in @($script:JsOut | Where-Object { $_ -like 'DENY=*' } | ForEach-Object { $_.Substring(5) })) {
    Warn "settings.json의 차단 규칙($rule) 때문에 이 이미지 도구를 쓸 수 없습니다. 쓰려면 $SettingsJson 의 permissions.deny 에서 지우세요."
}
foreach ($c in @($script:JsOut | Where-Object { $_ -like 'CONFLICT=*' } | ForEach-Object { $_.Substring(9) })) {
    if ($c.StartsWith('LOCAL:')) { $c = $c.Substring(6) + ' (로컬 범위)' }
    Warn "같은 이름의 다른 설정이 있어 그 폴더에서는 이 설치 대신 그 설정이 쓰일 수 있습니다: $c"
}
# company-managed Claude settings can hide user MCP servers or block this one; the install still finishes, so say so now
# a 32-bit PowerShell sees "Program Files (x86)" as ProgramFiles; the managed files live in the 64-bit folder
$PF64 = if ($env:ProgramW6432) { $env:ProgramW6432 } else { $env:ProgramFiles }
foreach ($md in @((Join-Path $PF64 'ClaudeCode'), (Join-Path $env:ProgramData 'ClaudeCode')) | Select-Object -Unique) {
    if (Test-Path -LiteralPath (Join-Path $md 'managed-mcp.json')) { Warn "회사가 관리하는 MCP 설정($md\managed-mcp.json)이 있어 Claude가 이 이미지 도구를 무시할 수 있습니다. 도구가 안 보이면 IT 담당자에게 문의하세요." }
    $ms = Join-Path $md 'managed-settings.json'
    if ((Test-Path -LiteralPath $ms) -and ([IO.File]::ReadAllText($ms) -match '"(denied|allowed)McpServers"')) { Warn "회사 관리 설정($ms)이 MCP 서버를 제한하고 있어 이 이미지 도구가 막힐 수 있습니다. 도구가 안 보이면 IT 담당자에게 문의하세요." }
}

# 8. 이미지 도구 권한 허용 (선택)
Step "권한 설정 (선택)"
$ans = Read-Host "    이미지 생성 도구를 매번 묻지 않고 허용할까요? 그냥 엔터 = 예 (Y/n)"
if ($ans -eq '' -or $ans -match '^[Yyㅛ]') {
    $env:CLAUDE_SETTINGS = $SettingsJson
    if ((Test-Path -LiteralPath $SettingsJson) -and -not (Copy-WithRetry $SettingsJson "$SettingsJson.backup-$(Get-Stamp)")) {
        Warn "settings.json을 백업하지 못해 권한 추가를 건너뜁니다 (이미지 생성에는 영향 없고, 사용할 때마다 허용 여부를 묻습니다)"
    } else {
        if (Test-Path -LiteralPath $SettingsJson) { Keep-NewestBackups (Split-Path -LiteralPath $SettingsJson) 'settings.json.backup-' 3 }
        Run-Js 'settings.js' @'
const path = require('path');
const file = process.env.CLAUDE_SETTINGS;
let s = {};
try {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  if (fs.existsSync(file)) { const raw = fs.readFileSync(file, 'utf8'); if (raw.trim()) s = readJson(file); }
} catch (e) { say('RESULT=' + (e instanceof SyntaxError ? 'BADJSON' : 'ERROR')); process.exit(0); }
if (!isObj(s) || (s.permissions != null && !isObj(s.permissions)) || (isObj(s.permissions) && s.permissions.allow != null && !Array.isArray(s.permissions.allow))) { say('RESULT=BADJSON'); process.exit(0); }
s.permissions = s.permissions || {};
s.permissions.allow = s.permissions.allow || [];
const rule = 'mcp__' + process.env.SERVER_NAME;
if (!s.permissions.allow.includes(rule)) s.permissions.allow.push(rule);
try { saveJson(file, s); say('RESULT=OK'); } catch (e) { say('RESULT=ERROR'); }
'@
        switch (Get-Value 'RESULT') {
            'OK'      { Ok "매번 묻지 않도록 허용 추가" }
            'BADJSON' { Warn "settings.json이 손상되었거나 형식이 달라 권한 추가만 건너뜁니다. 파일은 바꾸지 않았고, 이미지 생성에는 영향 없이 사용할 때마다 허용 여부를 묻습니다." }
            default   { Warn "권한 설정 실패 (이미지 생성에는 영향 없고, 사용할 때마다 허용 여부를 묻습니다)" }
        }
    }
} else {
    Ok "건너뜀"
}

# 9. 실제 동작 시험: MCP 서버 연결 → 도구 확인 → (선택) 이미지 1장 생성
Step "MCP 서버 연결 시험"
# a damaged history database stops every image request; keep it aside under another name and let the server start a new one
if (Test-Path -LiteralPath $HistoryDb) {
    $head = $null
    try { $fsh = [IO.File]::OpenRead($HistoryDb); $buf = New-Object byte[] 16; $n = $fsh.Read($buf, 0, 16); $fsh.Close(); $head = [Text.Encoding]::ASCII.GetString($buf, 0, $n) } catch { }
    if ($head -ne $null -and $head -ne "SQLite format 3$([char]0)") {
        $aside = "$HistoryDb.broken-$(Get-Stamp)"
        try {
            Move-Item -LiteralPath $HistoryDb -Destination $aside -Force
            foreach ($x in "$HistoryDb-wal", "$HistoryDb-shm") { if (Test-Path -LiteralPath $x) { Remove-Item -LiteralPath $x -Force } }
            Warn "이미지 기록 파일이 손상되어 따로 보관하고 새로 만듭니다: $aside (이미지 파일은 그대로입니다)"
        } catch { Warn "이미지 기록 파일이 손상됐지만 옮기지 못했습니다: $HistoryDb  Claude를 완전히 종료한 뒤 다시 실행하세요." }
    }
}
$ans = Read-Host "    시험용 이미지도 1장 만들까요? OpenAI 크레딧이 소량 차감됩니다. 그냥 엔터 = 예 (Y/n)"
$env:MCP_TEST_IMAGE    = if ($ans -eq '' -or $ans -match '^[Yyㅛ]') { '1' } else { '0' }
$env:MCP_PARENT_PID    = "$PID"
$env:MCP_PID_FILE      = $PidFile
$env:MCP_API_ERROR     = Join-Path $WorkDir 'api-error.json'
$env:MCP_PRELOAD       = Join-Path $WorkDir 'record-api-error.js'

# 도구가 돌려주는 오류 문장에는 오류 코드가 빠져 있어, 시험 때만 API 응답의 상태 코드와 오류 코드를 직접 기록한다
Set-Content -LiteralPath $env:MCP_PRELOAD -Encoding ASCII -Value @'
const fs = require('fs');
const out = process.env.MCP_API_ERROR;
const realFetch = globalThis.fetch;
globalThis.fetch = async (...args) => {
  const res = await realFetch(...args);
  if (!res.ok) {
    let e = {};
    try { const body = await res.clone().json(); e = (body && body.error) || {}; } catch {}
    const message = String(e.message || '').replace(/sk-[A-Za-z0-9_\-*]+/g, 'sk-***').slice(0, 300);
    try { fs.writeFileSync(out, JSON.stringify({ status: res.status, code: e.code || null, type: e.type || null, message })); } catch {}
  }
  return res;
};
'@

Run-Js 'self-test.js' @'
const { spawn, spawnSync } = require('child_process');
const path = require('path');
const started = Date.now();
const dir = process.env.MCP_IMAGE_DIR;
const child = spawn(process.execPath, ['--require', process.env.MCP_PRELOAD, process.env.MCP_ENTRY], {
  env: { ...process.env, OPENAI_API_KEY: process.env.MCP_OPENAI_KEY, OPENAI_IMAGE_OUTPUT_DIR: dir, HISTORY_DB_PATH: process.env.MCP_HISTORY_DB }, stdio: ['pipe', 'pipe', 'pipe']
});
fs.writeFileSync(process.env.MCP_PID_FILE, process.pid + '\n' + child.pid + '\n');
let buf = '', errTail = '', finished = false;
const finish = (result, detail) => {
  if (finished) return;
  finished = true;
  say('RESULT=' + result);
  if (detail) say('DETAIL=' + mask(detail));
  spawnSync(sys32('taskkill.exe'), ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
  process.exit(0);
};
const send = m => child.stdin.write(JSON.stringify(m) + '\n');
// classify by HTTP status and API error code, never by words anywhere in the message
const classify = text => {
  let api = null;
  try { api = JSON.parse(fs.readFileSync(process.env.MCP_API_ERROR, 'utf8')); } catch {}
  const m = /Failed to generate image: (\d{3}) /.exec(text);
  const status = api ? api.status : (m ? Number(m[1]) : 0);
  const code = api ? (api.code || api.type || '') : '';
  const message = api ? api.message : text;
  if (status === 401) return 'KEY';
  if (status === 429) return (code === 'insufficient_quota' || code === 'billing_hard_limit_reached') ? 'CREDIT' : 'RATE';
  if (status === 400 && code === 'billing_hard_limit_reached') return 'CREDIT';
  if ((status === 400 || status === 404) && (code === 'model_not_found' || /^The model .* does not exist/i.test(message))) return 'MODEL';
  if (status === 400 && (code === 'moderation_blocked' || code === 'content_policy_violation' || /safety system/i.test(message))) return 'SAFETY';
  if (status === 403 && code === 'unsupported_country_region_territory') return 'REGION';
  if (status === 403) return /must be verified/i.test(message) ? 'ORG' : 'PERM';
  if (status >= 500) return 'SERVER';
  if (status) return 'GENFAIL';
  if (/Failed to generate image: Connection error/i.test(text)) return 'NET';
  if (/Failed to generate image: Request timed out/i.test(text)) return 'TIMEOUT_API';
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
      send({ jsonrpc: '2.0', id: 2, method: 'tools/list' });
    } else if (m.id === 2) {
      const tools = (m.result && m.result.tools) || [];
      const gen = tools.find(t => t.name === 'generate_image');
      const props = (gen && gen.inputSchema && gen.inputSchema.properties) || {};
      if (!tools.find(t => t.name === 'list_history') || !['prompt', 'model', 'size', 'quality', 'output_path'].every(p => p in props)) {
        return finish('TOOLMISMATCH', tools.map(t => t.name).join(','));
      }
      send({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: 'list_history', arguments: {} } });
    } else if (m.id === 3) {
      if (m.error || (m.result && m.result.isError)) return finish('DBFAIL', JSON.stringify(m.error || m.result));
      if (process.env.MCP_TEST_IMAGE !== '1') return finish('CONNECTED');
      say('CONNECTED=1');
      send({ jsonrpc: '2.0', id: 4, method: 'tools/call', params: { name: 'generate_image', arguments: {
        prompt: 'a cute cat character, white background, simple webtoon style',
        model: 'gpt-image-2', size: '1024x1024', quality: 'low', output_path: 'install-test.png' } } });
    } else if (m.id === 4) {
      const text = JSON.stringify(m.error || m.result);
      if (m.error || m.result.isError) return finish(classify(text), text);
      const made = fs.existsSync(dir) && fs.readdirSync(dir).some(f =>
        /\.(png|jpe?g|webp)$/i.test(f) && fs.statSync(path.join(dir, f)).mtimeMs >= started && fs.statSync(path.join(dir, f)).size > 0);
      finish(made ? 'IMAGE_OK' : 'NOFILE', dir);
    }
  }
});
child.stderr.on('data', d => { errTail = (errTail + d).slice(-2000); });
child.on('exit', () => finish('NOSTART', errTail));
child.on('error', e => finish('NOSTART', e.message));
// stop together with the installer window
setInterval(() => { try { process.kill(Number(process.env.MCP_PARENT_PID), 0); } catch { finish('PARENT_GONE'); } }, 1000);
send({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'installer', version: '1' } } });
setTimeout(() => finish('TIMEOUT', errTail), 300000);
'@
$result = Get-Value 'RESULT'
$detail = Get-Value 'DETAIL'
$connected = (Get-Value 'CONNECTED') -eq '1' -or $result -eq 'CONNECTED'

# a running Claude can write its own copy of .claude.json over ours, so check the entry is still there
Run-Js 'recheck.js' @'
let ok = false;
try {
  const s = readJson(process.env.CLAUDE_JSON).mcpServers[process.env.SERVER_NAME];
  ok = !!s && s.command === process.env.MCP_NODE && !!s.env && s.env.OPENAI_API_KEY === process.env.MCP_OPENAI_KEY;
} catch {}
say('STILL=' + (ok ? '1' : '0'));
'@
$stillRegistered = (Get-Value 'STILL') -eq '1'
Remove-Item Env:MCP_OPENAI_KEY

if ($connected) { Ok "MCP 서버 연결과 도구 확인 성공" }
# checked before the result messages, so "no reinstall needed" is never shown when the registration is gone
if (-not $stillRegistered) { Fail "켜져 있던 Claude가 설정 파일을 덮어써서 방금 한 등록이 사라졌습니다. Claude를 트레이까지 완전히 종료한 뒤 install.bat을 다시 실행하세요." }

$NoReinstall = "설치는 끝났으니 재설치할 필요 없습니다."
switch ($result) {
    'IMAGE_OK'     { Ok "시험 이미지 생성 성공: $ImageDir" }
    'CONNECTED'    { Warn "이미지 시험은 건너뛰었습니다." }
    'ORG'          { Fail "이미지 생성이 거부됐습니다: 조직 인증이 필요합니다. platform.openai.com 의 Verify Organization 을 끝낸 뒤 Claude에서 다시 시도하세요. $NoReinstall" }
    'CREDIT'       { Fail "크레딧이 부족합니다. platform.openai.com 의 Billing 에서 충전한 뒤 Claude에서 다시 시도하세요. $NoReinstall" }
    'RATE'         { Fail "요청이 일시적으로 너무 많아 거절됐습니다(크레딧 문제 아님). 잠시 후 Claude에서 다시 시도하세요. $NoReinstall" }
    'MODEL'        { Fail "이 계정에서 gpt-image-2 모델을 쓸 수 없습니다. platform.openai.com 의 Verify Organization 이 끝났는지 확인하고, 끝났다면 OpenAI가 모델을 종료했는지 확인하세요. 내용: $detail" }
    'SAFETY'       { Fail "OpenAI 안전 정책이 시험 이미지 생성을 거부했습니다. 키와 설치 문제는 아닙니다. Claude에서 다른 이미지로 시도해 보세요. $NoReinstall" }
    'KEY'          { Fail "OpenAI가 키를 거부했습니다. 새 키를 발급받아 install.bat을 다시 실행하세요." }
    'PERM'         { Fail "이 키에 이미지 생성 권한이 없습니다. 키 권한을 All로 해서 새로 발급받아 install.bat을 다시 실행하세요." }
    'REGION'       { Fail "OpenAI가 지금 접속한 국가·지역을 지원하지 않는다고 거부했습니다. VPN을 쓰고 있다면 끄고 Claude에서 다시 시도하세요. $NoReinstall" }
    'SERVER'       { Fail "OpenAI 서버에 일시적인 오류가 났습니다. 잠시 후 Claude에서 다시 시도하세요. $NoReinstall" }
    'NET'          { Fail "OpenAI 접속에 실패했습니다. 회사 방화벽·프록시·VPN을 확인한 뒤 install.bat을 다시 실행하세요." }
    'TIMEOUT_API'  { Fail "OpenAI 응답 시간이 초과됐습니다. 잠시 후 Claude에서 다시 시도하세요. $NoReinstall" }
    'NOSTART'      { Fail "MCP 서버를 켜지 못했습니다. install.bat을 다시 실행하세요. 내용: $detail" }
    'DBFAIL'       { Fail "MCP 서버가 이미지 기록 파일을 열지 못했습니다. install.bat을 다시 실행하세요. 계속되면 $(Split-Path $HistoryDb) 폴더를 지운 뒤 다시 실행하세요. 내용: $detail" }
    'TOOLMISMATCH' { Fail "서버의 도구 구성이 예상과 다릅니다. 내용: $detail" }
    'NOFILE'       { Fail "API는 성공했지만 저장된 이미지를 찾지 못했습니다. 저장 폴더 권한을 확인하세요: $ImageDir" }
    'TIMEOUT'      { Fail "시간이 너무 오래 걸려 중단했습니다. 인터넷 상태를 확인한 뒤 다시 실행하세요. 내용: $detail" }
    'GENFAIL'      { Fail "설치와 연결은 끝났지만 OpenAI가 시험 이미지를 만들지 못했습니다. 잠시 후 Claude에서 이미지를 요청해 보고, 계속 실패하면 이 창의 내용을 보내 주세요. 내용: $detail" }
    default        { Fail "시험에 실패했습니다 ($result). 내용: $detail" }
}

Remove-WorkDir
Write-Host "`n설치 완료." -ForegroundColor Green
Write-Host "이제 Claude 앱을 실행하세요. (Claude를 켜 둔 채 설치했다면 완전히 종료 후 다시 실행)"
Write-Host "이미지 도구는 Claude 앱의 Code 탭에서만 쓸 수 있습니다. 일반 채팅에서는 보이지 않습니다."
Write-Host "만든 이미지는 $ImageDir 에 저장됩니다."

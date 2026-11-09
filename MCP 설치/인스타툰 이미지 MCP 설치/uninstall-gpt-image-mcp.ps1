# Claude Code + OpenAI GPT Image MCP 제거 스크립트 (Windows)
# uninstall.bat 을 더블클릭해서 실행하세요.

$ErrorActionPreference = 'Stop'
# tell uninstall.bat the script really started; if this never runs, policy or antivirus blocked the script
if ($env:GPTIMG_MARK) { Set-Content -LiteralPath $env:GPTIMG_MARK -Value 'started' -ErrorAction SilentlyContinue }
# company PCs with AppLocker/WDAC run scripts in Constrained Language Mode, where this script cannot work
if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') {
    Write-Host "    [X] 이 컴퓨터는 보안 정책 때문에 PowerShell이 제한 모드로 실행되어 제거할 수 없습니다. IT 담당자에게 문의하세요." -ForegroundColor Red
    exit 1
}
# a global NODE_OPTIONS (e.g. a --require left by another tool) would break the node call below
Remove-Item Env:NODE_OPTIONS -ErrorAction SilentlyContinue
$ServerName   = 'openai-gpt-image'
$InstallDir   = Join-Path $env:LOCALAPPDATA 'openai-gpt-image-mcp'
$WorkDir      = Join-Path $env:TEMP 'gpt-image-mcp-uninstall'
$ClaudeDir    = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { $env:USERPROFILE }
$ClaudeJson   = Join-Path $ClaudeDir '.claude.json'
$SettingsJson = if ($env:CLAUDE_CONFIG_DIR) { Join-Path $ClaudeDir 'settings.json' } else { Join-Path (Join-Path $ClaudeDir '.claude') 'settings.json' }

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
trap {
    Write-Host "`n    [X] 예상하지 못한 오류: $($_.Exception.Message)" -ForegroundColor Red
    Remove-WorkDir
    exit 1
}

$cmdArgs = [Environment]::GetCommandLineArgs()
if ([Console]::IsInputRedirected -or -not [Environment]::UserInteractive -or ($cmdArgs | Where-Object { $_ -match '^-noni' })) {
    Write-Host "    [X] 직접 입력할 수 없는 환경입니다. 파일 탐색기에서 uninstall.bat을 더블클릭해서 실행하세요." -ForegroundColor Red
    exit 1
}

# 설치 창과 동시에 실행되면 서로의 파일을 건드리므로 하나만 실행 (창이 닫히면 자동 해제)
$SetupMutex = New-Object Threading.Mutex($false, 'Local\openai-gpt-image-mcp-setup')
try { $gotMutex = $SetupMutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $gotMutex = $true }
if (-not $gotMutex) {
    Write-Host "    [X] 설치 또는 제거 창이 이미 열려 있습니다. 그 창이 끝난 뒤 다시 실행하세요." -ForegroundColor Red
    exit 1
}

# running elevated as another account would clean that account's profile, not the signed-in user's
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
    if ($desk -and $desk -ne $env:USERNAME) { Fail "다른 계정($env:USERNAME)의 관리자 권한으로 실행됐습니다. 이대로면 지금 로그인한 사용자($desk)의 설정을 지우지 못합니다. uninstall.bat을 '관리자 권한으로 실행' 없이 그냥 더블클릭하세요." }
}

# drop empty entries: a PATH starting with ';' makes cmd unable to find programs
$env:Path = (@([Environment]::GetEnvironmentVariable('Path','Machine') -split ';') + @([Environment]::GetEnvironmentVariable('Path','User') -split ';') | Where-Object { $_ }) -join ';'
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Fail "Node.js를 찾지 못해 설정을 수정할 수 없습니다. Node.js를 설치한 뒤 다시 실행하세요." }

$ans = Read-Host "OpenAI 이미지 MCP를 제거할까요? (y/N)"
if ($ans -notmatch '^[Yyㅛ]') { Write-Host "취소했습니다. 아무것도 바꾸지 않았습니다."; exit 0 }

Step "Claude 종료 확인"
while (Get-Process -Name claude -ErrorAction SilentlyContinue) {
    Warn "Claude가 실행 중입니다. 창을 닫고, 작업 표시줄 오른쪽 아래 트레이 아이콘에서도 종료해 주세요."
    $ans = Read-Host "    종료했으면 엔터 (그대로 진행하려면 s 입력 후 엔터)"
    if ($ans -match '^[sSㄴ]') { Warn "Claude가 켜진 채로 진행합니다."; break }
}
Ok "확인 완료"
[void][IO.Directory]::CreateDirectory($WorkDir)

$JsFile = Join-Path $WorkDir 'remove.js'
$Result = Join-Path $WorkDir 'result.txt'
$env:MCP_RESULT      = $Result
$env:CLAUDE_JSON     = $ClaudeJson
$env:CLAUDE_SETTINGS = $SettingsJson
$env:SERVER_NAME     = $ServerName
$env:MCP_DEST        = $InstallDir
$env:OTHER_CLAUDE_JSON = if ($env:CLAUDE_CONFIG_DIR) { Join-Path $env:USERPROFILE '.claude.json' } else { '' }
Set-Content -LiteralPath $JsFile -Encoding ASCII -Value @'
const fs = require('fs'), path = require('path');
const say = line => fs.appendFileSync(process.env.MCP_RESULT, line + '\n', 'utf8');
const sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const LOCK_CODES = ['EPERM', 'EBUSY', 'EACCES', 'ENOTEMPTY'];
const retry = f => { for (let i = 0; ; i++) { try { return f(); } catch (e) { if (i >= 4 || !LOCK_CODES.includes(e.code)) throw e; sleep(2000); } } };
// numbers are kept exactly as written (a plain parse would round big integers when the file is saved back)
const keepNumber = (k, v, c) => (typeof v === 'number' && c && typeof c.source === 'string' && String(v) !== c.source && typeof JSON.rawJSON === 'function') ? JSON.rawJSON(c.source) : v;
const readJson = file => JSON.parse((s => s.charCodeAt(0) === 0xFEFF ? s.slice(1) : s)(fs.readFileSync(file, 'utf8')) || '{}', keepNumber);
// a hard-linked file (settings sync tools) is written in place so the link survives; otherwise through a temp file
const write = (file, obj) => {
  const text = JSON.stringify(obj, null, 2);
  let links = 1; try { links = fs.statSync(file).nlink; } catch {}
  if (links > 1) { retry(() => fs.writeFileSync(file, text, 'utf8')); return; }
  const tmp = file + '.tmp-install'; fs.writeFileSync(tmp, text, 'utf8');
  try { retry(() => fs.renameSync(tmp, file)); } catch (e) { try { fs.unlinkSync(tmp); } catch {} throw e; }
};
// own recursive delete: fs.rmSync in Node 24.0.x crashes the process on paths with Korean or other non-ASCII characters
// anything that disappears while deleting (antivirus, a finishing process) counts as deleted
const gone = f => { try { f(); } catch (e) { if (e.code !== 'ENOENT') throw e; } };
const rmrf = p => {
  let st; try { st = fs.lstatSync(p); } catch (e) { if (e.code === 'ENOENT') return; throw e; }
  if (st.isDirectory() && !st.isSymbolicLink()) {
    let names = []; gone(() => { names = fs.readdirSync(p); });
    for (const n of names) rmrf(path.join(p, n));
    gone(() => fs.rmdirSync(p)); return;
  }
  try { fs.unlinkSync(p); } catch (e) {
    if (e.code === 'ENOENT') return;
    if (e.code === 'EPERM' && !st.isSymbolicLink()) { gone(() => fs.chmodSync(p, 0o666)); gone(() => fs.unlinkSync(p)); }
    else if (st.isSymbolicLink()) gone(() => fs.rmdirSync(p));
    else throw e;
  }
};
const name = process.env.SERVER_NAME;

const file = process.env.CLAUDE_JSON;
try {
  if (fs.existsSync(file)) {
    const cfg = readJson(file);
    const isObj = v => !!v && typeof v === 'object' && !Array.isArray(v);
    if (!isObj(cfg) || (cfg.mcpServers != null && !isObj(cfg.mcpServers))) throw new SyntaxError('unexpected shape');
    const entry = cfg.mcpServers && cfg.mcpServers[name];
    if (entry) {
      if (entry.env && entry.env.OPENAI_IMAGE_OUTPUT_DIR) say('IMAGES=' + entry.env.OPENAI_IMAGE_OUTPUT_DIR);
      delete cfg.mcpServers[name];
      write(file, cfg);
      say('CONFIG=REMOVED');
    } else say('CONFIG=NONE');
    for (const [p, v] of Object.entries(cfg.projects || {})) {
      if (v && v.mcpServers && v.mcpServers[name]) say('CONFLICT=LOCAL:' + p);
      try { if (readJson(path.join(p, '.mcp.json')).mcpServers[name]) say('CONFLICT=' + path.join(p, '.mcp.json')); } catch {}
    }
  } else say('CONFIG=NONE');
} catch (e) { say('CONFIG=' + (e instanceof SyntaxError ? 'BADJSON' : 'LOCKED')); }

const settings = process.env.CLAUDE_SETTINGS, rule = 'mcp__' + name;
try {
  if (fs.existsSync(settings)) {
    const s = readJson(settings);
    if (s.permissions && Array.isArray(s.permissions.allow) && s.permissions.allow.includes(rule)) {
      fs.copyFileSync(settings, settings + '.backup-uninstall');
      s.permissions.allow = s.permissions.allow.filter(r => r !== rule);
      write(settings, s);
      say('SETTINGS=REMOVED');
    } else say('SETTINGS=NONE');
  } else say('SETTINGS=NONE');
} catch (e) { say('SETTINGS=FAILED'); }

const dest = process.env.MCP_DEST;
// if the entry could not be removed from the config, deleting the folder would leave Claude pointing at a missing server
const cfgResult = fs.readFileSync(process.env.MCP_RESULT, 'utf8');
if (/CONFIG=(BADJSON|LOCKED)/.test(cfgResult)) say('DIR=KEPT');
else try {
  // the image history database lives next to the install folder (openai-gpt-image-mcp-data)
  const had = [dest, dest + '.new', dest + '.old', dest + '-data'].filter(d => fs.existsSync(d));
  for (const d of had) retry(() => rmrf(d));
  say('DIR=' + (had.length ? 'REMOVED' : 'NONE'));
} catch (e) { say('DIR=LOCKED'); }

// the other place Claude may keep its settings (before or after CLAUDE_CONFIG_DIR was set) can still hold the entry
const other = process.env.OTHER_CLAUDE_JSON;
try { if (other && other !== file && fs.existsSync(other) && readJson(other).mcpServers[name]) say('OTHER=' + other); } catch {}
'@
node $JsFile
# a running Claude can write its own copy of .claude.json back, so check the entry is really gone
$RecheckJs = Join-Path $WorkDir 'recheck.js'
Set-Content -LiteralPath $RecheckJs -Encoding ASCII -Value @'
const fs = require('fs'), f = process.env.CLAUDE_JSON;
let back = false;
try { const s = fs.readFileSync(f, 'utf8'); const c = JSON.parse(s.charCodeAt(0) === 0xFEFF ? s.slice(1) : s); back = !!(c && c.mcpServers && c.mcpServers[process.env.SERVER_NAME]); } catch {}
fs.appendFileSync(process.env.MCP_RESULT, 'BACK=' + (back ? '1' : '0') + '\n', 'utf8');
'@
node $RecheckJs
$out = if (Test-Path -LiteralPath $Result) { [IO.File]::ReadAllLines($Result, [Text.Encoding]::UTF8) } else { @() }
function Get-Value($prefix) {
    $line = $out | Where-Object { $_.StartsWith("$prefix=") } | Select-Object -Last 1
    if ($line) { return $line.Substring($prefix.Length + 1) }
    return ''
}
$Locked = "다른 프로그램이 사용 중입니다. Claude를 트레이까지 완전히 종료하고, OneDrive 동기화 일시 중지와 백신 검사 완료를 확인한 뒤 다시 실행하세요."

Step "제거 결과"
switch (Get-Value 'CONFIG') {
    'REMOVED' { Ok "Claude 설정에서 '$ServerName' 항목 삭제" }
    'NONE'    { Ok "Claude 설정에 '$ServerName' 항목이 없습니다" }
    'BADJSON' { Warn "$ClaudeJson 파일이 손상되어 수정하지 못했습니다." }
    default   { Warn "Claude 설정을 수정하지 못했습니다. $Locked" }
}
switch (Get-Value 'SETTINGS') {
    'REMOVED' { Ok "권한 허용 항목 삭제" }
    'NONE'    { Ok "권한 허용 항목이 없습니다" }
    default   { Warn "settings.json을 수정하지 못했습니다. 이미지 도구는 이미 제거되어 동작에는 영향이 없습니다." }
}
switch (Get-Value 'DIR') {
    'REMOVED' { Ok "설치 폴더 삭제: $InstallDir" }
    'NONE'    { Ok "설치 폴더가 없습니다" }
    'KEPT'    { Warn "Claude 설정에서 항목을 지우지 못해 설치 폴더도 남겨 두었습니다. 위 문제를 해결한 뒤 uninstall.bat을 다시 실행하세요." }
    default   { Warn "설치 폴더를 지우지 못했습니다: $InstallDir $Locked" }
}
if (Get-Value 'OTHER') { Warn "다른 위치의 Claude 설정($(Get-Value 'OTHER'))에도 이 이미지 도구가 남아 있습니다. CLAUDE_CONFIG_DIR 설정을 바꾸기 전에 쓰던 위치입니다. 필요 없으면 그 설정으로 Claude를 연 뒤 claude mcp remove $ServerName 을 실행하세요." }
if ((Get-Value 'CONFIG') -eq 'REMOVED' -and (Get-Value 'BACK') -eq '1') { Warn "켜져 있던 Claude가 설정 파일을 덮어써서 '$ServerName' 항목이 되살아났습니다. Claude를 트레이까지 완전히 종료한 뒤 uninstall.bat을 다시 실행하세요." }

# leftovers of an installer window that was closed midway (test process and temp files)
$InstallWork = Join-Path $env:TEMP 'gpt-image-mcp-install'
if (Test-Path -LiteralPath (Join-Path $InstallWork 'pids.txt')) {
    foreach ($oldPid in (Get-Content -LiteralPath (Join-Path $InstallWork 'pids.txt'))) {
        if ($oldPid -notmatch '^\d+$') { continue }
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$oldPid" -ErrorAction SilentlyContinue
        if ($proc -and $proc.CommandLine -like '*gpt-image-mcp-install*') { Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue }
    }
}
foreach ($leftover in $InstallWork, "$ClaudeJson.tmp-install", "$SettingsJson.tmp-install") {
    if (Test-Path -LiteralPath $leftover) { Remove-Item -LiteralPath $leftover -Recurse -Force -ErrorAction SilentlyContinue }
}
foreach ($c in @($out | Where-Object { $_ -like 'CONFLICT=*' } | ForEach-Object { $_.Substring(9) })) {
    if ($c.StartsWith('LOCAL:')) { $c = $c.Substring(6) + ' (로컬 범위)' }
    Warn "같은 이름의 다른 설정은 그대로 남아 있습니다: $c"
}

# 키가 든 백업 정리 (이 설치가 만든 백업 + Claude가 자동으로 만든 백업)
Step "키가 든 백업 정리"
$keyBackups = @()
foreach ($d in @($ClaudeDir, (Join-Path $ClaudeDir 'backups'), (Join-Path $env:USERPROFILE '.claude\backups'))) {
    if (-not (Test-Path -LiteralPath $d)) { continue }
    foreach ($f in (Get-ChildItem -LiteralPath $d -Force -File -Filter '.claude.json.backup*')) {
        $text = $null
        try { $text = [IO.File]::ReadAllText($f.FullName) } catch { }
        if ($text -and $text.Contains('"openai-gpt-image"') -and $text.Contains('OPENAI_API_KEY')) { $keyBackups += $f.FullName }
    }
}
$keyBackups = @($keyBackups | Select-Object -Unique)
if ($keyBackups.Count -eq 0) {
    Ok "키가 든 백업이 없습니다"
} else {
    $keyBackups | ForEach-Object { Write-Host "    $_" }
    $ans = Read-Host "    위 백업 $($keyBackups.Count)개에 API 키가 들어 있습니다. 삭제할까요? 삭제하면 되돌릴 수 없습니다. (y/N)"
    if ($ans -match '^[Yyㅛ]') {
        foreach ($f in $keyBackups) { Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue }
        $left = @($keyBackups | Where-Object { Test-Path -LiteralPath $_ }).Count
        if ($left -eq 0) { Ok "백업 삭제 완료" } else { Warn "$left 개를 지우지 못했습니다. $Locked" }
    } else {
        Warn "백업을 남겼습니다. 이 파일들에는 API 키가 그대로 들어 있습니다."
    }
}

Remove-WorkDir
Write-Host "`n제거 완료." -ForegroundColor Green
Write-Host "Node.js와 지금까지 만든 이미지는 지우지 않았습니다."
$images = Get-Value 'IMAGES'
if ($images) { Write-Host "이미지 폴더: $images" }
Write-Host "API 키를 더 쓰지 않는다면 platform.openai.com 의 API keys 에서 삭제하세요."

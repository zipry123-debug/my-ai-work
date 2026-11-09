@echo off
if not exist "%~dp0uninstall-gpt-image-mcp.ps1" (
    echo.
    echo [ERROR] uninstall-gpt-image-mcp.ps1 not found.
    echo Extract the ZIP file first, then run uninstall.bat inside the extracted folder.
    echo.
    pause
    exit /b 1
)
rem a 32-bit program that starts this file gets the 32-bit PowerShell; Sysnative reaches the 64-bit one
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
rem the script writes this file as its first step; if it is missing afterwards, the script was blocked before it could start
set "GPTIMG_MARK=%TEMP%\gpt-image-mcp-started-%RANDOM%%RANDOM%.txt"
if exist "%GPTIMG_MARK%" del "%GPTIMG_MARK%"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall-gpt-image-mcp.ps1"
set "RC=%ERRORLEVEL%"
if not exist "%GPTIMG_MARK%" (
    echo.
    echo [ERROR] The script was blocked before it could start ^(policy or antivirus^).
    "%PS%" -NoProfile -Command "Write-Host ([string]::new([char[]]@(49828,53356,47549,53944,32,49892,54665,51060,32,47561,54784,32,49884,51089,46104,51648,32,47803,54664,49845,45768,45796,46,32,54924,49324,32,48372,50504,32,51221,52293,51060,45208,32,48177,49888,32,46412,47928,51068,32,49688,32,51080,49845,45768,45796,46,32,82,69,65,68,77,69,51032,32,39,49892,54665,51060,32,47561,55184,32,46412,39,47484,32,54869,51064,54616,44256,44,32,54924,49324,32,80,67,46972,47732,32,73,84,32,45812,45817,51088,50640,44172,32,47928,51032,54616,49464,50836,46))) -ForegroundColor Red"
)
if exist "%GPTIMG_MARK%" del "%GPTIMG_MARK%"
echo.
pause
exit /b %RC%
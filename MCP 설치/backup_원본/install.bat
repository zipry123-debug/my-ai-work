@echo off
if not exist "%~dp0setup-gpt-image-mcp.ps1" (
    echo.
    echo [ERROR] setup-gpt-image-mcp.ps1 not found.
    echo Extract the ZIP file first, then run install.bat inside the extracted folder.
    echo.
    pause
    exit /b 1
)
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-gpt-image-mcp.ps1"
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%

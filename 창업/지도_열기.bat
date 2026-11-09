@echo off
rem Opens the map: starts a local web server in the folder that has dist\index.html and opens the browser.
rem (ASCII only on purpose: Korean text in .bat files breaks in some Windows consoles.)
cd /d "%~dp0"
set "MAPDIR="
for /d %%D in ("%~dp0*") do if exist "%%~fD\dist\index.html" set "MAPDIR=%%~fD\dist"
if not defined MAPDIR (
  echo [error] map folder with dist\index.html was not found.
  pause
  exit /b 1
)
where python >nul 2>nul || (
  echo [error] Python is required. Install it from https://www.python.org and run again.
  pause
  exit /b 1
)
cd /d "%MAPDIR%"
python -c "print('\uc9c0\ub3c4\ub97c \uc5ec\ub294 \uc911\uc785\ub2c8\ub2e4. \ube0c\ub77c\uc6b0\uc800\uac00 \uc5f4\ub9ac\uc9c0 \uc54a\uc73c\uba74 http://localhost:8000 \uc744 \uc9c1\uc811 \uc5ec\uc138\uc694. \uc774 \ucc3d\uc744 \ub2eb\uc73c\uba74 \uc9c0\ub3c4\uac00 \uaebc\uc9d1\ub2c8\ub2e4.')"
start "" cmd /c "timeout /t 2 >nul & start http://localhost:8000/"
python -m http.server 8000
pause

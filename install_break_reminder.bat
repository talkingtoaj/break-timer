@echo off
REM Download latest Break reminder.exe from GitHub Releases and optionally add to startup.
REM Requires: internet connection. If no release exists, build locally with build_exe.bat.

set REPO=https://github.com/talkingtoaj/break-timer
set INSTALL_DIR=%LOCALAPPDATA%\Break reminder
set EXE=%INSTALL_DIR%\Break reminder.exe
set DOWNLOAD_URL=%REPO%/releases/latest/download/Break%%20reminder.exe

echo Break reminder - Installer
echo.
echo This will download the latest release from GitHub and install to:
echo   %INSTALL_DIR%
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Downloading Break reminder.exe...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { " ^
  "  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
  "  Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%EXE%' -UseBasicParsing; " ^
  "  Write-Host 'Download complete.' " ^
  "} catch { " ^
  "  Write-Host 'Download failed. Go to %REPO%/releases/latest to download Break reminder.exe manually.'; " ^
  "  exit 1 " ^
  "}"

if errorlevel 1 (
  echo.
  echo Please download the exe from: %REPO%/releases/latest
  pause
  exit /b 1
)

echo.
echo Adding to Windows startup...
"%EXE%" --install

echo.
echo Done. Break reminder is installed at:
echo   %EXE%
echo It will start automatically when you log in.
echo.
start "" "%INSTALL_DIR%"
pause

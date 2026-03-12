@echo off
REM Rebuild Break.reminder.exe and publish a new release to GitHub.
REM Run on Windows from the project folder. Requires: git, Python, GitHub CLI (gh).
REM
REM Usage:
REM   release.bat           - prompt for version and release
REM   release.bat 1.0.3     - release as v1.0.3

setlocal EnableDelayedExpansion
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM --- Version ---
set VERSION=%1
if "%VERSION%"=="" (
  set /p VERSION="Enter version number (e.g. 1.0.3): "
  if "!VERSION!"=="" (
    echo No version entered. Exiting.
    exit /b 1
  )
)
set TAG=v%VERSION%

REM --- Build ---
echo.
echo [1/4] Building exe...
call build_exe.bat
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

REM --- Check artifacts ---
if not exist "dist\Break.reminder.exe" (
  echo Build failed: dist\Break.reminder.exe not found.
  exit /b 1
)
if not exist "install_break_reminder.bat" (
  echo install_break_reminder.bat not found.
  exit /b 1
)

REM --- GitHub CLI ---
where gh >nul 2>nul
if errorlevel 1 (
  echo.
  echo GitHub CLI (gh) is required to create the release.
  echo Install: winget install GitHub.cli   or see https://cli.github.com/
  echo.
  echo You can still push code and create the release manually:
  echo   git tag %TAG%
  echo   git push origin %TAG%
  echo   Then create a release at https://github.com/talkingtoaj/break-timer/releases/new and upload dist\Break.reminder.exe and install_break_reminder.bat
  exit /b 1
)

REM --- Commit and tag (no commit if nothing changed; tag only) ---
echo.
echo [2/4] Tagging %TAG%...
git tag -a %TAG% -m "Release %TAG%"
if errorlevel 1 (
  echo Tag failed. Does %TAG% already exist? Delete with: git tag -d %TAG%
  exit /b 1
)

echo.
echo [3/4] Pushing to GitHub...
git push origin main
git push origin %TAG%

echo.
echo [4/4] Creating GitHub release %TAG%...
gh release create %TAG% ^
  "dist\Break.reminder.exe" ^
  "install_break_reminder.bat" ^
  --title "Release %TAG%" ^
  --notes "Break reminder %VERSION%. Download install_break_reminder.bat and run it to install."

if errorlevel 1 (
  echo Release creation failed. Tag was pushed; create the release manually and upload the assets.
  exit /b 1
)

echo.
echo Done. Release: https://github.com/talkingtoaj/break-timer/releases/tag/%TAG%
exit /b 0

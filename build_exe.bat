@echo off
REM Build Break.reminder.exe and copy to Downloads.
REM Run this on Windows (Command Prompt or PowerShell) from the project folder.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Installing PyInstaller if needed...
pip install pyinstaller --quiet

echo Building exe...
python -m PyInstaller --noconfirm break_timer.spec

if not exist "dist\Break.reminder.exe" (
    echo Build failed. dist\Break.reminder.exe not found.
    exit /b 1
)

set DOWNLOADS=%USERPROFILE%\Downloads
set INSTALL_DIR=%LOCALAPPDATA%\Break reminder
echo Copying to %DOWNLOADS%...
copy /Y "dist\Break.reminder.exe" "%DOWNLOADS%\Break.reminder.exe"

if exist "%INSTALL_DIR%" (
    echo Updating installed app at %INSTALL_DIR%...
    copy /Y "dist\Break.reminder.exe" "%INSTALL_DIR%\Break.reminder.exe"
    echo Installed version updated.
)

echo Done. Exe is at: %DOWNLOADS%\Break.reminder.exe
explorer /select,"%DOWNLOADS%\Break.reminder.exe"

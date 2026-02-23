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
echo Copying to %DOWNLOADS%...
copy /Y "dist\Break.reminder.exe" "%DOWNLOADS%\Break.reminder.exe"

echo Done. Exe is at: %DOWNLOADS%\Break.reminder.exe
explorer /select,"%DOWNLOADS%\Break.reminder.exe"

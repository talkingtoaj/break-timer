@echo off
echo Installing Enhanced Break Timer...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Add to startup
echo Adding to startup...
python break_timer.py --install

echo.
echo Installation complete!
echo The Enhanced Break Timer will start automatically when you log in.
echo.
echo New Features:
echo - 2-minute break countdown with OK button activation
echo - Joke incentives when user ignores breaks frequently
echo - Smart ignore detection and tracking
echo.
pause
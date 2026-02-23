# Enhanced Break Timer

A smart Windows break reminder application that encourages your wife to take actual breaks from work.

## Features

- Runs on Windows 11+
- Starts automatically with Windows
- Default 30-minute timer (configurable: 20, 30, 45, 60 minutes)
- **2-minute break countdown** with visual timer
- **Smart ignore detection** - tracks behavior over last 5 breaks
- **Joke incentives** - if user ignores >40% of breaks, offers jokes as rewards
- **Conditional OK button** - only appears after 2-minute countdown
- **Minimize functionality** - user can minimize, but countdown continues
- **Smart reminder system** - "Trying to ignore me? Rejection hurts..." after 2 minutes if minimized
- Settings and break history saved to config file
- Clean, simple interface

## How It Works

1. **Regular Breaks**: Timer counts down from your chosen interval (default 30 min)
2. **Break Time**: When break time arrives, a popup shows with 2-minute countdown
3. **Choices**: 
   - Keep in foreground for full 2 minutes → OK button activates
   - Minimize → break recorded as "ignored"
4. **Smart Incentives**: After 5+ breaks with >40% ignore rate, shows joke offer
5. **Reward System**: If you stay for full 2 minutes with joke incentive, get a random joke!

## Installation

### Option 1: Automated Installation (Recommended)
1. Double-click `install.bat`
2. Follow the prompts
3. The timer will start automatically with Windows

### Option 2: Manual Installation
1. Install Python 3.7+ from https://python.org
2. Install dependencies: `pip install -r requirements.txt`
3. Run once to add to startup: `python break_timer.py --install`

## Building the Windows exe

To create a standalone **Break reminder.exe** and copy it to your Downloads folder:

1. On **Windows**, open the project folder in Command Prompt or PowerShell.
2. Run: **`build_exe.bat`**
3. The script installs PyInstaller (if needed), builds the exe, and copies **Break reminder.exe** to `%USERPROFILE%\Downloads`. A File Explorer window will open to that file.

Requirements: Python 3.7+ and pip on Windows. The exe is single-file and does not show a console window. Config and log files are created next to the exe when you run it from the folder you keep it in.

## Running on Windows

- **Using the exe**: Double-click **Break reminder.exe** (e.g. from your Downloads folder). The window appears in the **taskbar**; use the title bar **Minimize** or the in-app **Minimize to tray** button to hide it. Use the system tray icon (if available) or the taskbar button to restore.
- **Start with Windows**: Open Command Prompt or PowerShell, go to the folder where the exe lives, and run:  
  `"Break reminder.exe" --install`  
  Then the app will start automatically when you log in. To remove from startup: Task Manager → Startup tab → disable "BreakTimer".
- **Interval**: Use the 20 / 30 / 45 / 60 buttons to set the focus length. When the timer reaches 0, a break reminder appears; after the 2-minute break countdown you can resume.

## Usage

- **Linux / WSL**: Run with `./run_break_timer.sh` (uses system Python to avoid a known xcb/tkinter crash with some Python builds). Or use system Python: `/usr/bin/python3 break_timer.py`.
- **Windows**: Run `python break_timer.py` or use the venv.

- The timer starts automatically when you log in (Windows) or when you run the app
- To change the break interval, select from the dropdown (20, 30, 45, 60 minutes)
- Click "Restart Timer" to reset the countdown
- When the reminder appears, click "OK" to acknowledge and restart the timer
- The setting is automatically saved

## Files

- `break_timer.py` - Main application
- `break_timer.spec` - PyInstaller spec for building the Windows exe
- `build_exe.bat` - Builds exe and copies to Downloads (run on Windows)
- `run_break_timer.sh` - Launcher for Linux/WSL (uses system Python to avoid xcb crash)
- `install.bat` - Automated installation script (Windows)
- `requirements.txt` - Python dependencies
- `break_timer_config.json` - Settings file (created automatically)

## Troubleshooting

- **Linux/WSL: app crashes with "xcb Unknown sequence number" or "XInitThreads"**  
  Use system Python or the launcher: `./run_break_timer.sh` (see Usage). Avoid running with uv-managed Python if you see this crash.

- If the app doesn't start with Windows, run `python break_timer.py --install` again
- Make sure Python is installed and in your system PATH
- Check that no antivirus software is blocking the application

## Removing the App

1. Open Task Manager > Startup tab
2. Find "BreakTimer" and disable it
3. Delete the break-timer folder
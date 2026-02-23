# Enhanced Break Timer

A smart Windows break reminder application that encourages your wife to take actual breaks from work.

**Install on Windows:** From the [Releases](https://github.com/talkingtoaj/break-timer/releases/latest) page, download **install_break_reminder.ps1** (or **install_break_reminder.bat**), then run it. The script downloads the latest app and adds it to startup. *(You can also get the scripts from the repo: [.ps1](https://github.com/talkingtoaj/break-timer/blob/main/install_break_reminder.ps1) · [.bat](https://github.com/talkingtoaj/break-timer/blob/main/install_break_reminder.bat).)*

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

### Windows: use the installer script (recommended)

1. **Get the installer**  
   - Go to [**Releases**](https://github.com/talkingtoaj/break-timer/releases/latest) and download **install_break_reminder.ps1** (PowerShell) or **install_break_reminder.bat**, or  
   - Clone this repo and run either script from the project folder.

2. **Run it**  
   - **.ps1:** In PowerShell, run `powershell -ExecutionPolicy Bypass -File install_break_reminder.ps1` (or right‑click → Run with PowerShell).  
   - **.bat:** Double‑click the file.  
   The script downloads the latest **Break reminder.exe** from [Releases](https://github.com/talkingtoaj/break-timer/releases/latest), installs it to `%LOCALAPPDATA%\Break reminder`, and adds it to Windows startup. You’ll see the install folder when it’s done.

3. **Use the app**  
   The app starts with Windows. You can also run **Break reminder.exe** from the install folder. It appears in the taskbar; use the title bar **Minimize** or the in-app **Minimize to tray** button to hide it.

No Python or other dependencies needed. Requires an internet connection for the first install.

**Manual install (exe only):** If you prefer not to use the script, download **Break reminder.exe** from [Releases](https://github.com/talkingtoaj/break-timer/releases/latest), put it in a folder, and run `"Break reminder.exe" --install` from that folder to start with Windows.

### Option 1: Automated Installation (Python)
1. Double-click `install.bat`
2. Follow the prompts
3. The timer will start automatically with Windows

### Option 2: Manual Installation (Python)
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

After installing with **install_break_reminder.bat**, the app starts with Windows. You can also run **Break reminder.exe** from `%LOCALAPPDATA%\Break reminder`. Use the 20 / 30 / 45 / 60 buttons to set the focus length; when the timer hits 0, a break reminder appears. To remove from startup: Task Manager → Startup → disable "BreakTimer".

## Usage

- **Linux / WSL**: Run with `./run_break_timer.sh` (uses system Python to avoid a known xcb/tkinter crash with some Python builds). Or use system Python: `/usr/bin/python3 break_timer.py`.
- **Windows**: Run `python break_timer.py` or use the venv.

- The timer starts automatically when you log in (Windows) or when you run the app
- To change the break interval, select from the dropdown (20, 30, 45, 60 minutes)
- Click "Restart Timer" to reset the countdown
- When the reminder appears, click "OK" to acknowledge and restart the timer
- The setting is automatically saved

## Files

- `install_break_reminder.ps1` - **Windows installer** (PowerShell); on [Releases](https://github.com/talkingtoaj/break-timer/releases/latest)
- `install_break_reminder.bat` - **Windows installer** (batch); on [Releases](https://github.com/talkingtoaj/break-timer/releases/latest)
- `break_timer.py` - Main application
- `break_timer.spec` - PyInstaller spec for building the Windows exe
- `build_exe.bat` - Builds exe and copies to Downloads (for developers, run on Windows)
- `run_break_timer.sh` - Launcher for Linux/WSL (uses system Python to avoid xcb crash)
- `install.bat` - Python-based install (installs deps and adds to startup)
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
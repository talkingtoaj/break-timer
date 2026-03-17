import tkinter as tk
from tkinter import messagebox
import json
import os
import time
import sys
import random
import threading

# Debug logging to file (next to script or next to exe when frozen)
if getattr(sys, "frozen", False):
    _app_base = os.path.dirname(sys.executable)
    _data_base = getattr(sys, "_MEIPASS", _app_base)
else:
    _app_base = os.path.dirname(os.path.abspath(__file__))
    _data_base = _app_base
DEBUG_LOG = os.path.join(_app_base, "break_timer_debug.log")
CHIME_MP3 = os.path.join(_data_base, "chime.mp3")

def _log(msg):
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
            f.flush()
    except Exception:
        pass


def _stop_chime():
    """Stop chime immediately (e.g. when app brought to foreground)."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.winmm.mciSendStringW('stop chime_sound', None, 0, 0)
            ctypes.windll.winmm.mciSendStringW('close chime_sound', None, 0, 0)
        except Exception:
            pass


def _play_chime_once():
    """Play the gentle chime sound once (MP3). Uses Windows MCI (zero extra dependencies)."""
    if not os.path.exists(CHIME_MP3):
        _log("chime: file not found " + CHIME_MP3)
        return
    if sys.platform == "win32":
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            winmm.mciSendStringW('close chime_sound', None, 0, 0)
            path = CHIME_MP3.replace('/', '\\')
            ret = winmm.mciSendStringW(f'open "{path}" type mpegvideo alias chime_sound', None, 0, 0)
            if ret != 0:
                _log(f"chime: MCI open error {ret}")
                return
            winmm.mciSendStringW('play chime_sound', None, 0, 0)
        except Exception as e:
            _log(f"chime: MCI error {e}")
    else:
        try:
            import subprocess
            subprocess.Popen(
                ["mpg123", "-q", CHIME_MP3],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            _log(f"chime: mpg123 error {e}")

# Windows-specific imports
try:
    import winreg
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Time flies like an arrow, fruit flies like a banana!",
    "I don't trust stairs because they're always up to something.",
    "Why don't skeletons fight each other? They don't have the guts.",
    "My wife says I never buy her flowers, but to be honest, I never even knew she sold flowers.",
    "I told my husband he should embrace his mistakes, he just gave me a big hug.",
    "Albert Einstein was a genius, but people forget that his brother Frank was a monster.",
    "I have a stepladder, because my real ladder left when I was young.",
    "I used to hate facial hair, but then it grew on me."
]

# Minimalist Zen Pastel Theme
THEME = {
    "bg": "#FDFBF7",          # Warm Linen
    "fg": "#6A7062",          # Soft Sage Grey
    "accent": "#9FB4A6",      # Pastel Sage
    "accent_hover": "#8A9F91",# Deeper Sage
    "secondary": "#EBECE7",   # Soft background for buttons
    "font_main": ("Helvetica", 11),
    "font_title": ("Helvetica", 18),
    "font_timer": ("Helvetica", 48, "bold"),
    "font_small": ("Helvetica", 10, "italic"),
    "titlebar": "#EBE8E3",
}

class Win32TrayIcon:
    """System tray icon using pure ctypes — no pystray/Pillow needed."""

    WM_USER = 0x0400
    WM_TRAYICON = WM_USER + 20
    WM_COMMAND = 0x0111
    WM_LBUTTONDBLCLK = 0x0203
    WM_RBUTTONUP = 0x0205
    NIM_ADD = 0x00
    NIM_DELETE = 0x02
    NIF_ICON = 0x02
    NIF_MESSAGE = 0x01
    NIF_TIP = 0x04
    IDM_SHOW = 1
    IDM_EXIT = 2

    def __init__(self, tooltip, on_show, on_exit):
        import ctypes
        from ctypes import wintypes

        self._on_show = on_show
        self._on_exit = on_exit
        self._tooltip = tooltip
        self._hwnd = None
        self._thread = None

        # Define NOTIFYICONDATAW
        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
            ]
        self._NID = NOTIFYICONDATAW

    def run_detached(self):
        """Start the tray icon in a background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        kernel32 = ctypes.windll.kernel32

        # Set correct arg/return types for 64-bit Windows
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.DefWindowProcW.restype = ctypes.c_long

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long, wintypes.HWND, wintypes.UINT,
            wintypes.WPARAM, wintypes.LPARAM,
        )

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == self.WM_TRAYICON:
                if lparam == self.WM_LBUTTONDBLCLK:
                    self._on_show()
                elif lparam == self.WM_RBUTTONUP:
                    menu = user32.CreatePopupMenu()
                    user32.InsertMenuW(menu, 0, 0x0000, self.IDM_SHOW, "Show")
                    user32.InsertMenuW(menu, 1, 0x0000, self.IDM_EXIT, "Exit")
                    pt = wintypes.POINT()
                    user32.GetCursorPos(ctypes.byref(pt))
                    user32.SetForegroundWindow(hwnd)
                    user32.TrackPopupMenu(menu, 0, pt.x, pt.y, 0, hwnd, None)
                    user32.DestroyMenu(menu)
                return 0
            if msg == self.WM_COMMAND:
                cmd = wparam & 0xFFFF
                if cmd == self.IDM_SHOW:
                    self._on_show()
                elif cmd == self.IDM_EXIT:
                    self._on_exit()
                return 0
            if msg == 0x0002:  # WM_DESTROY
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc_ref = WNDPROC(wnd_proc)  # prevent GC

        # Define WNDCLASSW (not in ctypes.wintypes)
        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HANDLE),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        hinstance = kernel32.GetModuleHandleW(None)
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wnd_proc_ref
        wc.hInstance = hinstance
        wc.lpszClassName = "BreakReminderTray"
        user32.RegisterClassW(ctypes.byref(wc))

        # Create hidden message-only window
        self._hwnd = user32.CreateWindowExW(
            0, "BreakReminderTray", "BreakReminderTray",
            0, 0, 0, 0, 0, None, None, hinstance, None,
        )

        # Load default app icon
        hicon = user32.LoadIconW(None, ctypes.cast(32512, wintypes.LPCWSTR))  # IDI_APPLICATION

        # Add tray icon
        nid = self._NID()
        nid.cbSize = ctypes.sizeof(nid)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = self.NIF_ICON | self.NIF_MESSAGE | self.NIF_TIP
        nid.uCallbackMessage = self.WM_TRAYICON
        nid.hIcon = hicon
        nid.szTip = self._tooltip[:127]
        shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(nid))
        self._nid = nid
        _log("Win32TrayIcon: icon added")

        # Message loop
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        _log("Win32TrayIcon: message loop exited")

    def stop(self):
        """Remove tray icon and stop message loop."""
        if self._hwnd is None:
            return
        try:
            import ctypes
            shell32 = ctypes.windll.shell32
            shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(self._nid))
            ctypes.windll.user32.PostMessageW(self._hwnd, 0x0010, 0, 0)  # WM_CLOSE
        except Exception:
            pass

def make_title_bar(parent, window, title, on_close, on_minimize=None):
    """Custom title bar with title, minimize, and close. Draggable."""
    bar = tk.Frame(parent, bg=THEME["titlebar"], height=36)
    bar.pack(side=tk.TOP, fill=tk.X)
    bar.pack_propagate(False)
    tk.Label(bar, text=title, bg=THEME["titlebar"], fg=THEME["fg"],
             font=THEME["font_main"]).pack(side=tk.LEFT, padx=12, pady=8)
    if on_minimize is not None:
        min_btn = tk.Label(bar, text=" − ", bg=THEME["titlebar"], fg=THEME["fg"],
                          font=("Helvetica", 16), cursor="hand2")
        min_btn.pack(side=tk.RIGHT, padx=(0, 2), pady=4)
        def do_minimize(e):
            on_minimize()
        min_btn.bind("<Button-1>", do_minimize)
        min_btn.bind("<Enter>", lambda e: min_btn.config(bg=THEME["accent"], fg="white"))
        min_btn.bind("<Leave>", lambda e: min_btn.config(bg=THEME["titlebar"], fg=THEME["fg"]))
    close_btn = tk.Label(bar, text=" × ", bg=THEME["titlebar"], fg=THEME["fg"],
                         font=("Helvetica", 16), cursor="hand2")
    close_btn.pack(side=tk.RIGHT, padx=4, pady=4)
    close_btn.bind("<Button-1>", lambda e: on_close())
    close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#C4A494", fg="white"))
    close_btn.bind("<Leave>", lambda e: close_btn.config(bg=THEME["titlebar"], fg=THEME["fg"]))

    def start_drag(e):
        window._drag_x = e.x_root
        window._drag_y = e.y_root
        window._win_x = window.winfo_x()
        window._win_y = window.winfo_y()

    def do_drag(e):
        if hasattr(window, "_drag_x"):
            dx = e.x_root - window._drag_x
            dy = e.y_root - window._drag_y
            window.geometry(f"+{window._win_x + dx}+{window._win_y + dy}")
            window._win_x += dx
            window._win_y += dy
            window._drag_x = e.x_root
            window._drag_y = e.y_root

    bar.bind("<Button-1>", start_drag)
    bar.bind("<B1-Motion>", do_drag)
    return bar

class FlatButton(tk.Button):
    def __init__(self, master, **kwargs):
        kwargs["relief"] = "flat"
        kwargs["bg"] = THEME["secondary"]
        kwargs["fg"] = THEME["fg"]
        kwargs["font"] = THEME["font_main"]
        kwargs["activebackground"] = THEME["accent"]
        kwargs["activeforeground"] = "white"
        kwargs["cursor"] = "hand2"
        kwargs["borderwidth"] = 0
        kwargs["padx"] = 16
        kwargs["pady"] = 8
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if self['state'] != 'disabled':
            self['bg'] = THEME["accent"]
            self['fg'] = "white"

    def on_leave(self, e):
        if self['state'] != 'disabled':
            self['bg'] = THEME["secondary"]
            self['fg'] = THEME["fg"]

class BreakTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Break reminder")
        self.root.geometry("400x380")
        self.root.resizable(False, False)
        self.root.configure(bg=THEME["bg"])
        self.config_file = os.path.join(_app_base, "break_timer_config.json")
        self.config = self.load_config()
        
        self.time_left = self.get_work_duration_seconds()
        self.timer_job = None
        self.reminder_window = None
        self.break_countdown_job = None
        self.tray_icon = None
        self._app_in_foreground = True
        self._last_chime_time = 0
        self._last_break_tick_at = None
        self._is_quitting = False
        _log("init: starting setup_ui")
        self.setup_ui()
        _log("init: setup_ui done")
        self._center_window()
        _log("init: center done, starting timer")
        self.start_timer()
        self.root.protocol("WM_DELETE_WINDOW", self._request_close)
        self.root.bind("<Alt-F4>", lambda _event: self._request_close())
        # Stop any currently-playing chime immediately when app regains focus.
        # Bind multiple events because overrideredirect windows may not get FocusIn.
        self.root.bind("<FocusIn>", self._on_focus_in)
        self.root.bind("<Button-1>", self._on_focus_in)
        # After first map: strip decorations and start tray (avoids hang on X11/WSL)
        self.root.after(100, self._after_first_map)
        _log("init: after(100) scheduled, __init__ done")
        
    def load_config(self):
        default_config = {
            "default_minutes": 30,
            "default_seconds": None,
            "break_history": []
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    cfg = json.load(f)
                    if "default_seconds" not in cfg:
                        cfg["default_seconds"] = None
                    if cfg.get("default_seconds") == 20:
                        cfg["default_seconds"] = 5  # migrated from old 20s option
                    return cfg
            except:
                return default_config
        return default_config
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
            
    def setup_ui(self):
        _log("setup_ui: body frame")
        self.body = tk.Frame(self.root, bg=THEME["bg"])
        self.body.pack(fill=tk.BOTH, expand=True)
        self.body.config(width=400, height=380)
        self.show_focus_view()
        _log("setup_ui: done")

    def _clear_body(self):
        for child in self.body.winfo_children():
            child.destroy()

    def show_focus_view(self):
        self.root.title("Break reminder")
        self._clear_body()
        main_frame = tk.Frame(self.body, bg=THEME["bg"])
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(main_frame, text="Focus Session", font=THEME["font_title"],
                 bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(0, 10))

        self.timer_label = tk.Label(main_frame, text="", font=THEME["font_timer"],
                                    bg=THEME["bg"], fg=THEME["accent"])
        self.timer_label.pack(pady=(0, 20))

        self.minimize_btn = FlatButton(main_frame, text="Minimize to tray", command=self.minimize_to_tray)
        self.minimize_btn.config(font=("Helvetica", 14), padx=24, pady=12)
        self.minimize_btn.pack(pady=(0, 20))

        interval_frame = tk.Frame(main_frame, bg=THEME["bg"])
        interval_frame.pack(pady=(0, 10))

        self.interval_buttons = {}

        debug_btn = FlatButton(interval_frame, text="5s", command=lambda: self.set_interval_seconds(5))
        debug_btn.pack(side=tk.LEFT, padx=6)
        self.interval_buttons["5s"] = debug_btn
        debug_btn.bind("<Leave>", lambda e: self._interval_leave("5s"))

        for val in [20, 30, 45, 60]:
            key = f"{val}m"
            btn = FlatButton(interval_frame, text=str(val),
                             command=lambda v=val: self.set_interval(v))
            btn.pack(side=tk.LEFT, padx=6)
            self.interval_buttons[key] = btn
            btn.bind("<Leave>", lambda e, k=key: self._interval_leave(k))
        self._update_interval_buttons()

        self.restart_btn = FlatButton(main_frame, text="Restart Focus", command=self.restart_timer)

    def _center_window(self):
        """Center main window on screen (called after setup_ui and tray)."""
        self.root.update_idletasks()
        w, h = 400, 380
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _apply_no_decorations(self):
        """Remove OS window decorations on Windows and rely on tray-based minimize/exit."""
        if sys.platform != "win32":
            _log("apply_no_decorations: skipped (non-Windows)")
            return
        try:
            self.root.overrideredirect(True)
            _log("apply_no_decorations: enabled")
        except Exception as e:
            _log(f"apply_no_decorations: error {type(e).__name__}: {e}")

    def _after_first_map(self):
        """Runs once after window is shown: strip decorations, then start tray."""
        _log("after_first_map: start")
        self._apply_no_decorations()
        try:
            _log("after_first_map: starting tray")
            self._start_tray()
            _log("after_first_map: tray started")
        except Exception as e:
            _log(f"after_first_map: tray error {e}")
        _log("after_first_map: done")

    def minimize_to_tray(self):
        """Hide main window; restore via tray icon double-click or Show menu."""
        try:
            _log("minimize_to_tray: withdraw()")
            self.root.withdraw()
        except Exception as e:
            _log(f"minimize_to_tray: exception {type(e).__name__}: {e}")

    def _show_from_tray(self):
        """Restore main window from tray (called on main thread)."""
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(200, lambda: self.root.attributes("-topmost", False))
        try:
            self.root.focus_force()
        except Exception:
            pass
        self._on_focus_in()

    def _on_focus_in(self, _event=None):
        """Foreground callback: stop chime immediately."""
        self._app_in_foreground = True
        _stop_chime()

    def _request_close(self):
        """Normal close routes through tray minimize so the timer keeps running."""
        if self._is_quitting:
            return
        self.minimize_to_tray()

    def quit_app(self):
        """Fully exit the application. Intended for tray menu only."""
        if self._is_quitting:
            return
        self._is_quitting = True
        _stop_chime()
        if self.break_countdown_job:
            try:
                self.root.after_cancel(self.break_countdown_job)
            except Exception:
                pass
            self.break_countdown_job = None
        try:
            if self.tray_icon is not None:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _start_tray(self):
        """Start system tray icon using pure ctypes (Windows only)."""
        if sys.platform != "win32":
            _log("_start_tray: skipped (Windows only)")
            return
        try:
            icon = Win32TrayIcon(
                tooltip="Break reminder",
                on_show=lambda: self.root.after(0, self._show_from_tray),
                on_exit=lambda: self.root.after(0, self.quit_app),
            )
            icon.run_detached()
            self.tray_icon = icon
            _log("_start_tray: Win32TrayIcon running")
        except Exception as e:
            _log(f"_start_tray: error {type(e).__name__}: {e}")
            import traceback
            try:
                with open(DEBUG_LOG, "a", encoding="utf-8") as f:
                    traceback.print_exc(file=f)
            except Exception:
                pass

    def _interval_leave(self, key):
        btn = self.interval_buttons[key]
        if key == "5s" and self.config.get("default_seconds") == 5:
            btn.config(bg=THEME["accent"], fg="white")
        elif key.endswith("m") and int(key[:-1]) == self.config["default_minutes"] and self.config.get("default_seconds") is None:
            btn.config(bg=THEME["accent"], fg="white")
        else:
            btn.config(bg=THEME["secondary"], fg=THEME["fg"])

    def _update_interval_buttons(self):
        for key, btn in self.interval_buttons.items():
            if key == "5s" and self.config.get("default_seconds") == 5:
                btn.config(bg=THEME["accent"], fg="white")
            elif key.endswith("m") and int(key[:-1]) == self.config["default_minutes"] and self.config.get("default_seconds") is None:
                btn.config(bg=THEME["accent"], fg="white")
            else:
                btn.config(bg=THEME["secondary"], fg=THEME["fg"])

    def set_interval(self, minutes):
        self.config["default_seconds"] = None
        self.config["default_minutes"] = minutes
        self.save_config()
        self._update_interval_buttons()
        self.restart_timer()

    def set_interval_seconds(self, seconds):
        self.config["default_seconds"] = seconds
        self.save_config()
        self._update_interval_buttons()
        self.restart_timer()

    def get_work_duration_seconds(self):
        default_seconds = self.config.get("default_seconds")
        if isinstance(default_seconds, int) and default_seconds > 0:
            return default_seconds
        return self.config["default_minutes"] * 60

    def restart_timer(self):
        _stop_chime()
        self._last_chime_time = 0
        self.show_focus_view()
        if self.restart_btn.winfo_ismapped():
            self.restart_btn.pack_forget()
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
        if self.break_countdown_job:
            self.root.after_cancel(self.break_countdown_job)
            self.break_countdown_job = None
        self.reminder_window = None

        self.time_left = self.get_work_duration_seconds()
        self.update_timer_display()
        self.start_timer()
        
    def start_timer(self):
        _log("start_timer: update_display then after(1000, tick)")
        self.update_timer_display()
        self.timer_job = self.root.after(1000, self.tick)

    def update_timer_display(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")

    def tick(self):
        if self.time_left % 60 == 0 or self.time_left <= 5:
            _log(f"tick: time_left={self.time_left}")
        try:
            if self.time_left > 0:
                self.time_left -= 1
                self.update_timer_display()
                self.timer_job = self.root.after(1000, self.tick)
            else:
                _log("tick: time up, showing reminder")
                self.restart_btn.pack(pady=(15, 0))
                self.show_break_reminder("Time to take a mindful break.")
        except Exception as e:
            _log(f"tick: exception {e}")
            import traceback
            traceback.print_exc()
            self.timer_job = self.root.after(1000, self.tick)
            
    def get_ignore_rate(self):
        history = self.config.get("break_history", [])
        if not history: return 0.0
        recent = history[-5:]
        if not recent: return 0.0
        ignored = sum(1 for r in recent if not r.get("acknowledged", True))
        return (ignored / len(recent)) * 100
        
    def record_break_result(self, acknowledged):
        if "break_history" not in self.config:
            self.config["break_history"] = []
        self.config["break_history"].append({
            "acknowledged": acknowledged,
            "timestamp": time.time()
        })
        if len(self.config["break_history"]) > 10:
            self.config["break_history"] = self.config["break_history"][-10:]
        self.save_config()

    def show_break_reminder(self, message):
        # Bring main to front briefly to ensure visibility
        self.root.attributes('-topmost', True)
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.after(200, lambda: self.root.attributes('-topmost', False))

        self.root.title("Mindful Pause")
        self._clear_body()
        self.reminder_window = self.root

        main_frame = tk.Frame(self.body, bg=THEME["bg"])
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(main_frame, text=message, font=THEME["font_title"], 
                 bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(0, 10))
                 
        self.joke_shown = False
        self.break_was_ignored = False

        tk.Label(main_frame, text="Keep me in the forefront until the countdown ends for a joke!", 
                 font=THEME["font_small"], bg=THEME["bg"], fg=THEME["accent"]).pack(pady=(0, 5))
        
        self.break_time_left = 60 # 1 minute
        self._last_break_tick_at = time.time()
        self.break_timer_label = tk.Label(main_frame, text="01:00", 
                                         font=THEME["font_timer"], bg=THEME["bg"], fg=THEME["accent"])
        self.break_timer_label.pack(pady=(0, 15))
            
        self.joke_container = tk.Frame(main_frame, bg=THEME["bg"])
        self.joke_container.pack(fill="x", pady=5)
        
        btn_frame = tk.Frame(main_frame, bg=THEME["bg"])
        btn_frame.pack(pady=10)
        
        self.ok_btn = FlatButton(btn_frame, text="Resume Focus",
                                 command=lambda: self.on_reminder_close(True))
        self.ok_btn.pack(side=tk.LEFT, padx=10)
        
        # Initially disabled visual state
        self.ok_btn.config(state="disabled", bg="#E4E4E4", fg="#A9A9A9") 
            
        FlatButton(btn_frame, text="Minimize",
                   command=self.minimize_to_tray).pack(side=tk.LEFT, padx=10)

        # Start combined monitor and countdown loop
        self.break_tick()

    def _is_app_in_foreground(self):
        if self.root.state() in ("iconic", "withdrawn"):
            return False
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = self.root.winfo_id()
                GA_ROOT = 2
                top_hwnd = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
                if not user32.IsWindowVisible(top_hwnd) or user32.IsIconic(top_hwnd):
                    return False

                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

                class RECT(ctypes.Structure):
                    _fields_ = [
                        ("left", ctypes.c_long),
                        ("top", ctypes.c_long),
                        ("right", ctypes.c_long),
                        ("bottom", ctypes.c_long),
                    ]

                def root_owner(window_handle):
                    GA_ROOT = 2
                    return user32.GetAncestor(window_handle, GA_ROOT)

                # winfo_id() returns inner Tk frame; get actual top-level HWND
                my_root = root_owner(hwnd)
                # Collect all HWNDs that belong to this app
                app_hwnds = {h for h in (hwnd, my_root) if h}

                fg = user32.GetForegroundWindow()
                if fg:
                    fg_root = root_owner(fg)
                    if fg in app_hwnds or fg_root in app_hwnds:
                        return True

                # Fallback: check if window is topmost at sample points
                rect = RECT()
                if not user32.GetWindowRect(my_root or hwnd, ctypes.byref(rect)):
                    return False

                sample_points = [
                    POINT((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2),
                    POINT(rect.left + ((rect.right - rect.left) // 4), (rect.top + rect.bottom) // 2),
                    POINT(rect.right - ((rect.right - rect.left) // 4), (rect.top + rect.bottom) // 2),
                ]

                hits = 0
                for point in sample_points:
                    top_at_point = user32.WindowFromPoint(point)
                    if top_at_point:
                        top_root = root_owner(top_at_point)
                        if top_at_point in app_hwnds or top_root in app_hwnds:
                            hits += 1
                return hits >= 2
            except Exception:
                return self.root.focus_displayof() is not None
        return self.root.focus_displayof() is not None

    def break_tick(self):
        if not self.reminder_window or not self.root.winfo_exists():
            return

        now = time.time()
        elapsed = 1.0 if self._last_break_tick_at is None else now - self._last_break_tick_at
        self._last_break_tick_at = now

        self._app_in_foreground = self._is_app_in_foreground()

        # As soon as app is in foreground, stop chime immediately (even mid-play)
        if self._app_in_foreground:
            _stop_chime()

        if elapsed > 10:
            _log(f"break_tick: detected sleep/resume gap of {elapsed:.1f}s")
            self.break_countdown_job = self.root.after(1000, self.break_tick)
            return

        # Count down hidden time while minimized/withdrawn
        is_visible = self.root.state() not in ('iconic', 'withdrawn')

        # Handle countdown
        if self.break_time_left > 0:
            minutes = self.break_time_left // 60
            seconds = self.break_time_left % 60
            if hasattr(self, 'break_timer_label') and self.break_timer_label.winfo_exists():
                self.break_timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.break_time_left -= 1
            
        elif self.break_time_left == 0:
            if hasattr(self, 'break_timer_label') and self.break_timer_label.winfo_exists():
                self.break_timer_label.config(text="00:00")
                
            # Enable OK button
            if hasattr(self, 'ok_btn') and self.ok_btn.winfo_exists():
                self.ok_btn.config(state="normal", bg=THEME["secondary"], fg=THEME["fg"])

            # Determine ignored state exactly at expiry: hidden when countdown reaches zero.
            self.break_was_ignored = not is_visible

            if hasattr(self, 'joke_container') and self.joke_container.winfo_exists():
                for child in self.joke_container.winfo_children():
                    child.destroy()

                if self.break_was_ignored:
                    tk.Label(
                        self.joke_container,
                        text="Trying to ignore me? Rejection hurts...",
                        font=THEME["font_main"],
                        bg=THEME["bg"],
                        fg=THEME["accent"],
                        wraplength=380,
                        justify="center"
                    ).pack()
                elif not self.joke_shown:
                    joke = random.choice(JOKES)
                    tk.Label(
                        self.joke_container,
                        text=f"✨ {joke}",
                        font=THEME["font_main"],
                        bg=THEME["bg"],
                        fg=THEME["accent"],
                        wraplength=380,
                        justify="center"
                    ).pack()
                    self.joke_shown = True

            self.break_time_left -= 1  # Prevent entering this branch multiple times

        # After countdown has ended: chime once every 32s while not in foreground
        if self.break_time_left < 0 and not self._app_in_foreground:
            now = time.time()
            if now - self._last_chime_time >= 32:
                _play_chime_once()
                self._last_chime_time = now
                _log("chiming: played")

        # Keep monitoring
        self.break_countdown_job = self.root.after(1000, self.break_tick)

    def on_reminder_close(self, acknowledged):
        if self.break_countdown_job:
            self.root.after_cancel(self.break_countdown_job)
            self.break_countdown_job = None
        self._last_break_tick_at = None
            
        self.record_break_result(acknowledged and not self.break_was_ignored)
        
        self.reminder_window = None
        self.restart_timer()

    def run(self):
        _log("run: entering mainloop")
        self.root.mainloop()
        _log("run: mainloop returned (app closing)")

def add_to_startup():
    if not WINDOWS_SUPPORT:
        print("Startup registration is only available on Windows")
        return False
        
    try:
        import winreg as wr
        key = wr.HKEY_CURRENT_USER
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
        script_path = os.path.abspath(sys.argv[0])
        
        with wr.OpenKey(key, key_path, 0, wr.KEY_SET_VALUE) as registry_key:
            wr.SetValueEx(registry_key, "BreakTimer", 0, wr.REG_SZ, script_path)
        
        return True
    except Exception as e:
        print(f"Failed to add to startup: {e}")
        return False

def main():
    _log("main: start")
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        if add_to_startup():
            messagebox.showinfo("Success", "Break reminder has been added to startup!")
        else:
            messagebox.showerror("Error", "Failed to add to startup.")
        return

    # Hide console window on Windows so only the GUI is visible
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
        except Exception:
            pass
    
    _log("main: creating BreakTimer")
    app = BreakTimer()
    _log("main: calling app.run()")
    app.run()
    _log("main: exit")

if __name__ == "__main__":
    main()

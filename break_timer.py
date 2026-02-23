import tkinter as tk
from tkinter import messagebox
import json
import os
import time
import sys
import random
import threading

# Debug logging to file (same directory as script)
DEBUG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "break_timer_debug.log")

def _log(msg):
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
            f.flush()
    except Exception:
        pass

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

def create_tray_icon_image():
    """Create a simple pastel sage tray icon (64x64 RGBA)."""
    try:
        from PIL import Image, ImageDraw
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Sage circle
        margin = 8
        d.ellipse([margin, margin, size - margin, size - margin], fill=(159, 180, 166, 255))
        return img
    except Exception:
        return None

def make_title_bar(parent, window, title, on_close, on_minimize=None):
    """Custom title bar with title, minimize, and close. Draggable."""
    bar = tk.Frame(parent, bg=THEME["titlebar"], height=36)
    bar.pack(side=tk.TOP, fill=tk.X)
    bar.pack_propagate(False)
    tk.Label(bar, text=title, bg=THEME["titlebar"], fg=THEME["fg"],
             font=THEME["font_main"]).pack(side=tk.LEFT, padx=12, pady=8)
    min_btn = tk.Label(bar, text=" − ", bg=THEME["titlebar"], fg=THEME["fg"],
                      font=("Helvetica", 16), cursor="hand2")
    min_btn.pack(side=tk.RIGHT, padx=(0, 2), pady=4)
    def do_minimize(e):
        if on_minimize is not None:
            on_minimize()
        else:
            window.iconify()
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
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        self.root.configure(bg=THEME["bg"])
        self.config_file = "break_timer_config.json"
        self.config = self.load_config()
        
        self.time_left = self.config["default_minutes"] * 60
        self.timer_job = None
        self.reminder_window = None
        self.break_countdown_job = None
        self.tray_icon = None
        _log("init: starting setup_ui")
        self.setup_ui()
        _log("init: setup_ui done")
        self._center_window()
        _log("init: center done, starting timer")
        self.start_timer()
        # After first map: strip decorations and start tray (avoids hang on X11/WSL)
        self.root.after(100, self._after_first_map)
        _log("init: after(100) scheduled, __init__ done")
        
    def load_config(self):
        default_config = {
            "default_minutes": 30,
            "break_history": []
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return default_config
        return default_config
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
            
    def setup_ui(self):
        _log("setup_ui: make_title_bar")
        make_title_bar(self.root, self.root, "Break reminder", on_close=self.root.quit, on_minimize=self.minimize_to_tray)
        _log("setup_ui: body frame")
        # Body: centered content
        body = tk.Frame(self.root, bg=THEME["bg"])
        body.pack(fill=tk.BOTH, expand=True)
        body.config(width=400, height=264)  # avoid collapse before first layout

        main_frame = tk.Frame(body, bg=THEME["bg"])
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        tk.Label(main_frame, text="Focus Session", font=THEME["font_title"], 
                 bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(0, 15))
                 
        # Timer Display
        self.timer_label = tk.Label(main_frame, text="", font=THEME["font_timer"], 
                                    bg=THEME["bg"], fg=THEME["accent"])
        self.timer_label.pack(pady=(0, 25))
        
        # Interval Selection: buttons with label on the button
        interval_frame = tk.Frame(main_frame, bg=THEME["bg"])
        interval_frame.pack(pady=(0, 25))
        
        self.interval_buttons = {}
        for val in [20, 30, 45, 60]:
            btn = FlatButton(interval_frame, text=str(val),
                            command=lambda v=val: self.set_interval(v))
            btn.pack(side=tk.LEFT, padx=6)
            self.interval_buttons[val] = btn
            btn.bind("<Leave>", lambda e, v=val: self._interval_leave(v))
        self._update_interval_buttons()
            
        # Restart Button — only shown after focus session completes
        self.restart_btn = FlatButton(main_frame, text="Restart Focus", command=self.restart_timer)
        # don't pack yet; shown when timer hits zero
        _log("setup_ui: done")

    def _center_window(self):
        """Center main window on screen (called after setup_ui and tray)."""
        self.root.update_idletasks()
        w, h = 400, 300
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _apply_no_decorations(self):
        """Remove OS window decorations (call after first map to avoid hang)."""
        # overrideredirect on Linux/WSL can trigger X11/xcb crashes in some setups; skip.
        if sys.platform != "win32":
            _log("apply_no_decorations: skipped on non-Windows")
            return
        try:
            _log("apply_no_decorations: setting overrideredirect(True)")
            self.root.overrideredirect(True)
            self._center_window()
            _log("apply_no_decorations: done")
        except Exception as e:
            _log(f"apply_no_decorations: error {e}")

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
        """Hide main window to system tray (or iconify if no tray)."""
        if self.tray_icon is not None:
            self.root.withdraw()
        else:
            self.root.iconify()

    def _show_from_tray(self):
        """Restore main window from tray (called on main thread)."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _start_tray(self):
        """Start system tray icon in a background thread (if pystray/Pillow available)."""
        # Tray on Linux/WSL uses X11 in a thread and conflicts with Tkinter's X11 usage -> crash.
        # Only enable tray on Windows.
        if sys.platform != "win32":
            _log("_start_tray: skipped (tray only on Windows to avoid X11 conflict)")
            return
        def run_tray():
            try:
                _log("tray thread: import pystray")
                import pystray
                _log("tray thread: create image")
                img = create_tray_icon_image()
                if img is None:
                    _log("tray thread: no image, exit")
                    return
                root = self.root
                _log("tray thread: create Icon")
                icon = pystray.Icon(
                    "break_reminder",
                    img,
                    "Break reminder",
                    menu=pystray.Menu(
                        pystray.MenuItem("Show", lambda i, _: root.after(0, self._show_from_tray)),
                        pystray.MenuItem("Quit", lambda i, _: (root.after(0, root.quit), i.stop())),
                    ),
                )
                self.tray_icon = icon
                _log("tray thread: calling icon.run()")
                icon.run()
                _log("tray thread: icon.run() returned")
            except Exception as e:
                _log(f"tray thread: exception {type(e).__name__}: {e}")
                import traceback
                try:
                    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
                        traceback.print_exc(file=f)
                except Exception:
                    pass
        try:
            import pystray
        except ImportError:
            _log("_start_tray: pystray not installed")
            return
        _log("_start_tray: starting tray thread")
        threading.Thread(target=run_tray, daemon=True).start()

    def _interval_leave(self, val):
        btn = self.interval_buttons[val]
        if val == self.config["default_minutes"]:
            btn.config(bg=THEME["accent"], fg="white")
        else:
            btn.config(bg=THEME["secondary"], fg=THEME["fg"])

    def _update_interval_buttons(self):
        for val, btn in self.interval_buttons.items():
            if val == self.config["default_minutes"]:
                btn.config(bg=THEME["accent"], fg="white")
            else:
                btn.config(bg=THEME["secondary"], fg=THEME["fg"])

    def set_interval(self, minutes):
        self.config["default_minutes"] = minutes
        self.save_config()
        self._update_interval_buttons()
        self.restart_timer()

    def restart_timer(self):
        if self.restart_btn.winfo_ismapped():
            self.restart_btn.pack_forget()
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
        if self.reminder_window and self.reminder_window.winfo_exists():
            self.reminder_window.destroy()
        self.reminder_window = None
            
        self.time_left = self.config["default_minutes"] * 60
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

    def show_break_reminder(self, message, is_ignore_message=False):
        # Bring main to front briefly to ensure visibility
        self.root.attributes('-topmost', True)
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', False)
        
        if self.reminder_window and self.reminder_window.winfo_exists():
            self.reminder_window.destroy()
            
        self.reminder_window = tk.Toplevel(self.root)
        self.reminder_window.title("Mindful Pause")
        self.reminder_window.geometry("450x320")
        self.reminder_window.resizable(False, False)
        self.reminder_window.configure(bg=THEME["bg"])
        self.reminder_window.attributes('-topmost', True)

        make_title_bar(self.reminder_window, self.reminder_window, "Mindful Pause",
                      on_close=lambda: self.on_reminder_close(False))
        rem_body = tk.Frame(self.reminder_window, bg=THEME["bg"])
        rem_body.pack(fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(rem_body, bg=THEME["bg"])
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(main_frame, text=message, font=THEME["font_title"], 
                 bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(0, 10))
                 
        ignore_rate = self.get_ignore_rate()
        self.show_joke_incentive = ignore_rate > 40 and not is_ignore_message
        self.joke_shown = False
        
        if self.show_joke_incentive:
            tk.Label(main_frame, text="Stay mindful for a little humor...", 
                     font=THEME["font_small"], bg=THEME["bg"], fg=THEME["accent"]).pack(pady=(0, 5))
                     
        self.is_ignore_message = is_ignore_message
        self.hidden_time = 0
        
        if not is_ignore_message:
            self.break_time_left = 120 # 2 minutes
            self.break_timer_label = tk.Label(main_frame, text="02:00", 
                                             font=THEME["font_timer"], bg=THEME["bg"], fg=THEME["accent"])
            self.break_timer_label.pack(pady=(0, 15))
        else:
            self.break_time_left = 0
            
        self.joke_container = tk.Frame(main_frame, bg=THEME["bg"])
        self.joke_container.pack(fill="x", pady=5)
        
        btn_frame = tk.Frame(main_frame, bg=THEME["bg"])
        btn_frame.pack(pady=10)
        
        btn_text = "Fine, I'll take a break" if is_ignore_message else "Resume Focus"
        self.ok_btn = FlatButton(btn_frame, text=btn_text, 
                                 command=lambda: self.on_reminder_close(True))
        self.ok_btn.pack(side=tk.LEFT, padx=10)
        
        if not is_ignore_message:
            # Initially disabled visual state
            self.ok_btn.config(state="disabled", bg="#E4E4E4", fg="#A9A9A9") 
            
        FlatButton(btn_frame, text="Minimize", 
                   command=lambda: self.reminder_window.iconify()).pack(side=tk.LEFT, padx=10)

        self.reminder_window.update_idletasks()
        rw, rh = 450, 320
        rx = (self.reminder_window.winfo_screenwidth() // 2) - (rw // 2)
        ry = (self.reminder_window.winfo_screenheight() // 2) - (rh // 2)
        self.reminder_window.geometry(f"{rw}x{rh}+{rx}+{ry}")
        self.reminder_window.overrideredirect(True)

        # Start combined monitor and countdown loop
        self.break_tick()

    def break_tick(self):
        if not self.reminder_window or not self.reminder_window.winfo_exists():
            return
            
        # Check if window is minimized (iconic)
        is_visible = self.reminder_window.state() != 'iconic'
        
        if not is_visible:
            self.hidden_time += 1
            if self.hidden_time >= 120:
                self.on_reminder_close(False, was_ignored=True)
                return
        else:
            self.hidden_time = 0
            
        # Handle countdown if applicable
        if not self.is_ignore_message and self.break_time_left > 0:
            minutes = self.break_time_left // 60
            seconds = self.break_time_left % 60
            if hasattr(self, 'break_timer_label') and self.break_timer_label.winfo_exists():
                self.break_timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.break_time_left -= 1
            
        elif not self.is_ignore_message and self.break_time_left == 0:
            if hasattr(self, 'break_timer_label') and self.break_timer_label.winfo_exists():
                self.break_timer_label.config(text="00:00")
                
            # Enable OK button
            if hasattr(self, 'ok_btn') and self.ok_btn.winfo_exists():
                self.ok_btn.config(state="normal", bg=THEME["secondary"], fg=THEME["fg"])
                
            # Show joke incentive if applicable
            if self.show_joke_incentive and not self.joke_shown:
                joke = random.choice(JOKES)
                if hasattr(self, 'joke_container') and self.joke_container.winfo_exists():
                    tk.Label(self.joke_container, text=f"✨ {joke}", font=THEME["font_main"], 
                             bg=THEME["bg"], fg=THEME["accent"], wraplength=380, justify="center").pack()
                self.joke_shown = True
                
            self.break_time_left -= 1 # Prevent entering this branch multiple times
            
        # Keep monitoring
        self.break_countdown_job = self.root.after(1000, self.break_tick)

    def on_reminder_close(self, acknowledged, was_ignored=False):
        if self.break_countdown_job:
            self.root.after_cancel(self.break_countdown_job)
            self.break_countdown_job = None
            
        self.record_break_result(acknowledged)
        
        if self.reminder_window and self.reminder_window.winfo_exists():
            self.reminder_window.destroy()
        self.reminder_window = None
            
        if was_ignored:
            self.show_break_reminder("Trying to ignore me? Rejection hurts...", is_ignore_message=True)
        else:
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

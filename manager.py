import os
import sys
import atexit
import threading
import subprocess
import socket
import webbrowser
import time
import queue
from pathlib import Path
import tkinter as tk
import tkinter.messagebox as messagebox
import customtkinter as ctk

from portal_settings_dialog import PortalSettingsDialog

# Add current directory to path for shared module import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared import (
    BASE_DIR,
    DB_FILE,
    ARCHIVE_DB_FILE,
    DASHBOARD_PORT,
    API_PORT,
    DB_TIMEOUT,
)
from tools.db_watcher import DBWatcher


# ==========================================================
# Process Cleanup on Exit
# ==========================================================
_active_processes: list[subprocess.Popen] = []
_process_lock = threading.Lock()


def _cleanup_all_processes() -> None:
    """Cleanup all managed subprocesses on program exit."""
    with _process_lock:
        for proc in _active_processes:
            try:
                if proc.poll() is None:
                    _taskkill_tree(proc.pid)
            except Exception:
                pass
        _active_processes.clear()


def _register_process(proc: subprocess.Popen) -> None:
    """Register a process for cleanup on exit."""
    with _process_lock:
        _active_processes.append(proc)


def _unregister_process(proc: subprocess.Popen) -> None:
    """Unregister a process from cleanup."""
    with _process_lock:
        try:
            _active_processes.remove(proc)
        except ValueError:
            pass


# Register cleanup on exit
atexit.register(_cleanup_all_processes)

# ==========================================================
# Configuration & Constants
# ==========================================================
PY = sys.executable

# CustomTkinter Settings
ctk.set_appearance_mode("Dark") # Force Dark mode for better contrast
ctk.set_default_color_theme("blue")

# Colors
COLOR_SUCCESS = "#4caf50" # Green
COLOR_ERROR = "#ef5350"   # Red
COLOR_WARN = "#ffb74d"    # Orange
COLOR_INFO = "#e0e0e0"    # Light Gray
COLOR_MUTED = "#757575"   # Dark Gray
COLOR_BG_CARD = "#2b2b2b" # Card Background



# ==========================================================
# Helpers
# ==========================================================
def _get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def _is_port_in_use(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def _taskkill_tree(pid: int):
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        pass


# ==========================================================
# Manager UI (v3.0 - Portal Integration)
# ==========================================================
class ServerManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Production Data Hub Manager")
        self.geometry("1200x850")
        self.local_ip = _get_local_ip()
        
        # State
        self.proc_web = None
        self.proc_api = None
        self.proc_portal = None
        self.log_queue = queue.Queue()
        self.watcher = None

        # --- Layout (2×2 grid) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=3) # Web/API Panel
        self.grid_rowconfigure(2, weight=2) # DB + Portal Panel

        # --- Sections ---
        self._init_header()
        self._init_web_panel()
        self._init_api_panel()
        self._init_db_panel()
        self._init_portal_panel()

        # Start Queue Listener
        self.after(100, self._process_log_queue)
        
        # Auto-start Watcher
        self.toggle_watcher()

        # Safety on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _init_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame, 
            text="Production Data Hub", 
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        )
        title_label.pack(side="left")

        ip_badge = ctk.CTkButton(
            header_frame, text=f"Host: {self.local_ip}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#424242", hover=False, height=28, corner_radius=14,
            text_color_disabled="#E0E0E0", state="disabled"
        )
        ip_badge.pack(side="right")

    def _init_web_panel(self):
        self.web_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=COLOR_BG_CARD)
        self.web_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        self.web_frame.grid_rowconfigure(3, weight=1)
        self.web_frame.grid_columnconfigure(0, weight=1)

        # Status Bar (Visual Indicator)
        self.web_status_bar = ctk.CTkFrame(self.web_frame, height=4, fg_color=COLOR_MUTED, corner_radius=2)
        self.web_status_bar.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        # Content
        content_box = ctk.CTkFrame(self.web_frame, fg_color="transparent")
        content_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        ctk.CTkLabel(content_box, text="📊 Dashboard", text_color="#ffffff", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        self.lbl_web_status = ctk.CTkLabel(content_box, text="Stopped", text_color=COLOR_MUTED, font=ctk.CTkFont(size=14))
        self.lbl_web_status.pack(anchor="w", pady=(0, 10))

        # Controls
        ctrl_frame = ctk.CTkFrame(self.web_frame, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.btn_web_start = ctk.CTkButton(ctrl_frame, text="▶ Start", command=self.start_web, fg_color="#1f6aa5", width=80)
        self.btn_web_start.pack(side="left", padx=(0, 5))
        self.btn_web_stop = ctk.CTkButton(ctrl_frame, text="■ Stop", command=self.stop_web, fg_color="#c62828", state="disabled", width=80)
        self.btn_web_stop.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="🔗 Open", command=lambda: webbrowser.open(f"http://{self.local_ip}:{DASHBOARD_PORT}"), fg_color="#424242", width=60).pack(side="left", padx=5)

        self.log_web = ctk.CTkTextbox(self.web_frame, font=("Consolas", 12), text_color="#eeeeee", activate_scrollbars=True)
        self.log_web.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)
        self.log_web.configure(state="disabled")
        
        # Tags for coloring
        self.log_web.tag_config("INFO", foreground=COLOR_INFO)
        self.log_web.tag_config("WARN", foreground=COLOR_WARN)
        self.log_web.tag_config("ERROR", foreground=COLOR_ERROR)
        self.log_web.tag_config("SUCCESS", foreground=COLOR_SUCCESS)

    def _init_api_panel(self):
        self.api_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=COLOR_BG_CARD)
        self.api_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        self.api_frame.grid_rowconfigure(3, weight=1)
        self.api_frame.grid_columnconfigure(0, weight=1)

        # Status Bar
        self.api_status_bar = ctk.CTkFrame(self.api_frame, height=4, fg_color=COLOR_MUTED, corner_radius=2)
        self.api_status_bar.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        # Content
        content_box = ctk.CTkFrame(self.api_frame, fg_color="transparent")
        content_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        ctk.CTkLabel(content_box, text="⚡ API Gateway", text_color="#ffffff", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        self.lbl_api_status = ctk.CTkLabel(content_box, text="Stopped", text_color=COLOR_MUTED, font=ctk.CTkFont(size=14))
        self.lbl_api_status.pack(anchor="w", pady=(0, 10))

        # Controls
        ctrl_frame = ctk.CTkFrame(self.api_frame, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.btn_api_start = ctk.CTkButton(ctrl_frame, text="▶ Start", command=self.start_api, fg_color="#2e7d32", width=80)
        self.btn_api_start.pack(side="left", padx=(0, 5))
        self.btn_api_stop = ctk.CTkButton(ctrl_frame, text="■ Stop", command=self.stop_api, fg_color="#c62828", state="disabled", width=80)
        self.btn_api_stop.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="🔗 Docs", command=lambda: webbrowser.open(f"http://{self.local_ip}:{API_PORT}/docs"), fg_color="#424242", width=60).pack(side="left", padx=5)

        self.log_api = ctk.CTkTextbox(self.api_frame, font=("Consolas", 12), text_color="#eeeeee", activate_scrollbars=True)
        self.log_api.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)
        self.log_api.configure(state="disabled")
        
        self.log_api.tag_config("INFO", foreground=COLOR_INFO)
        self.log_api.tag_config("WARN", foreground=COLOR_WARN)
        self.log_api.tag_config("ERROR", foreground=COLOR_ERROR)
        self.log_api.tag_config("SUCCESS", foreground=COLOR_SUCCESS)

    def _init_db_panel(self):
        self.db_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=COLOR_BG_CARD)
        self.db_frame.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=(10, 20))
        self.db_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_frame = ctk.CTkFrame(self.db_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=20, pady=20)
        
        ctk.CTkLabel(title_frame, text="🔧 DB Automation", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        self.lbl_watcher_status = ctk.CTkLabel(title_frame, text="Active (1h)", text_color=COLOR_SUCCESS, font=ctk.CTkFont(size=12))
        self.lbl_watcher_status.pack(anchor="w")

        # Controls
        btn_frame = ctk.CTkFrame(self.db_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="🛠️ Check Now", command=self.manual_db_check, 
                      fg_color="#e65100", hover_color="#ef6c00", width=120).pack(side="right", padx=10)
        
        self.btn_toggle_watcher = ctk.CTkButton(btn_frame, text="Pause", command=self.toggle_watcher, 
                                                fg_color="#546e7a", width=100)
        self.btn_toggle_watcher.pack(side="right")

        # Log Area
        self.log_db = ctk.CTkTextbox(self.db_frame, height=80, font=("Consolas", 11), text_color="#eeeeee", activate_scrollbars=True)
        self.log_db.grid(row=0, column=1, sticky="nsew", padx=10, pady=15)
        self.log_db.configure(state="disabled")
        
        self.log_db.tag_config("INFO", foreground=COLOR_INFO)
        self.log_db.tag_config("WARN", foreground=COLOR_WARN)
        self.log_db.tag_config("ERROR", foreground=COLOR_ERROR)
        self.log_db.tag_config("SUCCESS", foreground=COLOR_SUCCESS)
        
        self.append_log(self.log_db, ">>> Automation System Initialized.", "INFO")

    def _init_portal_panel(self):
        self.portal_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=COLOR_BG_CARD)
        self.portal_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 20), pady=(10, 20))
        self.portal_frame.grid_rowconfigure(3, weight=1)
        self.portal_frame.grid_columnconfigure(0, weight=1)

        # Status Bar
        self.portal_status_bar = ctk.CTkFrame(self.portal_frame, height=4, fg_color=COLOR_MUTED, corner_radius=2)
        self.portal_status_bar.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        # Content
        content_box = ctk.CTkFrame(self.portal_frame, fg_color="transparent")
        content_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        ctk.CTkLabel(content_box, text="🤖 Portal Automation", text_color="#ffffff", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        self.lbl_portal_status = ctk.CTkLabel(content_box, text="Stopped", text_color=COLOR_MUTED, font=ctk.CTkFont(size=14))
        self.lbl_portal_status.pack(anchor="w", pady=(0, 10))

        # Controls
        ctrl_frame = ctk.CTkFrame(self.portal_frame, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.btn_portal_start = ctk.CTkButton(ctrl_frame, text="▶ Start", command=self.start_portal, fg_color="#6a1b9a", width=80)
        self.btn_portal_start.pack(side="left", padx=(0, 5))
        self.btn_portal_stop = ctk.CTkButton(ctrl_frame, text="■ Stop", command=self.stop_portal, fg_color="#c62828", state="disabled", width=80)
        self.btn_portal_stop.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="🚀 Run Now", command=self.run_portal_now, fg_color="#e65100", hover_color="#ef6c00", width=100).pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="⚙️ Settings", command=self.open_portal_settings, fg_color="#37474f", hover_color="#546e7a", width=100).pack(side="left", padx=5)

        # Log Area
        self.log_portal = ctk.CTkTextbox(self.portal_frame, font=("Consolas", 12), text_color="#eeeeee", activate_scrollbars=True)
        self.log_portal.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)
        self.log_portal.configure(state="disabled")

        self.log_portal.tag_config("INFO", foreground=COLOR_INFO)
        self.log_portal.tag_config("WARN", foreground=COLOR_WARN)
        self.log_portal.tag_config("ERROR", foreground=COLOR_ERROR)
        self.log_portal.tag_config("SUCCESS", foreground=COLOR_SUCCESS)

    # --------------------------
    # Logging with Colors
    # --------------------------
    def _process_log_queue(self):
        while not self.log_queue.empty():
            try:
                level, msg = self.log_queue.get_nowait()
                timestamp = time.strftime("%H:%M:%S")
                log_msg = f"[{timestamp}] {msg}"
                self.append_log(self.log_db, log_msg, level)
            except queue.Empty:
                break
        self.after(200, self._process_log_queue)

    def append_log(self, widget, text, level="INFO"):
        widget.configure(state="normal")
        widget.insert(tk.END, text + "\n", level) # Apply tag
        widget.see(tk.END)
        widget.configure(state="disabled")

    # --------------------------
    # Logic
    # --------------------------
    def toggle_watcher(self):
        if self.watcher and self.watcher.is_alive():
            self.watcher.stop()
            self.watcher = None
            self.lbl_watcher_status.configure(text="Paused", text_color=COLOR_MUTED)
            self.btn_toggle_watcher.configure(text="Resume", fg_color="#2e7d32")
        else:
            self.watcher = DBWatcher(self.log_queue)
            self.watcher.start()
            self.lbl_watcher_status.configure(text="Active (1h)", text_color=COLOR_SUCCESS)
            self.btn_toggle_watcher.configure(text="Pause", fg_color="#546e7a")

    def manual_db_check(self):
        if self.watcher:
            self.log_queue.put(("INFO", "🛠️ Manual Check Triggered..."))
            self.watcher.manual_trigger()
        else:
            self.log_queue.put(("WARN", "Watcher is paused."))

    def _stream_output(self, proc, widget):
        """Stream subprocess output with timeout protection."""
        try:
            while proc.poll() is None:
                try:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    text = line.rstrip()
                    if not text:
                        continue
                    level = "INFO"
                    if "ERROR" in text.upper() or "EXCEPTION" in text.upper():
                        level = "ERROR"
                    elif "WARNING" in text.upper():
                        level = "WARN"
                    elif "SUCCESS" in text.upper() or "COMPLETE" in text.upper():
                        level = "SUCCESS"

                    self.append_log(widget, text, level)
                except Exception:
                    break
        except Exception:
            pass
        finally:
            try:
                self.append_log(widget, ">>> Process Exited", "WARN")
            except Exception:
                pass  # Widget may be destroyed

    def _start_process(self, cmd, widget, cwd=None):
        # Use UTF-8 environment for subprocess
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        proc = subprocess.Popen(
            cmd, cwd=cwd or str(BASE_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, encoding='utf-8', errors='replace',
            env=env
        )
        # Register for cleanup on exit
        _register_process(proc)
        threading.Thread(target=self._stream_output, args=(proc, widget), daemon=True).start()
        return proc

    def start_web(self):
        if self.proc_web and self.proc_web.poll() is None: return
        if _is_port_in_use(DASHBOARD_PORT):
            messagebox.showerror("Error", f"Port {DASHBOARD_PORT} is in use.")
            return

        self.btn_web_start.configure(state="disabled")
        self.btn_web_stop.configure(state="normal")
        self.lbl_web_status.configure(text=f"Running ({DASHBOARD_PORT})", text_color=COLOR_SUCCESS)
        self.web_status_bar.configure(fg_color=COLOR_SUCCESS) # Status Bar ON
        self.append_log(self.log_web, ">>> Starting Dashboard...", "INFO")

        cmd = [PY, "-m", "streamlit", "run", str(BASE_DIR / "dashboard" / "app.py"), "--server.address", "0.0.0.0", "--server.port", str(DASHBOARD_PORT), "--server.headless", "true"]
        self.proc_web = self._start_process(cmd, self.log_web)

    def stop_web(self):
        if self.proc_web:
            _unregister_process(self.proc_web)
            _taskkill_tree(self.proc_web.pid)
        self.proc_web = None
        self.btn_web_start.configure(state="normal")
        self.btn_web_stop.configure(state="disabled")
        self.lbl_web_status.configure(text="Stopped", text_color=COLOR_MUTED)
        self.web_status_bar.configure(fg_color=COLOR_MUTED) # Status Bar OFF
        self.append_log(self.log_web, ">>> Stopped.", "WARN")

    def start_api(self):
        if self.proc_api and self.proc_api.poll() is None: return
        if _is_port_in_use(API_PORT):
            messagebox.showerror("Error", f"Port {API_PORT} is in use.")
            return

        self.btn_api_start.configure(state="disabled")
        self.btn_api_stop.configure(state="normal")
        self.lbl_api_status.configure(text=f"Running ({API_PORT})", text_color=COLOR_SUCCESS)
        self.api_status_bar.configure(fg_color=COLOR_SUCCESS) # Status Bar ON
        self.append_log(self.log_api, ">>> Starting API Server...", "INFO")

        cmd = [PY, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", str(API_PORT)]
        self.proc_api = self._start_process(cmd, self.log_api)

    def stop_api(self):
        if self.proc_api:
            _unregister_process(self.proc_api)
            _taskkill_tree(self.proc_api.pid)
        self.proc_api = None
        self.btn_api_start.configure(state="normal")
        self.btn_api_stop.configure(state="disabled")
        self.lbl_api_status.configure(text="Stopped", text_color=COLOR_MUTED)
        self.api_status_bar.configure(fg_color=COLOR_MUTED) # Status Bar OFF
        self.append_log(self.log_api, ">>> Stopped.", "WARN")

    def start_portal(self):
        if self.proc_portal and self.proc_portal.poll() is None:
            return

        self.btn_portal_start.configure(state="disabled")
        self.btn_portal_stop.configure(state="normal")
        self.lbl_portal_status.configure(text="Running", text_color=COLOR_SUCCESS)
        self.portal_status_bar.configure(fg_color=COLOR_SUCCESS)
        self.append_log(self.log_portal, ">>> Starting Portal Automation...", "INFO")

        portal_dir = str(BASE_DIR / "webcloring-pdf")
        cmd = [PY, "main.py", "--auto"]
        self.proc_portal = self._start_process(cmd, self.log_portal, cwd=portal_dir)

    def stop_portal(self):
        if self.proc_portal:
            _unregister_process(self.proc_portal)
            _taskkill_tree(self.proc_portal.pid)
        self.proc_portal = None
        self.btn_portal_start.configure(state="normal")
        self.btn_portal_stop.configure(state="disabled")
        self.lbl_portal_status.configure(text="Stopped", text_color=COLOR_MUTED)
        self.portal_status_bar.configure(fg_color=COLOR_MUTED)
        self.append_log(self.log_portal, ">>> Stopped.", "WARN")

    def open_portal_settings(self):
        """Open portal settings dialog."""
        env_path = BASE_DIR / "webcloring-pdf" / ".env"
        dialog = PortalSettingsDialog(self, env_path)
        self.wait_window(dialog)
        if dialog.result:
            self.append_log(self.log_portal, "⚙️ Settings saved.", "SUCCESS")

    def run_portal_now(self):
        """Run portal automation once (non-blocking)."""
        if self.proc_portal and self.proc_portal.poll() is None:
            self.append_log(self.log_portal, "⚠️ Already running.", "WARN")
            return

        self.btn_portal_start.configure(state="disabled")
        self.btn_portal_stop.configure(state="normal")
        self.lbl_portal_status.configure(text="Running (1-shot)", text_color="#ffb74d")
        self.portal_status_bar.configure(fg_color="#ffb74d")
        self.append_log(self.log_portal, ">>> Running Portal Automation (1-shot)...", "INFO")

        portal_dir = str(BASE_DIR / "webcloring-pdf")
        cmd = [PY, "main.py", "--auto"]
        self.proc_portal = self._start_process(cmd, self.log_portal, cwd=portal_dir)

        # Monitor for completion and reset UI (thread-safe via self.after)
        def _monitor():
            if self.proc_portal:
                self.proc_portal.wait()
            try:
                self.after(0, self._reset_portal_ui)
            except Exception:
                pass  # Widget may be destroyed
        threading.Thread(target=_monitor, daemon=True).start()

    def _reset_portal_ui(self):
        """Reset portal panel to stopped state (main thread only)."""
        self.btn_portal_start.configure(state="normal")
        self.btn_portal_stop.configure(state="disabled")
        self.lbl_portal_status.configure(text="Stopped", text_color=COLOR_MUTED)
        self.portal_status_bar.configure(fg_color=COLOR_MUTED)

    def on_close(self):
        if self.watcher: self.watcher.stop()
        self.stop_web()
        self.stop_api()
        self.stop_portal()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = ServerManager()
    app.mainloop()
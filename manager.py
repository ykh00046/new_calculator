import os
import sys
import threading
import subprocess
import socket
import webbrowser
import time
import queue
import sqlite3
from pathlib import Path
import tkinter as tk
import customtkinter as ctk

# Add current directory to path for shared module import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared import (
    BASE_DIR,
    DB_FILE,
    DASHBOARD_PORT,
    API_PORT,
    DB_TIMEOUT,
)

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
# DB Watcher Logic (Background Thread)
# ==========================================================
class DBWatcher(threading.Thread):
    def __init__(self, log_queue, interval=3600):
        super().__init__()
        self.log_queue = log_queue
        self.interval = interval  # Default 1 hour
        self.running = False
        self.last_mtime = 0
        self.last_size = 0
        
        if DB_FILE.exists():
            self.last_mtime = os.path.getmtime(DB_FILE)
            self.last_size = os.path.getsize(DB_FILE)

    def run(self):
        self.running = True
        self.log_queue.put(("SUCCESS", "✅ DB Watcher Started (Interval: 1h)"))
        
        while self.running:
            try:
                for _ in range(self.interval):
                    if not self.running: break
                    time.sleep(1)
                
                if not self.running: break
                self._check_and_heal()
                
            except Exception as e:
                self.log_queue.put(("ERROR", f"Watcher Error: {e}"))
                time.sleep(60)

    def stop(self):
        self.running = False
        self.log_queue.put(("INFO", "🛑 DB Watcher Stopped"))

    def _check_and_heal(self):
        if not DB_FILE.exists(): return

        current_mtime = os.path.getmtime(DB_FILE)
        current_size = os.path.getsize(DB_FILE)

        if current_mtime != self.last_mtime or current_size != self.last_size:
            self.log_queue.put(("WARN", "🔄 DB Change Detected! Waiting for stabilization..."))
            
            if self._wait_for_stabilization(current_mtime, current_size):
                self.log_queue.put(("INFO", "✅ DB Stabilized. Checking indexes..."))
                self._heal_index()
                self.last_mtime = os.path.getmtime(DB_FILE)
                self.last_size = os.path.getsize(DB_FILE)
            else:
                self.log_queue.put(("WARN", "⚠️ DB unstable. Skip this cycle."))

    def _wait_for_stabilization(self, initial_mtime, initial_size):
        for _ in range(3):
            time.sleep(5)
            if not DB_FILE.exists(): return False
            now_mtime = os.path.getmtime(DB_FILE)
            now_size = os.path.getsize(DB_FILE)
            if now_mtime != initial_mtime or now_size != initial_size: return False
        return True

    def _heal_index(self):
        try:
            conn = sqlite3.connect(f"file:{DB_FILE}?mode=rw", uri=True, timeout=DB_TIMEOUT)
            cursor = conn.cursor()
            cursor.execute("PRAGMA index_list('production_records')")
            indexes = [row[1] for row in cursor.fetchall()]
            
            required_indexes = {
                "idx_production_date": "CREATE INDEX IF NOT EXISTS idx_production_date ON production_records(production_date)",
                "idx_item_code": "CREATE INDEX IF NOT EXISTS idx_item_code ON production_records(item_code)",
                "idx_item_date": "CREATE INDEX IF NOT EXISTS idx_item_date ON production_records(item_code, production_date)",  # v7: 복합 인덱스
            }
            
            restored = []
            for name, sql in required_indexes.items():
                if name not in indexes:
                    cursor.execute(sql)
                    restored.append(name)
            
            if restored:
                conn.commit()
                self.log_queue.put(("SUCCESS", f"♻️ Auto-Healed Indexes: {', '.join(restored)}"))
            else:
                self.log_queue.put(("INFO", "👍 Indexes are healthy."))
            conn.close()
        except Exception as e:
            self.log_queue.put(("ERROR", f"❌ Index Heal Failed: {e}"))

    def manual_trigger(self):
        threading.Thread(target=self._check_and_heal, daemon=True).start()


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
# Manager UI (v2.1 - Enhanced UX)
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
        self.log_queue = queue.Queue()
        self.watcher = None

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=3) # Web/API Panel
        self.grid_rowconfigure(2, weight=1) # DB Panel

        # --- Sections ---
        self._init_header()
        self._init_web_panel()
        self._init_api_panel()
        self._init_db_panel()

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
        self.db_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=(10, 20))
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
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line: break
                text = line.rstrip()
                level = "INFO"
                if "ERROR" in text.upper() or "EXCEPTION" in text.upper(): level = "ERROR"
                elif "WARNING" in text.upper(): level = "WARN"
                elif "SUCCESS" in text.upper() or "COMPLETE" in text.upper(): level = "SUCCESS"
                
                self.append_log(widget, text, level)
        except Exception: pass
        finally:
            self.append_log(widget, ">>> Process Exited", "WARN")

    def _start_process(self, cmd, widget):
        # Use UTF-8 environment for subprocess
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        proc = subprocess.Popen(
            cmd, cwd=str(BASE_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, encoding='utf-8', errors='replace',
            env=env
        )
        threading.Thread(target=self._stream_output, args=(proc, widget), daemon=True).start()
        return proc

    def start_web(self):
        if self.proc_web and self.proc_web.poll() is None: return
        if _is_port_in_use(DASHBOARD_PORT):
            tk.messagebox.showerror("Error", f"Port {DASHBOARD_PORT} is in use.")
            return

        self.btn_web_start.configure(state="disabled")
        self.btn_web_stop.configure(state="normal")
        self.lbl_web_status.configure(text=f"Running ({DASHBOARD_PORT})", text_color=COLOR_SUCCESS)
        self.web_status_bar.configure(fg_color=COLOR_SUCCESS) # Status Bar ON
        self.append_log(self.log_web, ">>> Starting Dashboard...", "INFO")

        cmd = [PY, "-m", "streamlit", "run", str(BASE_DIR / "dashboard" / "app.py"), "--server.address", "0.0.0.0", "--server.port", str(DASHBOARD_PORT), "--server.headless", "true"]
        self.proc_web = self._start_process(cmd, self.log_web)

    def stop_web(self):
        if self.proc_web: _taskkill_tree(self.proc_web.pid)
        self.proc_web = None
        self.btn_web_start.configure(state="normal")
        self.btn_web_stop.configure(state="disabled")
        self.lbl_web_status.configure(text="Stopped", text_color=COLOR_MUTED)
        self.web_status_bar.configure(fg_color=COLOR_MUTED) # Status Bar OFF
        self.append_log(self.log_web, ">>> Stopped.", "WARN")

    def start_api(self):
        if self.proc_api and self.proc_api.poll() is None: return
        if _is_port_in_use(API_PORT):
            tk.messagebox.showerror("Error", f"Port {API_PORT} is in use.")
            return

        self.btn_api_start.configure(state="disabled")
        self.btn_api_stop.configure(state="normal")
        self.lbl_api_status.configure(text=f"Running ({API_PORT})", text_color=COLOR_SUCCESS)
        self.api_status_bar.configure(fg_color=COLOR_SUCCESS) # Status Bar ON
        self.append_log(self.log_api, ">>> Starting API Server...", "INFO")

        cmd = [PY, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", str(API_PORT)]
        self.proc_api = self._start_process(cmd, self.log_api)

    def stop_api(self):
        if self.proc_api: _taskkill_tree(self.proc_api.pid)
        self.proc_api = None
        self.btn_api_start.configure(state="normal")
        self.btn_api_stop.configure(state="disabled")
        self.lbl_api_status.configure(text="Stopped", text_color=COLOR_MUTED)
        self.api_status_bar.configure(fg_color=COLOR_MUTED) # Status Bar OFF
        self.append_log(self.log_api, ">>> Stopped.", "WARN")

    def on_close(self):
        if self.watcher: self.watcher.stop()
        self.stop_web()
        self.stop_api()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = ServerManager()
    app.mainloop()
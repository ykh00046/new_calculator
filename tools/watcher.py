# tools/watcher.py
"""
Production Data Hub - Independent DB Watcher Script

Features (Section 6.3):
- Runs independently from Manager UI
- Monitors DB file changes and auto-heals indexes
- Can be scheduled via Windows Task Scheduler

Usage:
    python tools/watcher.py              # Single check and heal
    python tools/watcher.py --daemon     # Run continuously (1 hour interval)
    python tools/watcher.py --interval 300  # Custom interval (seconds)

Windows Task Scheduler Setup:
    1. Open Task Scheduler
    2. Create Basic Task
    3. Trigger: At startup / Daily / Every 5 minutes
    4. Action: Start a program
       - Program: python.exe (or full path)
       - Arguments: C:\\X\\Server_v1\\tools\\watcher.py
       - Start in: C:\\X\\Server_v1
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import DB_FILE, ARCHIVE_DB_FILE, DATABASE_DIR, DB_TIMEOUT, LOGS_DIR


# ==========================================================
# Configuration
# ==========================================================
STATE_FILE = DATABASE_DIR / ".watcher_state.json"
DEFAULT_INTERVAL = 3600  # 1 hour
STABILIZATION_WAIT = 5  # seconds between stability checks
STABILIZATION_CHECKS = 3

# Required indexes for production_records
REQUIRED_INDEXES = {
    "idx_production_date": "CREATE INDEX IF NOT EXISTS idx_production_date ON production_records(production_date)",
    "idx_item_code": "CREATE INDEX IF NOT EXISTS idx_item_code ON production_records(item_code)",
    "idx_item_date": "CREATE INDEX IF NOT EXISTS idx_item_date ON production_records(item_code, production_date)",  # v7: 복합 인덱스
}


# ==========================================================
# Logging
# ==========================================================
LOG_FILE = LOGS_DIR / "watcher.log"


def log(level: str, msg: str):
    """Log to both stdout and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level:5}] {msg}"
    print(log_line)

    # Also write to log file
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception:
        pass  # Don't fail if logging fails


# ==========================================================
# State Management
# ==========================================================
def load_state() -> dict:
    """Load last known state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"live_mtime": 0, "live_size": 0, "archive_mtime": 0, "archive_size": 0}


def save_state(state: dict):
    """Save current state to file."""
    try:
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        log("WARN", f"Failed to save state: {e}")


def get_file_state(path: Path) -> tuple[float, int]:
    """Get mtime and size of a file. Returns (0, 0) if not exists."""
    if not path.exists():
        return 0, 0
    try:
        return os.path.getmtime(path), os.path.getsize(path)
    except Exception:
        return 0, 0


# ==========================================================
# Core Functions
# ==========================================================
def wait_for_stabilization(db_path: Path) -> bool:
    """
    Wait until the DB file's mtime stops changing.
    Returns True if stabilized.
    """
    if not db_path.exists():
        return False

    last_mtime, last_size = get_file_state(db_path)

    for _ in range(STABILIZATION_CHECKS):
        time.sleep(STABILIZATION_WAIT)

        current_mtime, current_size = get_file_state(db_path)

        if current_mtime != last_mtime or current_size != last_size:
            log("INFO", f"DB still changing, waiting... ({db_path.name})")
            last_mtime, last_size = current_mtime, current_size
            # Restart the wait
            return wait_for_stabilization(db_path)

    return True


def check_and_heal_indexes(db_path: Path, is_archive: bool = False) -> dict:
    """
    Check and restore missing indexes on a database.
    Returns dict with results.
    """
    result = {
        "db": db_path.name,
        "checked": False,
        "healed": [],
        "error": None
    }

    if not db_path.exists():
        result["error"] = "File not found"
        return result

    try:
        # Connect in read-write mode for potential index creation
        conn = sqlite3.connect(str(db_path), timeout=DB_TIMEOUT)
        cursor = conn.cursor()

        # Get existing indexes
        cursor.execute("PRAGMA index_list('production_records')")
        existing = {row[1] for row in cursor.fetchall()}

        result["checked"] = True

        # Check and create missing indexes
        for name, sql in REQUIRED_INDEXES.items():
            if name not in existing:
                log("INFO", f"Creating missing index: {name} on {db_path.name}")
                cursor.execute(sql)
                result["healed"].append(name)

        if result["healed"]:
            conn.commit()
            log("INFO", f"Healed {len(result['healed'])} indexes on {db_path.name}")
        else:
            log("INFO", f"All indexes OK on {db_path.name}")

        conn.close()

    except sqlite3.Error as e:
        result["error"] = str(e)
        log("ERROR", f"SQLite error on {db_path.name}: {e}")

    except Exception as e:
        result["error"] = str(e)
        log("ERROR", f"Error checking {db_path.name}: {e}")

    return result


def run_check() -> dict:
    """
    Run a single check cycle.
    Returns summary of actions taken.
    """
    log("INFO", "=" * 50)
    log("INFO", "Starting DB check cycle")
    log("INFO", "=" * 50)

    state = load_state()
    summary = {
        "timestamp": datetime.now().isoformat(),
        "live": {"changed": False, "result": None},
        "archive": {"changed": False, "result": None}
    }

    # Check Live DB
    live_mtime, live_size = get_file_state(DB_FILE)

    if DB_FILE.exists():
        if live_mtime != state["live_mtime"] or live_size != state["live_size"]:
            log("INFO", f"Live DB changed: mtime={live_mtime}, size={live_size}")
            summary["live"]["changed"] = True

            if wait_for_stabilization(DB_FILE):
                summary["live"]["result"] = check_and_heal_indexes(DB_FILE)
                # Update state with new values
                live_mtime, live_size = get_file_state(DB_FILE)
            else:
                log("WARN", "Live DB not stable, skipping index check")
        else:
            log("INFO", "Live DB unchanged")
            # Still do a periodic check even if unchanged
            summary["live"]["result"] = check_and_heal_indexes(DB_FILE)

    # Check Archive DB
    archive_mtime, archive_size = get_file_state(ARCHIVE_DB_FILE)

    if ARCHIVE_DB_FILE.exists():
        if archive_mtime != state["archive_mtime"] or archive_size != state["archive_size"]:
            log("INFO", f"Archive DB changed: mtime={archive_mtime}, size={archive_size}")
            summary["archive"]["changed"] = True

            if wait_for_stabilization(ARCHIVE_DB_FILE):
                summary["archive"]["result"] = check_and_heal_indexes(ARCHIVE_DB_FILE, is_archive=True)
                archive_mtime, archive_size = get_file_state(ARCHIVE_DB_FILE)
            else:
                log("WARN", "Archive DB not stable, skipping index check")
        else:
            log("INFO", "Archive DB unchanged")
    else:
        log("INFO", "Archive DB not found (may not exist yet)")

    # Save updated state
    save_state({
        "live_mtime": live_mtime,
        "live_size": live_size,
        "archive_mtime": archive_mtime,
        "archive_size": archive_size
    })

    log("INFO", "=" * 50)
    log("INFO", "Check cycle complete")
    log("INFO", "=" * 50)

    return summary


def run_daemon(interval: int):
    """
    Run continuously with specified interval.
    """
    log("INFO", f"Starting daemon mode with interval={interval}s")

    while True:
        try:
            run_check()
        except Exception as e:
            log("ERROR", f"Check cycle failed: {e}")

        log("INFO", f"Next check in {interval} seconds...")

        # Sleep in small increments for graceful shutdown
        for _ in range(interval):
            time.sleep(1)


# ==========================================================
# Main
# ==========================================================
def main():
    parser = argparse.ArgumentParser(description="Production Data Hub - DB Watcher")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})")
    args = parser.parse_args()

    log("INFO", "Production Data Hub - DB Watcher")
    log("INFO", f"Live DB: {DB_FILE}")
    log("INFO", f"Archive DB: {ARCHIVE_DB_FILE}")

    if args.daemon:
        run_daemon(args.interval)
    else:
        summary = run_check()

        # Print summary
        print("\n--- Summary ---")
        print(json.dumps(summary, indent=2, default=str))

        # Return non-zero if any errors
        if summary["live"]["result"] and summary["live"]["result"].get("error"):
            return 1
        if summary["archive"]["result"] and summary["archive"]["result"].get("error"):
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

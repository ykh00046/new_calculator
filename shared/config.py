# shared/config.py
"""
Production Data Hub - Configuration Constants

All hardcoded values are centralized here for maintainability.
Environment variables can override default values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ==========================================================
# Paths
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"

DB_FILE = DATABASE_DIR / "production_analysis.db"
ARCHIVE_DB_FILE = DATABASE_DIR / "archive_2025.db"

# ==========================================================
# Archive Policy
# ==========================================================
# Archive DB contains data BEFORE this year (i.e., 2025 and earlier)
# Live DB contains data FROM this year onwards (i.e., 2026+)
ARCHIVE_CUTOFF_YEAR = 2026
ARCHIVE_CUTOFF_DATE = f"{ARCHIVE_CUTOFF_YEAR}-01-01"

# ==========================================================
# Server Ports (can be overridden via .env)
# ==========================================================
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))
API_PORT = int(os.getenv("API_PORT", 8000))

# ==========================================================
# Database Connection
# ==========================================================
DB_TIMEOUT = 10.0  # seconds
SLOW_QUERY_THRESHOLD_MS = 500  # Log WARNING for queries exceeding this

# ==========================================================
# Logging
# ==========================================================
LOG_FILE = LOGS_DIR / "app.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==========================================================
# Date Handling Policy (6.4)
# ==========================================================
# - SQL filters operate on Day-level only
# - Monthly aggregation uses substr(production_date, 1, 7)
# - API input date_from/date_to normalized to 'YYYY-MM-DD'
DATE_FORMAT = "%Y-%m-%d"

# shared/__init__.py
"""
Production Data Hub - Shared Module

This module provides common utilities used across the application:
- config: Application constants and settings
- database: DB connection, routing, and query utilities
- logging_config: Centralized logging configuration
"""

from .config import (
    BASE_DIR,
    DATABASE_DIR,
    DB_FILE,
    ARCHIVE_DB_FILE,
    ARCHIVE_CUTOFF_YEAR,
    ARCHIVE_CUTOFF_DATE,
    DASHBOARD_PORT,
    API_PORT,
    DB_TIMEOUT,
)

from .database import (
    DBTargets,
    DBRouter,
)

from .logging_config import setup_logging, get_logger
from .cache import api_cache, get_db_version, clear_api_cache, get_cache_stats

__all__ = [
    # config
    "BASE_DIR",
    "DATABASE_DIR",
    "DB_FILE",
    "ARCHIVE_DB_FILE",
    "ARCHIVE_CUTOFF_YEAR",
    "ARCHIVE_CUTOFF_DATE",
    "DASHBOARD_PORT",
    "API_PORT",
    "DB_TIMEOUT",
    # database
    "DBTargets",
    "DBRouter",
    # logging
    "setup_logging",
    "get_logger",
    # cache
    "api_cache",
    "get_db_version",
    "clear_api_cache",
    "get_cache_stats",
]

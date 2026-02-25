# shared/__init__.py
"""
Production Data Hub - Shared Module

This module provides common utilities used across the application:
- config: Application constants and settings
- database: DB connection, routing, and query utilities
- logging_config: Centralized logging configuration
- rate_limiter: IP-based rate limiting system
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
    RATE_LIMIT_CHAT,
    RATE_LIMIT_API,
    RATE_LIMIT_WINDOW,
)

from .database import (
    DBTargets,
    DBRouter,
)

from .logging_config import setup_logging, get_logger
from .cache import api_cache, get_db_version, clear_api_cache, get_cache_stats
from .rate_limiter import RateLimiter, chat_rate_limiter, api_rate_limiter
from .validators import (
    validate_date_format,
    validate_date_range,
    validate_date_range_exclusive,
    validate_length,
)

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
    "RATE_LIMIT_CHAT",
    "RATE_LIMIT_API",
    "RATE_LIMIT_WINDOW",
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
    # rate limiter
    "RateLimiter",
    "chat_rate_limiter",
    "api_rate_limiter",
    # validators
    "validate_date_format",
    "validate_date_range",
    "validate_date_range_exclusive",
    "validate_length",
]

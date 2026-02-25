# shared/cache.py
"""
Production Data Hub - API Cache with DB mtime invalidation

v7 Performance Improvement:
- TTLCache with db_mtime based cache key
- Automatic invalidation when DB file changes

v8 Thread Safety:
- Thread-safe cache operations with threading.Lock
"""

from __future__ import annotations

import os
import hashlib
import threading
from functools import wraps
from typing import Any, Callable

from cachetools import TTLCache

from .config import DB_FILE, ARCHIVE_DB_FILE


# ==========================================================
# DB Version (mtime-based)
# ==========================================================
_db_version_cache: str | None = None
_db_version_lock = threading.Lock()
_db_version_timestamp: float = 0
_DB_VERSION_CACHE_TTL = 1.0  # Cache mtime for 1 second


def get_db_version() -> str:
    """
    Get combined mtime of Live + Archive DB as version string.
    Used as cache key component for automatic invalidation.

    v8: Caches mtime for 1 second to reduce filesystem calls.
    """
    global _db_version_cache, _db_version_timestamp

    current_time = time.time() if (time := __import__('time')).time() else 0

    # Return cached version if still valid
    with _db_version_lock:
        if _db_version_cache is not None and (current_time - _db_version_timestamp) < _DB_VERSION_CACHE_TTL:
            return _db_version_cache

        try:
            live_mtime = os.path.getmtime(DB_FILE) if DB_FILE.exists() else 0
            archive_mtime = os.path.getmtime(ARCHIVE_DB_FILE) if ARCHIVE_DB_FILE.exists() else 0
            # Combine and truncate to reduce key length
            combined = f"{live_mtime:.0f}_{archive_mtime:.0f}"
            _db_version_cache = combined
            _db_version_timestamp = current_time
            return combined
        except Exception:
            return "0_0"


# ==========================================================
# Cache Instance (Thread-safe)
# ==========================================================
# maxsize: 최대 캐시 항목 수
# ttl: 초 단위 TTL (mtime이 같아도 이 시간 후 만료)
_api_cache = TTLCache(maxsize=200, ttl=300)  # 5분 TTL, 최대 200개 항목
_cache_lock = threading.Lock()


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key including db_version."""
    db_ver = get_db_version()
    key_data = f"{prefix}:{db_ver}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()


# ==========================================================
# Cache Decorator (Thread-safe)
# ==========================================================
def api_cache(prefix: str, ttl: int | None = None):
    """
    Decorator for caching API endpoint results.

    Args:
        prefix: Cache key prefix (usually endpoint name)
        ttl: Optional TTL override (not currently used, reserved for future)

    Usage:
        @api_cache("items")
        def list_items(q: str = None, limit: int = 200):
            ...

    Note:
        - Cache key includes db_mtime, so DB changes auto-invalidate
        - Cached results are dicts/lists (JSON-serializable)
        - Thread-safe with internal locking
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _make_cache_key(prefix, *args, **kwargs)

            # Thread-safe cache check
            with _cache_lock:
                if cache_key in _api_cache:
                    return _api_cache[cache_key]

            # Execute outside lock (may be slow)
            result = func(*args, **kwargs)

            # Thread-safe cache store
            with _cache_lock:
                _api_cache[cache_key] = result

            return result

        return wrapper
    return decorator


def clear_api_cache():
    """Clear all API cache entries (thread-safe)."""
    with _cache_lock:
        _api_cache.clear()


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring (thread-safe)."""
    with _cache_lock:
        return {
            "size": len(_api_cache),
            "maxsize": _api_cache.maxsize,
            "ttl": _api_cache.ttl,
            "db_version": get_db_version(),
        }

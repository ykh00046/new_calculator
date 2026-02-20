# shared/rate_limiter.py
"""
Production Data Hub - Rate Limiting System

IP-based sliding window rate limiting implementation.
Thread-safe with automatic cleanup of expired entries.

Features:
- Sliding window algorithm for accurate rate limiting
- Thread-safe with RLock
- Automatic cleanup of expired entries
- Retry-After calculation for 429 responses
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from .config import RATE_LIMIT_WINDOW


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window algorithm.

    Each IP address maintains a list of request timestamps.
    Requests older than the window are automatically cleaned up.

    Usage:
        limiter = RateLimiter(max_requests=20, window_seconds=60)

        if limiter.is_allowed("192.168.1.1"):
            # Process request
            pass
        else:
            # Return 429 with retry_after
            retry = limiter.retry_after("192.168.1.1")
    """

    def __init__(self, max_requests: int, window_seconds: int = RATE_LIMIT_WINDOW):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds (default: from config)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # IP -> List of timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def is_allowed(self, ip: str) -> bool:
        """
        Check if request from IP is allowed and record the request.

        This method both checks AND records the request atomically.

        Args:
            ip: Client IP address

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            # Remove expired timestamps (sliding window cleanup)
            self._requests[ip] = [
                ts for ts in self._requests[ip]
                if ts > cutoff_time
            ]

            # Check if under limit
            if len(self._requests[ip]) < self.max_requests:
                # Record this request
                self._requests[ip].append(current_time)
                return True

            return False

    def remaining(self, ip: str) -> int:
        """
        Get remaining requests for IP in current window.

        Does NOT record a request - just checks current state.

        Args:
            ip: Client IP address

        Returns:
            Number of requests remaining (>= 0)
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            # Count valid requests in window
            valid_count = sum(
                1 for ts in self._requests[ip]
                if ts > cutoff_time
            )

            return max(0, self.max_requests - valid_count)

    def retry_after(self, ip: str) -> int:
        """
        Calculate seconds until oldest request in window expires.

        Used for Retry-After header in 429 responses.

        Args:
            ip: Client IP address

        Returns:
            Seconds to wait, or 0 if no requests in window
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            # Get valid timestamps
            valid_timestamps = [
                ts for ts in self._requests[ip]
                if ts > cutoff_time
            ]

            if not valid_timestamps:
                return 0

            # Oldest timestamp determines when a slot frees up
            oldest = min(valid_timestamps)
            retry_at = oldest + self.window_seconds
            wait_seconds = max(1, int(retry_at - current_time) + 1)

            return wait_seconds

    def cleanup(self, max_ips: int = 10000) -> int:
        """
        Remove expired entries to free memory.

        Call periodically (e.g., every 100 requests) to prevent memory leak.

        Args:
            max_ips: Maximum IPs to check (prevent long cleanup)

        Returns:
            Number of IPs removed
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            removed = 0
            ips_to_remove = []

            for ip, timestamps in self._requests.items():
                if len(timestamps) > max_ips:
                    # Safety: stop if too many IPs
                    break

                # Check if all timestamps expired
                if all(ts <= cutoff_time for ts in timestamps):
                    ips_to_remove.append(ip)

            for ip in ips_to_remove:
                del self._requests[ip]
                removed += 1

            return removed

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.

        Returns:
            Dict with total_ips, total_requests, config
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            total_requests = 0
            active_ips = 0

            for ip, timestamps in self._requests.items():
                valid = [ts for ts in timestamps if ts > cutoff_time]
                if valid:
                    active_ips += 1
                    total_requests += len(valid)

            return {
                "active_ips": active_ips,
                "total_tracked_requests": total_requests,
                "max_requests_per_window": self.max_requests,
                "window_seconds": self.window_seconds,
            }


# ==========================================================
# Global Rate Limiter Instances
# ==========================================================
# Chat endpoint: 20 requests per minute (more restrictive)
chat_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)

# General API: 60 requests per minute
api_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)

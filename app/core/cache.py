"""
TTL (Time-To-Live) Cache for prediction results.

Prevents redundant LLM calls and web searches for the same matchup
within a configurable time window. Thread-safe implementation.
"""
import time
import threading
import hashlib
import json
from typing import Any, Optional

from app.core.logger import get_logger

logger = get_logger("cache")


class TTLCache:
    """Thread-safe in-memory cache with per-entry TTL expiration."""

    def __init__(self, default_ttl: int = 600):
        """
        Args:
            default_ttl: Default time-to-live in seconds (default: 10 minutes).
        """
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl

    @staticmethod
    def _make_key(*args, **kwargs) -> str:
        """Generate a deterministic cache key from arguments."""
        raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value if it exists and hasn't expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.time() > entry["expires_at"]:
                del self._store[key]
                logger.debug(f"Cache expired: {key[:8]}...")
                return None
            logger.debug(f"Cache hit: {key[:8]}...")
            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value with TTL."""
        ttl = ttl or self.default_ttl
        with self._lock:
            self._store[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
            }
            logger.debug(f"Cache set: {key[:8]}... (TTL={ttl}s)")

    def invalidate(self, key: str) -> None:
        """Remove a specific entry."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._store.clear()
            logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        now = time.time()
        removed = 0
        with self._lock:
            expired_keys = [
                k for k, v in self._store.items() if now > v["expires_at"]
            ]
            for k in expired_keys:
                del self._store[k]
                removed += 1
        if removed:
            logger.info(f"Cleaned up {removed} expired cache entries")
        return removed

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)


# Global cache instances
prediction_cache = TTLCache(default_ttl=600)    # 10 min for full predictions
search_cache = TTLCache(default_ttl=300)        # 5 min for web searches

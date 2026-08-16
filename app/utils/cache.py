"""Small TTL cache for reference data.

DOCUMENT_TYPE, REMEDY_TYPE, ROLE, PROVINCIAL_OFFICE and MINERAL are read on
nearly every request and change rarely, so they are worth caching. Nothing
assessment- or payment-related is ever cached.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

DEFAULT_TTL_SECONDS = 300


class TTLCache:
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.ttl = ttl_seconds
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires, value = entry
            if expires < time.monotonic():
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + (ttl_seconds or self.ttl), value)

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl_seconds: int | None = None) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = factory()
        self.set(key, value, ttl_seconds)
        return value

    def invalidate(self, prefix: str | None = None) -> None:
        with self._lock:
            if prefix is None:
                self._data.clear()
            else:
                for key in [k for k in self._data if k.startswith(prefix)]:
                    self._data.pop(key, None)


reference_cache = TTLCache()

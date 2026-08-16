"""Token-bucket store backing the rate limiter.

In-process and thread-safe. With more than one uvicorn worker, swap in a
Redis-backed store — `hit(key, rate_per_minute, burst)` is the only method a
replacement has to implement.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    updated: float


class MemoryBucketStore:
    def __init__(self) -> None:
        self._buckets: dict[str, Bucket] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, rate_per_minute: int, burst: int) -> tuple[bool, float, int]:
        """Consume one token. Returns (allowed, retry_after_seconds, remaining)."""
        capacity = float(rate_per_minute + burst)
        refill_per_sec = rate_per_minute / 60.0
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = Bucket(tokens=capacity, updated=now)
                self._buckets[key] = bucket
            bucket.tokens = min(capacity, bucket.tokens + (now - bucket.updated) * refill_per_sec)
            bucket.updated = now
            if bucket.tokens < 1.0:
                return False, (1.0 - bucket.tokens) / refill_per_sec, 0
            bucket.tokens -= 1.0
            return True, 0.0, int(bucket.tokens)

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            self._buckets.pop(key, None) if key else self._buckets.clear()


store = MemoryBucketStore()

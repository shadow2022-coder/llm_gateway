from __future__ import annotations

import threading
import time

import redis

from app.config import Settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[float, int]] = {}

    def allow(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            window_start, count = self._windows.get(key, (now, 0))
            if now - window_start >= window_seconds:
                window_start, count = now, 0
            count += 1
            self._windows[key] = (window_start, count)
            if count > limit:
                retry_after = max(1, int(window_seconds - (now - window_start)))
                return False, retry_after
            return True, 0

    def clear(self) -> None:
        with self._lock:
            self._windows.clear()


class RedisRateLimiter:
    def __init__(self, redis_url: str) -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._client.ping()

    def allow(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        counter_key = f"rate_limit:{key}"
        current_value = self._client.incr(counter_key)
        if current_value == 1:
            self._client.expire(counter_key, window_seconds)
        if current_value > limit:
            ttl = self._client.ttl(counter_key)
            return False, max(1, ttl)
        return True, 0


_rate_limiter: InMemoryRateLimiter | RedisRateLimiter | None = None
_rate_limiter_key: str | None = None


def get_rate_limiter(settings: Settings):
    global _rate_limiter, _rate_limiter_key

    limiter_key = settings.redis_url or "memory"
    if _rate_limiter is not None and limiter_key == _rate_limiter_key:
        return _rate_limiter

    if settings.redis_url:
        try:
            _rate_limiter = RedisRateLimiter(settings.redis_url)
            _rate_limiter_key = settings.redis_url
            return _rate_limiter
        except Exception:
            pass

    if not isinstance(_rate_limiter, InMemoryRateLimiter) or limiter_key != _rate_limiter_key:
        _rate_limiter = InMemoryRateLimiter()
        _rate_limiter_key = limiter_key
    return _rate_limiter


def reset_rate_limiter() -> None:
    global _rate_limiter, _rate_limiter_key

    if isinstance(_rate_limiter, InMemoryRateLimiter):
        _rate_limiter.clear()
    _rate_limiter = None
    _rate_limiter_key = None

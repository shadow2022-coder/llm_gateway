from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any

import redis

from app.config import Settings


class InMemoryTTLCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            cached = self._data.get(key)
            if cached is None:
                return None
            expires_at, value = cached
            if expires_at < now:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        with self._lock:
            self._data[key] = (time.time() + ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


class RedisTTLCache:
    def __init__(self, redis_url: str) -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._client.ping()

    def get(self, key: str) -> dict[str, Any] | None:
        payload = self._client.get(key)
        return None if payload is None else json.loads(payload)

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self._client.setex(key, ttl_seconds, json.dumps(value))


_cache_backend: InMemoryTTLCache | RedisTTLCache | None = None
_cache_backend_key: str | None = None


def build_cache_key(model: str, prompt: str) -> str:
    digest = hashlib.sha256(json.dumps({"model": model, "prompt": prompt}, sort_keys=True).encode("utf-8")).hexdigest()
    return f"chat:{digest}"


def get_cache_backend(settings: Settings):
    global _cache_backend, _cache_backend_key

    backend_key = settings.redis_url or "memory"
    if _cache_backend is not None and backend_key == _cache_backend_key:
        return _cache_backend

    if settings.redis_url:
        try:
            _cache_backend = RedisTTLCache(settings.redis_url)
            _cache_backend_key = settings.redis_url
            return _cache_backend
        except Exception:
            pass

    if not isinstance(_cache_backend, InMemoryTTLCache) or backend_key != _cache_backend_key:
        _cache_backend = InMemoryTTLCache()
        _cache_backend_key = backend_key
    return _cache_backend


def reset_cache_backend() -> None:
    global _cache_backend, _cache_backend_key

    if isinstance(_cache_backend, InMemoryTTLCache):
        _cache_backend.clear()
    _cache_backend = None
    _cache_backend_key = None

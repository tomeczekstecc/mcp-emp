"""Słowniki TTL cache — in-process cache for task types and tags.

get_or_load(key, loader, ttl_seconds) returns cached data or calls loader.
Cache is a module-level singleton initialised in server.py lifespan.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

_store: dict[str, tuple[object, float]] = {}
_lock = asyncio.Lock()


async def get_or_load[T](
    key: str,
    loader: Callable[[], Awaitable[T]],
    ttl_seconds: float,
) -> T:
    """Return cached *key* value or call *loader* and cache the result."""
    now = time.monotonic()
    if key in _store:
        value, expires_at = _store[key]
        if now < expires_at:
            return value  # type: ignore[return-value]
    async with _lock:
        # Double-checked: another coroutine may have filled it while we waited
        if key in _store:
            value, expires_at = _store[key]
            if now < expires_at:
                return value  # type: ignore[return-value]
        result = await loader()
        _store[key] = (result, now + ttl_seconds)
        return result


def invalidate(key: str | None = None) -> None:
    """Evict *key* (or the entire cache when key is None)."""
    if key is None:
        _store.clear()
    else:
        _store.pop(key, None)

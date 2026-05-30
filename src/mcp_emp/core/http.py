"""Shared httpx.AsyncClient — singleton initialised in server lifespan.

Domain client modules call get_client() to obtain the process-wide client.
The base URL and bearer token injection are configured during lifespan startup.
"""

from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Return the process-wide httpx.AsyncClient.

    Raises RuntimeError if called before lifespan has started.
    """
    if _client is None:
        raise RuntimeError("httpx client has not been initialised (lifespan not started)")
    return _client


def _set_client(client: httpx.AsyncClient) -> None:
    """Set the singleton — called from lifespan only (and tests)."""
    global _client
    _client = client


async def create_client(base_url: str) -> httpx.AsyncClient:
    """Create and return a new AsyncClient with EMP base URL."""
    return httpx.AsyncClient(base_url=base_url, timeout=30.0, follow_redirects=True)

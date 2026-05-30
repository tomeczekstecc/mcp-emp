"""Keycloak authentication — Resource Owner Password grant.

KeycloakAuth holds the current token, refreshes it under an asyncio lock
so N concurrent callers only trigger one refresh.  Implemented in M1.
"""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)

_auth: KeycloakAuth | None = None


class KeycloakAuth:
    """Token holder with locked refresh logic."""

    def __init__(
        self,
        base_url: str,
        realm: str,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._realm = realm
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if self._access_token and time.monotonic() < self._expires_at - 30:
            return self._access_token
        async with self._lock:
            # Double-checked
            if self._access_token and time.monotonic() < self._expires_at - 30:
                return self._access_token
            await self._do_login()
            assert self._access_token is not None
            return self._access_token

    async def _do_login(self) -> None:
        """Perform the ROPC token request against Keycloak."""
        url = f"{self._base_url}/realms/{self._realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": self._client_id,
            "username": self._username,
            "password": self._password,
        }
        if self._client_secret:
            data["client_secret"] = self._client_secret
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=data)
        if resp.status_code != 200:
            from mcp_emp.core.errors import AuthMisconfigured  # noqa: PLC0415

            raise AuthMisconfigured(
                f"Keycloak login failed: {resp.status_code} {resp.text[:200]}"
            )
        body = resp.json()
        self._access_token = body["access_token"]
        self._refresh_token = body.get("refresh_token")
        expires_in: int = body.get("expires_in", 300)
        self._expires_at = time.monotonic() + expires_in
        logger.debug("KC token acquired, expires_in=%d", expires_in)


def get_auth() -> KeycloakAuth:
    """Return the process-wide KeycloakAuth singleton."""
    if _auth is None:
        raise RuntimeError("KeycloakAuth has not been initialised (lifespan not started)")
    return _auth


def _set_auth(auth: KeycloakAuth) -> None:
    """Set the singleton — called from lifespan only (and tests)."""
    global _auth
    _auth = auth

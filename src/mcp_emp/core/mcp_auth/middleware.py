"""HTTP auth middleware — checks Authorization: Bearer <api_key> header."""

from __future__ import annotations

import sqlite3

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from mcp_emp.core.mcp_auth.db import verify_key

_OPEN_PATHS = {"/healthz"}   # never require auth


class ApiKeyMiddleware:
    """Starlette ASGI middleware that validates Bearer API keys."""

    def __init__(self, app: ASGIApp, db_conn: sqlite3.Connection) -> None:
        self._app = app
        self._conn = db_conn

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path not in _OPEN_PATHS:
                request = Request(scope, receive)
                auth = request.headers.get("Authorization", "")
                if not auth.startswith("Bearer "):
                    await _deny(scope, receive, send, "Missing Bearer token")
                    return
                key = auth[len("Bearer "):]
                user = verify_key(self._conn, key)
                if user is None:
                    await _deny(scope, receive, send, "Invalid or revoked API key")
                    return
                scope["mcp_auth_user"] = user
        await self._app(scope, receive, send)


async def _deny(scope: Scope, receive: Receive, send: Send, msg: str) -> None:
    response = JSONResponse(
        {"error": "Unauthorized", "detail": msg},
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )
    await response(scope, receive, send)

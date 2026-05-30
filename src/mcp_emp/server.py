"""FastMCP server: lifespan, tool registration, transport dispatch."""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.auth import KeycloakAuth, _set_auth
from mcp_emp.core.config import get_settings
from mcp_emp.core.errors import AuthMisconfigured
from mcp_emp.core.health import HealthStatus, check_health
from mcp_emp.core.http import _set_client, create_client
from mcp_emp.core.identity import _set_identity, parse_identity
from mcp_emp.core.logging import setup_logging
from mcp_emp.core.modes import readable

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Initialise shared resources on startup; tear them down on shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)

    # ── Keycloak auth ────────────────────────────────────────────────────────
    auth = KeycloakAuth(
        base_url=settings.kc_base_url,
        realm=settings.kc_realm,
        client_id=settings.kc_client_id,
        client_secret=settings.kc_client_secret.get_secret_value(),
        username=settings.kc_username,
        password=settings.kc_password.get_secret_value(),
    )
    try:
        token = await auth.get_token()
    except AuthMisconfigured as exc:
        logger.error("Startup failed (AUTH_MISCONFIGURED): %s", exc.message)
        sys.exit(77)
    _set_auth(auth)

    # ── Identity ─────────────────────────────────────────────────────────────
    identity = parse_identity(token, settings.kc_realm)
    _set_identity(identity)
    logger.info("Authenticated as %s roles=%s", identity.username, identity.roles)

    # ── EMP HTTP client ───────────────────────────────────────────────────────
    client = await create_client(settings.api_base_url)
    _set_client(client)

    # ── EMP startup health check (WARN only; non-fatal) ──────────────────────
    try:
        resp = await client.get(
            "",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        logger.info("EMP API reachable at %s", settings.api_base_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("EMP API unreachable at startup: %s", exc)

    logger.info(
        "mcp-emp ready, transport=%s read_only=%s",
        settings.transport,
        settings.read_only,
    )

    yield

    # ── Teardown (reverse order) ──────────────────────────────────────────────
    await client.aclose()
    logger.info("mcp-emp shutdown complete")


def build_server() -> FastMCP:
    """Construct and return the configured FastMCP instance."""
    settings = get_settings()
    server = FastMCP(
        "mcp-emp",
        lifespan=lifespan,
        host=settings.sse_host,
        port=settings.sse_port,
    )

    @server.tool()
    @readable
    async def health_check() -> HealthStatus:
        """Check EMP API reachability and Keycloak auth status.

        Returns the reachability of the EMP backend, whether the current
        Keycloak token is still valid, and the authenticated user's identity.

        Call this to confirm the server is configured correctly before using
        other tools.
        """
        return await check_health()

    # M2: slowniki.tools.register(server)
    # M3: rejestr read tools
    # M4-M6: rejestr write tools

    return server


async def main() -> None:
    """Async entry point — dispatches to the configured transport."""
    settings = get_settings()
    server = build_server()
    if settings.transport == "http":
        await server.run_streamable_http_async()
    else:
        await server.run_stdio_async()

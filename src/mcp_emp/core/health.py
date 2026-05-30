"""Health check types and logic — used by the health_check MCP tool."""

from __future__ import annotations

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class UserInfo(BaseModel):
    """Identifying information for the currently authenticated user."""

    username: str
    display_name: str
    roles: list[str]
    unit: str
    team: str


class HealthStatus(BaseModel):
    """Result of the health_check MCP tool."""

    emp_api: str  # "reachable" | "unreachable"
    auth: str  # "valid" | "expired"
    user: UserInfo


async def check_health() -> HealthStatus:
    """Probe the EMP API and verify the KC token is still valid."""
    from mcp_emp.core.auth import get_auth  # noqa: PLC0415
    from mcp_emp.core.http import get_client  # noqa: PLC0415
    from mcp_emp.core.identity import get_identity  # noqa: PLC0415

    identity = get_identity()

    # Attempt to obtain a fresh token — verifies KC is still reachable
    auth_status = "valid"
    token: str | None = None
    try:
        token = await get_auth().get_token()
    except Exception as exc:  # noqa: BLE001
        logger.warning("KC token refresh failed during health check: %s", exc)
        auth_status = "expired"

    # Ping the EMP API
    emp_status = "reachable"
    if token:
        try:
            resp = await get_client().get(
                "",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("EMP /health-check failed: %s", exc)
            emp_status = "unreachable"
    else:
        emp_status = "unreachable"

    return HealthStatus(
        emp_api=emp_status,
        auth=auth_status,
        user=UserInfo(
            username=identity.username,
            display_name=identity.display_name,
            roles=identity.roles,
            unit=identity.unit,
            team=identity.team,
        ),
    )

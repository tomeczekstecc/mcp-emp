"""Integration tests for core.health.check_health()."""

from __future__ import annotations

import httpx
import respx

from mcp_emp.core.health import check_health

EMP_BASE = "http://localhost:480/api"


@respx.mock
async def test_check_health_emp_reachable(
    fake_settings,  # noqa: ANN001
    fake_identity,  # noqa: ANN001
    fake_auth,  # noqa: ANN001
    fake_http_client,  # noqa: ANN001
) -> None:
    """EMP / returns 200 → emp_api='reachable', auth='valid'."""
    respx.get(f"{EMP_BASE}/").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    result = await check_health()

    assert result.emp_api == "reachable"
    assert result.auth == "valid"
    assert result.user.username == "tkowalski"
    assert "pracownik" in result.user.roles


@respx.mock
async def test_check_health_emp_unreachable(
    fake_settings,  # noqa: ANN001
    fake_identity,  # noqa: ANN001
    fake_auth,  # noqa: ANN001
    fake_http_client,  # noqa: ANN001
) -> None:
    """EMP / times out → emp_api='unreachable', auth='valid'."""
    respx.get(f"{EMP_BASE}/").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    result = await check_health()

    assert result.emp_api == "unreachable"
    assert result.auth == "valid"


@respx.mock
async def test_check_health_auth_expired(
    fake_settings,  # noqa: ANN001
    fake_identity,  # noqa: ANN001
    failing_auth,  # noqa: ANN001
    fake_http_client,  # noqa: ANN001
) -> None:
    """KC token refresh fails → auth='expired', emp_api='unreachable'."""
    result = await check_health()

    assert result.auth == "expired"
    assert result.emp_api == "unreachable"


@respx.mock
async def test_check_health_emp_returns_500(
    fake_settings,  # noqa: ANN001
    fake_identity,  # noqa: ANN001
    fake_auth,  # noqa: ANN001
    fake_http_client,  # noqa: ANN001
) -> None:
    """EMP returns 500 → emp_api='unreachable'."""
    respx.get(f"{EMP_BASE}/").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    result = await check_health()

    assert result.emp_api == "unreachable"
    assert result.auth == "valid"

"""Tests for core.auth — KeycloakAuth token lifecycle and concurrency."""

from __future__ import annotations

import asyncio
import time

import pytest

from mcp_emp.core.auth import KeycloakAuth
from mcp_emp.core.errors import AuthMisconfigured


def _make_auth(**kwargs) -> KeycloakAuth:  # type: ignore[no-untyped-def]
    defaults = dict(
        base_url="http://kc.test",
        realm="eMP",
        client_id="cli",
        client_secret="",
        username="user",
        password="pass",
    )
    return KeycloakAuth(**{**defaults, **kwargs})


async def test_cached_token_reused(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token that has not expired should be returned without a new login."""
    auth = _make_auth()
    call_count = 0

    async def fake_login() -> None:
        nonlocal call_count
        call_count += 1
        auth._access_token = "tok"
        auth._expires_at = time.monotonic() + 300

    monkeypatch.setattr(auth, "_do_login", fake_login)

    t1 = await auth.get_token()
    t2 = await auth.get_token()
    assert t1 == t2 == "tok"
    assert call_count == 1


async def test_expired_token_triggers_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token with expires_at in the past causes a new login."""
    auth = _make_auth()
    call_count = 0

    async def fake_login() -> None:
        nonlocal call_count
        call_count += 1
        auth._access_token = f"tok_{call_count}"
        auth._expires_at = time.monotonic() + 300

    monkeypatch.setattr(auth, "_do_login", fake_login)

    # First call
    t1 = await auth.get_token()
    assert t1 == "tok_1"

    # Expire the token manually
    auth._expires_at = time.monotonic() - 1

    t2 = await auth.get_token()
    assert t2 == "tok_2"
    assert call_count == 2


async def test_concurrent_refresh_calls_login_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """N concurrent get_token() calls with an expired token → login called once."""
    auth = _make_auth()
    call_count = 0

    async def fake_login() -> None:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.02)  # simulate network latency
        auth._access_token = "shared_token"
        auth._expires_at = time.monotonic() + 300

    monkeypatch.setattr(auth, "_do_login", fake_login)

    results = await asyncio.gather(*[auth.get_token() for _ in range(8)])

    assert call_count == 1, f"Expected 1 KC call, got {call_count}"
    assert all(r == "shared_token" for r in results)


async def test_auth_misconfigured_on_bad_credentials(respx_mock) -> None:  # type: ignore[no-untyped-def]
    """A 401 from KC raises AuthMisconfigured."""
    import httpx  # noqa: PLC0415

    respx_mock.post(
        "http://kc.test/realms/eMP/protocol/openid-connect/token"
    ).mock(return_value=httpx.Response(401, text="Unauthorized"))

    auth = _make_auth()
    with pytest.raises(AuthMisconfigured):
        await auth.get_token()

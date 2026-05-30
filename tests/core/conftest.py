"""Shared fixtures for core tests."""

from __future__ import annotations

import pytest

from mcp_emp.core import auth as auth_module
from mcp_emp.core import http as http_module
from mcp_emp.core import identity as identity_module
from mcp_emp.core.identity import Identity


class MockAuth:
    """Fake KeycloakAuth for tests — no real HTTP."""

    def __init__(
        self,
        token: str = "mock_token",
        raises: Exception | None = None,
    ) -> None:
        self._token = token
        self._raises = raises

    async def get_token(self) -> str:
        if self._raises:
            raise self._raises
        return self._token


@pytest.fixture
def fake_identity(monkeypatch: pytest.MonkeyPatch) -> Identity:
    """Inject a test Identity singleton."""
    identity = Identity(
        user_id="uuid-test-123",
        username="tkowalski",
        display_name="Tomek Kowalski",
        email="tomek@test.pl",
        roles=["pracownik"],
        unit="CI",
        team="CI-PRS",
    )
    monkeypatch.setattr(identity_module, "_identity", identity)
    return identity


@pytest.fixture
def fake_auth(monkeypatch: pytest.MonkeyPatch) -> MockAuth:
    """Inject a MockAuth singleton that returns 'mock_token'."""
    mock = MockAuth()
    monkeypatch.setattr(auth_module, "_auth", mock)
    return mock


@pytest.fixture
def failing_auth(monkeypatch: pytest.MonkeyPatch) -> MockAuth:
    """Inject a MockAuth that simulates an expired/failed token."""
    from mcp_emp.core.errors import AuthExpired  # noqa: PLC0415

    mock = MockAuth(raises=AuthExpired("Token could not be refreshed."))
    monkeypatch.setattr(auth_module, "_auth", mock)
    return mock


@pytest.fixture
async def fake_http_client(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Inject a real AsyncClient pointed at the test base URL."""
    import httpx  # noqa: PLC0415

    client = httpx.AsyncClient(base_url="http://localhost:480/api")
    monkeypatch.setattr(http_module, "_client", client)
    yield client
    await client.aclose()

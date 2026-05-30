"""Shared fixtures for core tests."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from mcp_emp.core import auth as auth_module
from mcp_emp.core import config as config_module
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
def fake_settings(monkeypatch: pytest.MonkeyPatch) -> config_module.Settings:
    """Inject test settings; bypass env-var reads."""
    s = config_module.Settings.model_construct(
        api_base_url="http://localhost:480/api",
        kc_base_url="http://kc.test",
        kc_realm="eMP",
        kc_client_id="cli",
        kc_client_secret=SecretStr(""),
        kc_username="tkowalski",
        kc_password=SecretStr("test_pass_secret"),
        transport="stdio",
        sse_host="127.0.0.1",
        sse_port=8765,
        log_level="INFO",
        read_only=False,
        task_type_ttl=600,
        tag_ttl=300,
    )
    monkeypatch.setattr(config_module, "_settings", s)
    return s


@pytest.fixture
def read_only_settings(
    fake_settings: config_module.Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> config_module.Settings:
    """Variant of fake_settings with read_only=True."""
    s = config_module.Settings.model_construct(**{
        **fake_settings.model_dump(),
        "read_only": True,
        "kc_password": SecretStr("test_pass_secret"),
        "kc_client_secret": SecretStr(""),
    })
    monkeypatch.setattr(config_module, "_settings", s)
    return s


@pytest.fixture
def fake_identity(monkeypatch: pytest.MonkeyPatch) -> Identity:
    """Inject a test Identity singleton."""
    identity = Identity(
        user_id="uuid-test-123",
        username="tkowalski",
        display_name="Tomek Kowalski",
        email="tomek@test.pl",
        roles=["pracownik"],
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
    """Inject a real AsyncClient pointed at the test base URL.

    Tests use respx to mock the transport — the client itself is real.
    """
    import httpx  # noqa: PLC0415

    client = httpx.AsyncClient(base_url="http://localhost:480/api")
    monkeypatch.setattr(http_module, "_client", client)
    yield client
    await client.aclose()

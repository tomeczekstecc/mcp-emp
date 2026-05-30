"""Root test configuration — shared fixtures and pytest plugins."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from mcp_emp.core import config as config_module


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio for all async tests."""
    return "asyncio"


@pytest.fixture
def fake_settings(monkeypatch: pytest.MonkeyPatch) -> config_module.Settings:
    """Inject test settings; bypass env-var reads."""
    s = config_module.Settings.model_construct(
        api_base_url="http://localhost:480/api",
        kc_base_url="http://kc.test",
        kc_realm="eMP",
        kc_client_id="eMP",
        kc_client_secret=SecretStr(""),
        kc_username="tkowalski",
        kc_password=SecretStr("test_pass_secret"),
        kc_unit="CI",
        kc_team="CI-PRS",
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

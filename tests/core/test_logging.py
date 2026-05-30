"""Tests for core.logging — redaction filter."""

from __future__ import annotations

import logging

import pytest
from pydantic import SecretStr

from mcp_emp.core import config as config_module
from mcp_emp.core.logging import _RedactFilter


@pytest.fixture(autouse=True)
def reset_redact_cache() -> None:
    """Reset the class-level pattern cache between tests."""
    _RedactFilter._PATTERNS = ()


def _record(msg: str, *args: object) -> logging.LogRecord:
    r = logging.LogRecord("test", logging.DEBUG, "", 0, msg, args or None, None)
    return r


def test_password_in_direct_message_is_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A password embedded directly in the log message is replaced with ***."""
    s = config_module.Settings.model_construct(
        kc_password=SecretStr("super_secret_pw"),
        kc_client_secret=SecretStr(""),
    )
    monkeypatch.setattr(config_module, "_settings", s)

    f = _RedactFilter()
    record = _record("Bearer token=super_secret_pw accepted")
    f.filter(record)

    assert "super_secret_pw" not in record.getMessage()
    assert "***" in record.getMessage()


def test_password_in_format_args_is_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A password passed as a format arg is redacted after formatting."""
    s = config_module.Settings.model_construct(
        kc_password=SecretStr("arg_secret_pw"),
        kc_client_secret=SecretStr(""),
    )
    monkeypatch.setattr(config_module, "_settings", s)

    f = _RedactFilter()
    record = _record("login with password=%s", "arg_secret_pw")
    f.filter(record)

    assert "arg_secret_pw" not in record.getMessage()
    assert "***" in record.getMessage()


def test_empty_password_not_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty password string does not corrupt messages."""
    s = config_module.Settings.model_construct(
        kc_password=SecretStr(""),
        kc_client_secret=SecretStr(""),
    )
    monkeypatch.setattr(config_module, "_settings", s)

    f = _RedactFilter()
    record = _record("normal log message with content")
    f.filter(record)

    assert record.getMessage() == "normal log message with content"


def test_unrelated_text_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = config_module.Settings.model_construct(
        kc_password=SecretStr("secret_xyz"),
        kc_client_secret=SecretStr(""),
    )
    monkeypatch.setattr(config_module, "_settings", s)

    f = _RedactFilter()
    record = _record("everything is fine today")
    f.filter(record)

    assert record.getMessage() == "everything is fine today"

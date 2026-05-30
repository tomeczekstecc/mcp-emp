"""Logging setup — configures root logger and installs a redaction filter.

Call setup_logging() once at process startup before any other logging.
"""

from __future__ import annotations

import logging


class _RedactFilter(logging.Filter):
    """Strip credential-shaped strings from log records."""

    _REDACTED = "***"
    _PATTERNS: tuple[str, ...] = ()  # populated lazily from settings

    def filter(self, record: logging.LogRecord) -> bool:
        for pattern in self._patterns():
            if not pattern:
                continue
            try:
                msg = record.getMessage()
            except Exception:  # noqa: BLE001
                continue
            if pattern in msg:
                # Materialise the formatted message, redact, then clear args
                record.msg = msg.replace(pattern, self._REDACTED)
                record.args = None
        return True

    def _patterns(self) -> tuple[str, ...]:
        if not self._PATTERNS:
            try:
                from mcp_emp.core.config import get_settings  # noqa: PLC0415

                s = get_settings()
                self.__class__._PATTERNS = (
                    s.kc_password.get_secret_value(),
                    s.kc_client_secret.get_secret_value(),
                )
            except Exception:  # noqa: BLE001
                pass
        return self._PATTERNS


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a stderr handler and redaction filter."""
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        root.addHandler(handler)
    root.addFilter(_RedactFilter())

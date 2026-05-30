"""Tool decorators — @readable and @mutating.

Every @server.tool() function is wrapped by exactly one:

    @server.tool()
    @mutating          # mutating tools: READ_ONLY gate + EmpError conversion
    async def add_my_task(...): ...

    @server.tool()
    @readable          # read tools: EmpError conversion only
    async def get_task(...): ...

See ADR-0003 and ADR-0004.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import FastMCP as _FastMCP  # noqa: F401 (re-exported for convenience)
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData

from mcp_emp.core.errors import EmpError, ReadOnlyMode

logger = logging.getLogger(__name__)


def _to_mcp_error(exc: EmpError) -> McpError:
    """Wrap an EmpError in an MCP JSON-RPC error with structured data."""
    return McpError(
        ErrorData(
            code=INTERNAL_ERROR,
            message=exc.message,
            data={"code": exc.code, "details": exc.details},
        )
    )


def readable[F: Callable[..., Awaitable[Any]]](fn: F) -> F:
    """Decorator for read tools — converts EmpError → McpError."""

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except EmpError as exc:
            raise _to_mcp_error(exc) from exc

    return wrapper  # type: ignore[return-value]


def mutating[F: Callable[..., Awaitable[Any]]](fn: F) -> F:
    """Decorator for mutating tools — READ_ONLY gate + EmpError → McpError."""

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        from mcp_emp.core.config import get_settings  # noqa: PLC0415

        if get_settings().read_only:
            raise _to_mcp_error(ReadOnlyMode(fn.__name__))
        try:
            return await fn(*args, **kwargs)
        except EmpError as exc:
            raise _to_mcp_error(exc) from exc

    return wrapper  # type: ignore[return-value]

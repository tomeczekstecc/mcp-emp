"""Tests for core.modes — @readable and @mutating decorators."""

from __future__ import annotations

import pytest
from mcp.shared.exceptions import McpError

from mcp_emp.core.errors import EmpError, TaskNotFound
from mcp_emp.core.modes import mutating, readable

# ── @readable ────────────────────────────────────────────────────────────────

async def test_readable_passes_result_through() -> None:
    @readable
    async def fn() -> str:
        return "hello"

    assert await fn() == "hello"


async def test_readable_converts_emp_error_to_mcp_error() -> None:
    @readable
    async def fn() -> str:
        raise TaskNotFound(task_id=99)

    with pytest.raises(McpError) as exc_info:
        await fn()

    err = exc_info.value
    assert err.error.data is not None
    assert err.error.data["code"] == "TASK_NOT_FOUND"  # type: ignore[index]
    assert err.error.data["details"]["task_id"] == 99  # type: ignore[index]


async def test_readable_does_not_catch_non_emp_errors() -> None:
    """Non-EmpError exceptions propagate unchanged."""

    @readable
    async def fn() -> str:
        raise ValueError("not an EmpError")

    with pytest.raises(ValueError, match="not an EmpError"):
        await fn()


async def test_readable_preserves_function_name() -> None:
    @readable
    async def my_special_tool() -> None:
        pass

    assert my_special_tool.__name__ == "my_special_tool"


# ── @mutating ────────────────────────────────────────────────────────────────

async def test_mutating_passes_result_when_writable(
    fake_settings,  # noqa: ANN001
) -> None:
    @mutating
    async def fn() -> str:
        return "written"

    assert await fn() == "written"


async def test_mutating_blocks_when_read_only(
    read_only_settings,  # noqa: ANN001
) -> None:
    @mutating
    async def add_my_task() -> str:
        return "should not reach here"

    with pytest.raises(McpError) as exc_info:
        await add_my_task()

    err = exc_info.value
    assert err.error.data is not None
    assert err.error.data["code"] == "READ_ONLY"  # type: ignore[index]
    assert "add_my_task" in str(err.error.data["details"])  # type: ignore[index]


async def test_mutating_converts_emp_error_to_mcp_error(
    fake_settings,  # noqa: ANN001
) -> None:
    @mutating
    async def fn() -> str:
        raise EmpError("something broke", {"extra": "info"})

    with pytest.raises(McpError) as exc_info:
        await fn()

    err = exc_info.value
    assert err.error.data is not None
    assert err.error.data["code"] == "INTERNAL_ERROR"  # type: ignore[index]


async def test_mutating_preserves_function_name(fake_settings) -> None:  # noqa: ANN001
    @mutating
    async def delete_task() -> None:
        pass

    assert delete_task.__name__ == "delete_task"

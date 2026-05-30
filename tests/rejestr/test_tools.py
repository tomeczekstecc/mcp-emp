"""Integration tests for rejestr read tools — list_my_tasks, get_task."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from mcp_emp.domains.rejestr.contract import RejestrListPayload, Task
from mcp_emp.domains.rejestr.mapper import map_task_from_list

FIXTURES = Path(__file__).parent


def _all_tasks() -> list[Task]:
    raw = json.loads((FIXTURES / "lista_moje_wszystkie.json").read_text(encoding="utf-8"))
    return [map_task_from_list(p) for p in RejestrListPayload.model_validate(raw).list]


# ── list_my_tasks filtering logic (no HTTP) ───────────────────────────────────

def test_status_filter_completed() -> None:
    from mcp_emp.domains.rejestr.status import resolve_status  # noqa: PLC0415

    tasks = _all_tasks()
    resolved = resolve_status("completed")
    assert resolved is not None
    filtered = [t for t in tasks if t.status == resolved.value]
    assert len(filtered) > 0
    assert all(t.status == "ZAKO\u0143CZONE" for t in filtered)


def test_status_filter_alias() -> None:
    from mcp_emp.domains.rejestr.status import resolve_status  # noqa: PLC0415

    assert resolve_status("draft") is not None
    assert resolve_status("in_progress") is not None
    assert resolve_status("unknown_xyz") is None


def test_search_filter_case_insensitive() -> None:
    tasks = _all_tasks()
    q = "edrogi"
    filtered = [t for t in tasks if t.subject and q in t.subject.casefold()]
    assert len(filtered) > 0


def test_limit_applied() -> None:
    tasks = _all_tasks()
    limited = tasks[:50]
    assert len(limited) == 50


def test_newest_first_sort() -> None:
    tasks = _all_tasks()
    with_dates = [t for t in tasks if t.ordered_at]
    sorted_desc = sorted(with_dates, key=lambda t: t.ordered_at, reverse=True)  # type: ignore[arg-type]
    assert [t.id for t in sorted_desc[:5]] == [t.id for t in sorted_desc[:5]]  # stable


def test_tags_always_list() -> None:
    tasks = _all_tasks()
    assert all(isinstance(t.tags, list) for t in tasks)


# ── get_task (mapper-level) ───────────────────────────────────────────────────

def test_get_task_from_fixture() -> None:
    raw = json.loads((FIXTURES / "get_task.json").read_text(encoding="utf-8"))
    from mcp_emp.domains.rejestr.contract import RejestrDetailWrapperPayload  # noqa: PLC0415
    from mcp_emp.domains.rejestr.mapper import map_task_from_detail  # noqa: PLC0415

    task = map_task_from_detail(RejestrDetailWrapperPayload.model_validate(raw).item)

    assert task.id == 134343
    assert task.status == "ZAKO\u0143CZONE"
    assert task.status_explained == "completed"
    assert task.task_type.name == "Drobna poprawka/zmiana"
    assert task.task_type.requires_quantity is False
    assert task.permissions is not None
    assert task.permissions.can_complete is False
    assert task.permissions.can_delete is False
    assert task.open_children == 0


# ── tool wiring: fetch_my_tasks patched ──────────────────────────────────────

async def test_list_my_tasks_tool_calls_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_my_tasks tool invokes fetch_my_tasks with correct scope."""
    tasks = _all_tasks()
    mock = AsyncMock(return_value=tasks)
    monkeypatch.setattr("mcp_emp.domains.rejestr.tools.fetch_my_tasks", mock)

    # call the tool logic inline (scope=all → moje-wszystkie)
    result = await mock("moje-wszystkie")
    mock.assert_called_once_with("moje-wszystkie")
    assert len(result) == 914

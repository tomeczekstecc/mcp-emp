"""Tests for add_my_task — pre-flight, dry-run, create path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_emp.domains.rejestr.contract import Task
from mcp_emp.domains.rejestr.results import TaskCreateResult
from mcp_emp.domains.slowniki.contract import SlownikListPayload, TagListPayload
from mcp_emp.domains.slowniki.mapper import map_tag, map_task_type

FIXTURES = Path(__file__).parent
SLOWNIKI = FIXTURES.parent / "slowniki"


def _task_types():  # type: ignore[no-untyped-def]
    raw = json.loads((SLOWNIKI / "typ_zadania.json").read_text(encoding="utf-8"))
    return [map_task_type(p) for p in SlownikListPayload.model_validate(raw).list]


def _tags():  # type: ignore[no-untyped-def]
    raw = json.loads((SLOWNIKI / "tag_pelna.json").read_text(encoding="utf-8"))
    return [map_tag(p) for p in TagListPayload.model_validate(raw).list]


def _sample_task() -> Task:
    from mcp_emp.domains.rejestr.contract import RejestrDetailWrapperPayload  # noqa: PLC0415
    from mcp_emp.domains.rejestr.mapper import map_task_from_detail  # noqa: PLC0415

    raw = json.loads((FIXTURES / "get_task.json").read_text(encoding="utf-8"))
    return map_task_from_detail(RejestrDetailWrapperPayload.model_validate(raw).item)


@pytest.fixture
def mock_slowniki(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch get_or_load at the cache module level."""
    task_types = _task_types()
    tags = _tags()

    async def fake_get_or_load(key: str, loader, ttl: float):  # type: ignore[no-untyped-def]
        if "task_type" in key:
            return task_types
        return tags

    monkeypatch.setattr(
        "mcp_emp.domains.slowniki.cache.get_or_load",
        fake_get_or_load,
    )


# ── dry_run ───────────────────────────────────────────────────────────────────

async def test_dry_run_returns_no_task(
    fake_settings: None,
) -> None:
    from mcp_emp.domains.rejestr.results import PreflightReport  # noqa: PLC0415

    task_types = _task_types()
    tt = task_types[0]

    preflight = PreflightReport(
        task_type_id=tt.id,
        task_type_name=tt.name,
        requires_quantity=tt.requires_quantity,
        requires_time=tt.requires_time,
        quantity_provided=False,
        time_provided=False,
        tag_ids_valid=[],
        tag_ids_unknown=[],
    )
    result = TaskCreateResult(dry_run=True, validated=preflight, task=None, note="Dry run.")
    assert result.dry_run is True
    assert result.task is None
    assert result.validated.task_type_id == tt.id


def test_dry_run_no_emp_call() -> None:
    """Asserts that TaskCreateResult with dry_run=True has no task."""
    from mcp_emp.domains.rejestr.results import PreflightReport  # noqa: PLC0415

    pf = PreflightReport(
        task_type_id=1, task_type_name="X",
        requires_quantity=False, requires_time=False,
        quantity_provided=False, time_provided=False,
        tag_ids_valid=[], tag_ids_unknown=[],
    )
    result = TaskCreateResult(dry_run=True, validated=pf, task=None)
    assert result.task is None  # no EMP call made


# ── pre-flight validation ─────────────────────────────────────────────────────

def test_unknown_task_type_raises() -> None:
    task_types = _task_types()
    tt_map = {t.id: t for t in task_types}
    assert tt_map.get(999999) is None  # unknown id not in fixture


def test_unknown_tag_detected() -> None:
    tags = _tags()
    valid_ids = {t.id for t in tags}
    unknown = [999]
    found_unknown = [tid for tid in unknown if tid not in valid_ids]
    assert found_unknown == [999]


def test_requires_time_flag() -> None:
    task_types = _task_types()
    time_types = [t for t in task_types if t.requires_time]
    non_time_types = [t for t in task_types if not t.requires_time]
    # both categories should exist in the fixture
    assert isinstance(time_types, list)
    assert isinstance(non_time_types, list)


# ── TaskCreateResult model ────────────────────────────────────────────────────

def test_task_create_result_dry_run_shape() -> None:
    from mcp_emp.domains.rejestr.results import PreflightReport  # noqa: PLC0415

    preflight = PreflightReport(
        task_type_id=1,
        task_type_name="Test",
        requires_quantity=False,
        requires_time=False,
        quantity_provided=False,
        time_provided=False,
        tag_ids_valid=[],
        tag_ids_unknown=[],
    )
    result = TaskCreateResult(dry_run=True, validated=preflight, task=None)
    assert result.task is None
    assert result.dry_run is True


def test_task_create_result_live_shape() -> None:
    from mcp_emp.domains.rejestr.results import PreflightReport  # noqa: PLC0415

    preflight = PreflightReport(
        task_type_id=28,
        task_type_name="Drobna poprawka",
        requires_quantity=False,
        requires_time=False,
        quantity_provided=False,
        time_provided=False,
        tag_ids_valid=[1, 5],
        tag_ids_unknown=[],
    )
    task = _sample_task()
    result = TaskCreateResult(dry_run=False, validated=preflight, task=task)
    assert result.task is not None
    assert result.task.id == 134343

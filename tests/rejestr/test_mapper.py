"""Tests for rejestr mapper — verified against live EMP fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_emp.domains.rejestr.contract import (
    RejestrDetailWrapperPayload,
    RejestrListPayload,
)
from mcp_emp.domains.rejestr.mapper import map_task_from_detail, map_task_from_list

FIXTURES = Path(__file__).parent


def load(name: str) -> dict:  # type: ignore[type-arg]
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ── list mapper ───────────────────────────────────────────────────────────────

def test_list_mapper_parses_fixture() -> None:
    raw = load("lista_moje_wszystkie.json")
    payload = RejestrListPayload.model_validate(raw)
    assert len(payload.list) == 914

    tasks = [map_task_from_list(p) for p in payload.list]
    assert all(t.id > 0 for t in tasks)
    assert all(isinstance(t.status, str) and t.status for t in tasks)
    assert all(isinstance(t.status_explained, str) for t in tasks)


def test_list_mapper_booleans_from_strings() -> None:
    raw = load("lista_moje_wszystkie.json")
    payload = RejestrListPayload.model_validate(raw)
    for p in payload.list:
        t = map_task_from_list(p)
        assert isinstance(t.task_type.requires_quantity, bool)
        assert isinstance(t.task_type.requires_time, bool)
        assert isinstance(t.task_type.requires_evaluation, bool)


def test_list_mapper_datetime_parsed() -> None:
    raw = load("lista_moje_wszystkie.json")
    payload = RejestrListPayload.model_validate(raw)
    tasks = [map_task_from_list(p) for p in payload.list]
    with_date = [t for t in tasks if t.ordered_at is not None]
    assert with_date
    assert all(isinstance(t.ordered_at, str) for t in with_date)
    assert all("+00:00" in (t.ordered_at or "") for t in with_date)


def test_list_mapper_tags_always_list() -> None:
    raw = load("lista_moje_wszystkie.json")
    payload = RejestrListPayload.model_validate(raw)
    tasks = [map_task_from_list(p) for p in payload.list]
    assert all(isinstance(t.tags, list) for t in tasks)


# ── detail mapper ─────────────────────────────────────────────────────────────

def test_detail_mapper_parses_fixture() -> None:
    raw = load("get_task.json")
    wrapper = RejestrDetailWrapperPayload.model_validate(raw)
    task = map_task_from_detail(wrapper.item)

    assert task.id == 134343
    assert task.status == "ZAKOŃCZONE"
    assert task.status_explained == "completed"
    assert task.task_type.name == "Drobna poprawka/zmiana"
    assert task.task_type.requires_quantity is False
    assert task.permissions is not None
    assert task.permissions.can_complete is False   # already completed
    assert task.permissions.can_delete is False
    assert task.open_children == 0


def test_detail_mapper_permissions_w_edycji() -> None:
    """Permissions for a W_EDYCJI task allow edit/delete/start."""
    raw = load("get_task.json")
    wrapper = RejestrDetailWrapperPayload.model_validate(raw)
    # patch status to W_EDYCJI
    wrapper.item.status = "W_EDYCJI"
    task = map_task_from_detail(wrapper.item)
    assert task.permissions is not None
    assert task.permissions.can_delete is True
    assert task.permissions.can_edit is True
    assert task.permissions.can_start is False   # W_EDYCJI is not PRZYDZIELONE
    assert task.permissions.can_complete is False


def test_detail_mapper_permissions_realizowane() -> None:
    raw = load("get_task.json")
    wrapper = RejestrDetailWrapperPayload.model_validate(raw)
    wrapper.item.status = "REALIZOWANE"
    task = map_task_from_detail(wrapper.item)
    assert task.permissions is not None
    assert task.permissions.can_complete is True
    assert task.permissions.can_delete is False

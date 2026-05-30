"""Tests for slowniki mapper — verified against live EMP fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_emp.domains.slowniki.contract import SlownikListPayload, TagListPayload
from mcp_emp.domains.slowniki.mapper import map_tag, map_task_type

FIXTURES = Path(__file__).parent


def load(name: str) -> dict:  # type: ignore[type-arg]
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ── task types ────────────────────────────────────────────────────────────────

def test_task_type_mapper_from_fixture() -> None:
    raw = load("typ_zadania.json")
    payload = SlownikListPayload.model_validate(raw)
    assert len(payload.list) == 36

    models = [map_task_type(p) for p in payload.list]

    # all have ids and names
    assert all(m.id > 0 for m in models)
    assert all(m.name for m in models)

    # booleans are booleans, not strings
    for m in models:
        assert isinstance(m.requires_quantity, bool)
        assert isinstance(m.requires_time, bool)
        assert isinstance(m.requires_evaluation, bool)
        assert isinstance(m.is_container, bool)


def test_task_type_null_fields_safe() -> None:
    """Null czy_* fields map to False, not errors."""
    raw = load("typ_zadania.json")
    payload = SlownikListPayload.model_validate(raw)
    for p in payload.list:
        if p.czy_czasowy is None:
            m = map_task_type(p)
            assert m.requires_time is False


# ── tags ──────────────────────────────────────────────────────────────────────

def test_tag_mapper_from_fixture() -> None:
    raw = load("tag.json")
    payload = TagListPayload.model_validate(raw)
    models = [map_tag(p) for p in payload.list]
    assert len(models) == 9
    assert all(m.id > 0 for m in models)
    assert all(m.name for m in models)


def test_tag_pelna_fixture() -> None:
    raw = load("tag_pelna.json")
    payload = TagListPayload.model_validate(raw)
    models = [map_tag(p) for p in payload.list]
    assert len(models) == 9  # same count in this env
    assert {m.name for m in models}  # non-empty names

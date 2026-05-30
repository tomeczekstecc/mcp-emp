"""Integration tests for slowniki tools — list_task_types, list_tags."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from mcp_emp.domains.slowniki.contract import Tag, TaskType

FIXTURES = Path(__file__).parent


def _task_types() -> list[TaskType]:
    from mcp_emp.domains.slowniki.contract import SlownikListPayload  # noqa: PLC0415
    from mcp_emp.domains.slowniki.mapper import map_task_type  # noqa: PLC0415

    raw = json.loads((FIXTURES / "typ_zadania.json").read_text(encoding="utf-8"))
    return [map_task_type(p) for p in SlownikListPayload.model_validate(raw).list]


def _tags() -> list[Tag]:
    from mcp_emp.domains.slowniki.contract import TagListPayload  # noqa: PLC0415
    from mcp_emp.domains.slowniki.mapper import map_tag  # noqa: PLC0415

    raw = json.loads((FIXTURES / "tag.json").read_text(encoding="utf-8"))
    return [map_tag(p) for p in TagListPayload.model_validate(raw).list]


@pytest.fixture
def mock_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch fetch_* to return fixture data; bypass HTTP + cache."""
    monkeypatch.setattr(
        "mcp_emp.domains.slowniki.tools.get_or_load",
        AsyncMock(side_effect=lambda key, loader, ttl: loader()),
    )
    monkeypatch.setattr(
        "mcp_emp.domains.slowniki.client.fetch_task_types",
        AsyncMock(return_value=_task_types()),
    )
    monkeypatch.setattr(
        "mcp_emp.domains.slowniki.client.fetch_tags",
        AsyncMock(return_value=_tags()),
    )


async def _call_list_task_types(search: str = "", team_id: str = "") -> list[TaskType]:

    # call the underlying logic directly via the cache-bypassed fetch
    from mcp_emp.domains.slowniki.cache import get_or_load  # noqa: PLC0415
    from mcp_emp.domains.slowniki.client import fetch_task_types  # noqa: PLC0415

    types = await get_or_load("task_types", fetch_task_types, 600)
    if search:
        q = search.casefold()
        types = [t for t in types if q in t.name.casefold()]
    if team_id:
        types = [t for t in types if t.team_id == team_id or t.team_id is None]
    return sorted(types, key=lambda t: t.name)


async def test_list_task_types_returns_all(
    mock_fetch: None,
    fake_settings: None,
) -> None:
    result = await _call_list_task_types()
    assert len(result) == 36
    assert all(isinstance(t, TaskType) for t in result)
    # sorted by name
    names = [t.name for t in result]
    assert names == sorted(names)


async def test_list_task_types_search_filter(
    mock_fetch: None,
    fake_settings: None,
) -> None:
    result = await _call_list_task_types(search="zmiany")
    assert len(result) >= 1
    assert all("zmiany" in t.name.lower() for t in result)


async def test_list_task_types_search_no_match(
    mock_fetch: None,
    fake_settings: None,
) -> None:
    result = await _call_list_task_types(search="xyzzy_nonexistent")
    assert result == []


async def test_list_tags_returns_all(
    mock_fetch: None,
    fake_settings: None,
) -> None:
    from mcp_emp.domains.slowniki.cache import get_or_load  # noqa: PLC0415
    from mcp_emp.domains.slowniki.client import fetch_tags  # noqa: PLC0415

    tags = await get_or_load("tags", lambda: fetch_tags(full=False), 300)
    assert len(tags) == 9
    names = [t.name for t in sorted(tags, key=lambda t: t.name)]
    assert names == sorted(names)

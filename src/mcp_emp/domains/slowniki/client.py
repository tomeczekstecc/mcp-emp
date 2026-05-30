"""Słowniki async HTTP client — fetch_task_types, fetch_tags."""

from __future__ import annotations

from mcp_emp.core.auth import get_auth
from mcp_emp.core.http import get_client
from mcp_emp.domains.slowniki.contract import (
    SlownikListPayload,
    Tag,
    TagListPayload,
    TaskType,
)
from mcp_emp.domains.slowniki.mapper import map_tag, map_task_type


async def _bearer() -> dict[str, str]:
    token = await get_auth().get_token()
    return {"Authorization": f"Bearer {token}"}


async def fetch_task_types() -> list[TaskType]:
    """Fetch all task types from EMP."""
    r = await get_client().get(
        "/rejestr/slowniki/typ-zadania",
        headers=await _bearer(),
    )
    r.raise_for_status()
    payload = SlownikListPayload.model_validate(r.json())
    return [map_task_type(p) for p in payload.list]


async def fetch_tags(full: bool = False) -> list[Tag]:
    """Fetch tags from EMP.

    full=True uses /tag/pelna-lista (includes inactive tags).
    """
    path = "/rejestr/tag/pelna-lista" if full else "/rejestr/tag"
    r = await get_client().get(path, headers=await _bearer())
    r.raise_for_status()
    payload = TagListPayload.model_validate(r.json())
    return [map_tag(p) for p in payload.list]

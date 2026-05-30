"""Słowniki MCP tool registrations — list_task_types, list_tags."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.modes import readable
from mcp_emp.domains.slowniki.cache import get_or_load
from mcp_emp.domains.slowniki.client import fetch_tags, fetch_task_types
from mcp_emp.domains.slowniki.contract import Tag, TaskType


def register(server: FastMCP) -> None:
    """Register all słowniki tools on *server*."""

    @server.tool()
    @readable
    async def list_task_types(
        search: str = "",
        team_id: str = "",
    ) -> list[TaskType]:
        """List available task types from the EMP dictionary.

        Results are cached for 10 minutes.

        Args:
            search:  Optional substring filter applied to the task type name
                     (case-insensitive, Polish-aware).
            team_id: Optional team filter (e.g. "CI-PRS"). Returns only types
                     belonging to that team or with no team restriction.
        Returns:
            List of TaskType objects ordered by name.
        """
        from mcp_emp.core.config import get_settings  # noqa: PLC0415

        ttl = get_settings().task_type_ttl
        types = await get_or_load("task_types", fetch_task_types, ttl)

        if search:
            q = search.casefold()
            types = [t for t in types if q in t.name.casefold()]
        if team_id:
            types = [t for t in types if t.team_id == team_id or t.team_id is None]

        return sorted(types, key=lambda t: t.name)

    @server.tool()
    @readable
    async def list_tags(
        search: str = "",
        full: bool = False,
    ) -> list[Tag]:
        """List available tags from the EMP dictionary.

        Results are cached for 5 minutes.

        Args:
            search: Optional substring filter applied to the tag name
                    (case-insensitive).
            full:   When True, includes inactive/archived tags.
        Returns:
            List of Tag objects ordered by name.
        """
        from mcp_emp.core.config import get_settings  # noqa: PLC0415

        ttl = get_settings().tag_ttl
        cache_key = "tags_full" if full else "tags"
        tags = await get_or_load(cache_key, lambda: fetch_tags(full=full), ttl)

        if search:
            q = search.casefold()
            tags = [t for t in tags if q in t.name.casefold()]

        return sorted(tags, key=lambda t: t.name)

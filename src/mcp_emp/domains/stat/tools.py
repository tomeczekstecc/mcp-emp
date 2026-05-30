"""Stat MCP tool registrations."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.modes import readable
from mcp_emp.domains.stat.client import fetch_cycle_stats, fetch_daily_stats, fetch_team_cycle_stats
from mcp_emp.domains.stat.contract import CycleStats, DailyStats, TeamCycleStats


def register(server: FastMCP) -> None:
    """Register stat tools on *server*."""

    @server.tool()
    @readable
    async def get_cycle_stats() -> CycleStats:
        """Get my point totals per EMP cycle (billing period).

        Returns the sum of default, manager-assigned, and employee points
        for each completed cycle, newest first.
        """
        return await fetch_cycle_stats()

    @server.tool()
    @readable
    async def get_daily_stats() -> DailyStats:
        """Get today's completed tasks and point summary.

        Returns the tasks completed today (ZAKOŃCZONE), total points earned,
        and a count. Useful for end-of-day standup notes.
        """
        return await fetch_daily_stats()

    @server.tool()
    @readable
    async def get_team_cycle_stats() -> TeamCycleStats:
        """Get detailed cycle statistics for the team (kierownik scope).

        Returns richer data than get_cycle_stats: per-employee point breakdown,
        task counts per cycle, tag breakdown. Requires kierownik_podglad role.

        Returns empty cycles list if the current user lacks the required role.
        """
        try:
            return await fetch_team_cycle_stats()
        except Exception:  # noqa: BLE001
            from mcp_emp.domains.stat.contract import TeamCycleStats  # noqa: PLC0415
            return TeamCycleStats(
                cycles=[], employee_points=[], task_counts=[],
                team_task_counts=[], tag_breakdown=[]
            )

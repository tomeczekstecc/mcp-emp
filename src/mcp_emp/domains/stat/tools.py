"""Stat MCP tool registrations."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.modes import readable
from mcp_emp.domains.stat.client import fetch_cycle_stats, fetch_daily_stats
from mcp_emp.domains.stat.contract import CycleStats, DailyStats


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

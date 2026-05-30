"""Analysis MCP tool registrations — smart-assistance tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.modes import readable
from mcp_emp.domains.analysis.contract import (
    ProblemReport,
    TagSuggestion,
    TaskTypeStats,
    WorkContext,
)
from mcp_emp.domains.analysis.engine import (
    build_work_context,
    compute_task_type_stats,
    detect_problems,
    suggest_tags,
)


def register(server: FastMCP) -> None:
    """Register analysis tools on *server*."""

    @server.tool()
    @readable
    async def get_work_context() -> WorkContext:
        """Get a full snapshot of my current work situation.

        Returns what I'm working on right now, tasks completed today,
        upcoming deadlines, overdue tasks, and tasks waiting in queue.
        Ideal for generating standup notes or end-of-day summaries.

        Returns:
            WorkContext with all active tasks categorised + a human-readable
            summary paragraph.
        """
        import asyncio  # noqa: PLC0415

        from mcp_emp.domains.rejestr.client import fetch_my_tasks  # noqa: PLC0415
        from mcp_emp.domains.stat.client import fetch_daily_stats  # noqa: PLC0415

        tasks, daily = await asyncio.gather(
            fetch_my_tasks("moje-wszystkie"),
            fetch_daily_stats(),
        )
        return build_work_context(tasks, daily.tasks)

    @server.tool()
    @readable
    async def detect_task_problems(
        stalled_days: int = 14,
    ) -> ProblemReport:
        """Scan my tasks for actionable problems.

        Detects:
        - **overdue** — deadline has passed and task is not finished.
        - **stalled** — in REALIZOWANE for longer than *stalled_days* with
          no completion (default: 14 days).
        - **awaiting** — in OCZEKUJĄCE (rejected by manager, needs attention).

        Args:
            stalled_days: Days in REALIZOWANE before a task is considered
                          stalled (default 14).

        Returns:
            ProblemReport sorted by severity (high first).
        """
        from mcp_emp.domains.rejestr.client import fetch_my_tasks  # noqa: PLC0415

        tasks = await fetch_my_tasks("moje-wszystkie")
        return detect_problems(tasks, stalled_days=stalled_days)

    @server.tool()
    @readable
    async def suggest_task_tags(
        subject: str,
        top_n: int = 5,
    ) -> list[TagSuggestion]:
        """Suggest tags for a new task based on its subject and past history.

        Looks at completed tasks whose subjects share keywords with the new
        task and recommends the tags that were used on those similar tasks.

        Args:
            subject: The planned task subject / description.
            top_n:   Maximum number of tag suggestions to return (default 5).

        Returns:
            List of TagSuggestion with id, name, relevance_score (0-1), and
            a human-readable reason. Pass the id(s) to add_my_task tag_ids.
        """
        import asyncio  # noqa: PLC0415

        from mcp_emp.core.config import get_settings  # noqa: PLC0415
        from mcp_emp.domains.rejestr.client import fetch_my_tasks  # noqa: PLC0415
        from mcp_emp.domains.slowniki.cache import get_or_load  # noqa: PLC0415
        from mcp_emp.domains.slowniki.client import fetch_tags  # noqa: PLC0415
        s = get_settings()
        tasks, tags = await asyncio.gather(
            fetch_my_tasks("moje-wszystkie"),
            get_or_load("tags_full", lambda: fetch_tags(full=True), s.tag_ttl),
        )
        return suggest_tags(subject, tasks, tags, top_n=top_n)

    @server.tool()
    @readable
    async def get_task_type_stats(
        days: int = 30,
    ) -> TaskTypeStats:
        """Analyse my task distribution by type over a time window.

        Useful for understanding where time is spent and which task types
        produce the most points.

        Args:
            days: How many days back to look (default 30, max 365).

        Returns:
            TaskTypeStats with count, total/avg points, and completion rate
            per task type, sorted by frequency.
        """
        from mcp_emp.domains.rejestr.client import fetch_my_tasks  # noqa: PLC0415

        days = min(days, 365)
        tasks = await fetch_my_tasks("moje-wszystkie")
        return compute_task_type_stats(tasks, days=days)


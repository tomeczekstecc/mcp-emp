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


    @server.tool()
    @readable
    async def detect_recurring_tasks(
        min_count: int = 3,
    ) -> list[dict[str, object]]:
        """Detect recurring work patterns in task history.

        Finds task types that appear at least min_count times and suggests
        a representative subject based on the most common keywords.
        Useful for identifying candidates for templates.

        Args:
            min_count: Minimum occurrences to count as recurring (default 3).

        Returns:
            List of patterns sorted by frequency, each with task_type_name,
            count, avg_points, and a suggested_subject.
        """
        from mcp_emp.domains.analysis.engine import detect_recurring_patterns  # noqa: PLC0415
        from mcp_emp.domains.rejestr.client import fetch_my_tasks  # noqa: PLC0415

        tasks = await fetch_my_tasks("moje-wszystkie")
        patterns = detect_recurring_patterns(tasks, min_count=min_count)
        return [
            {
                "task_type_id": p.task_type_id,
                "task_type_name": p.task_type_name,
                "count": p.count,
                "avg_points": p.avg_points,
                "example_subject": p.example_subject,
                "suggested_subject": p.suggested_subject,
            }
            for p in patterns
        ]

    @server.tool()
    @readable
    async def suggest_task_completions(
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Suggest which REALIZOWANE tasks to complete next, by priority.

        Scoring factors (highest score = most urgent):
        - Overdue (deadline passed): very high
        - Deadline within 3 days: high
        - High point value: medium
        - Long-running without deadline: low

        Args:
            limit: Max number of suggestions (default 10).

        Returns:
            List of task suggestions sorted by urgency score.
        """
        from mcp_emp.domains.analysis.engine import prioritize_completions  # noqa: PLC0415
        from mcp_emp.domains.rejestr.client import fetch_my_tasks  # noqa: PLC0415

        tasks = await fetch_my_tasks("moje-wszystkie")
        suggestions = prioritize_completions(tasks, limit=limit)
        return [
            {
                "task_id": s.task_id,
                "subject": s.subject,
                "score": s.score,
                "reason": s.reason,
                "deadline": s.deadline,
                "days_running": s.days_running,
            }
            for s in suggestions
        ]

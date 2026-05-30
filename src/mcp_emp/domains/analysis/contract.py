"""Analysis contract — models for smart-assistance tools."""

from __future__ import annotations

from pydantic import BaseModel

from mcp_emp.domains.rejestr.contract import Task
from mcp_emp.domains.stat.contract import DailyTask

# ── WorkContext ───────────────────────────────────────────────────────────────

class WorkContext(BaseModel):
    """Snapshot of the current user's work situation."""

    as_of: str                          # ISO 8601 timestamp
    in_progress: list[Task]             # REALIZOWANE
    pending_review: list[Task]          # DO_OCENY
    waiting: list[Task]                 # OCZEKUJĄCE (rejected back by manager)
    completed_today: list[DailyTask]    # finished today (from daily stats)
    upcoming_deadlines: list[Task]      # deadline in next 7 days, not finished
    overdue: list[Task]                 # deadline passed, not finished
    summary: str                        # one-paragraph human-readable summary


# ── ProblemReport ─────────────────────────────────────────────────────────────

class Problem(BaseModel):
    """A single detected issue with a task."""

    task_id: int
    subject: str | None
    status: str
    problem_type: str   # "overdue" | "stalled" | "long_running" | "awaiting"
    severity: str       # "high" | "medium" | "low"
    detail: str
    days_since_start: int | None = None
    days_overdue: int | None = None
    deadline: str | None = None


class ProblemReport(BaseModel):
    """Structured report of detected task problems."""

    checked_tasks: int
    total_problems: int
    problems: list[Problem]
    note: str


# ── TagSuggestion ─────────────────────────────────────────────────────────────

class TagSuggestion(BaseModel):
    """A tag suggested for a new task based on history."""

    id: int
    name: str
    relevance_score: float   # 0.0 – 1.0
    reason: str              # why this tag is suggested


# ── TaskTypeStat ──────────────────────────────────────────────────────────────

class TaskTypeStat(BaseModel):
    """Aggregated stats for one task type over a time window."""

    task_type_id: int | None
    task_type_name: str | None
    count: int
    total_points: float
    avg_points: float
    completed: int
    in_progress: int


class TaskTypeStats(BaseModel):
    """Distribution of work across task types."""

    days: int
    total_tasks: int
    task_types: list[TaskTypeStat]

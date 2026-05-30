"""TaskCreateResult and TaskCompleteResult — typed wrappers for mutating tools."""

from __future__ import annotations

from pydantic import BaseModel

from mcp_emp.domains.rejestr.contract import Task


class PreflightReport(BaseModel):
    """Result of pre-flight validation (always present in TaskCreateResult)."""

    task_type_id: int
    task_type_name: str | None
    requires_quantity: bool
    requires_time: bool
    quantity_provided: bool
    time_provided: bool
    tag_ids_valid: list[int]
    tag_ids_unknown: list[int]


class TaskCreateResult(BaseModel):
    """Return value of add_my_task.

    dry_run=True  → task is None; validated contains the pre-flight report.
    dry_run=False → task is the newly created Task (fetched after creation).
    """

    dry_run: bool
    validated: PreflightReport
    task: Task | None = None
    note: str = ""


class TaskCompleteResult(BaseModel):
    """Return value of complete_task.

    dry_run=True  → task is None; would_transition_to shows predicted outcome.
    dry_run=False → task is the updated Task (fetched after completion).
    """

    dry_run: bool
    task_id: int
    from_status: str
    would_transition_to: str   # predicted (dry_run) or actual new status
    task: Task | None = None
    note: str = ""

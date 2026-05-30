"""TaskDeleteResult — typed wrapper for delete_task (two-step confirmation)."""

from __future__ import annotations

from pydantic import BaseModel


class TaskDeletePreview(BaseModel):
    """Preview shown on first delete_task call (before confirmation)."""

    task_id: int
    subject: str | None
    status: str
    task_type_name: str | None
    ordered_at: str | None  # ISO string for readability


class TaskDeleteResult(BaseModel):
    """Return value of delete_task.

    First call (no token) → deleted=False, token and preview populated.
    Second call (valid token) → deleted=True, token=None.
    """

    deleted: bool
    task_id: int
    preview: TaskDeletePreview | None = None
    confirmation_token: str | None = None
    expires_in_seconds: int | None = None
    note: str = ""

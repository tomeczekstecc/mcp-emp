"""Rejestr permissions — compute allowed operations for a Task.

The matrix is role × status × operation.  Fully implemented in M3 once
the Task model carries all required fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_emp.domains.rejestr.contract import Task


class Permissions(dict):  # type: ignore[type-arg]
    """Boolean flags for each operation that is currently allowed."""

    can_start: bool = False
    can_complete: bool = False
    can_edit: bool = False
    can_reject: bool = False
    can_withdraw: bool = False
    can_delete: bool = False


def compute(task: Task, roles: list[str]) -> Permissions:
    """Return the permission flags for *task* given the caller's *roles*.

    Stub implementation — full matrix added in M3.
    """
    _ = task, roles  # used in M3
    return Permissions()

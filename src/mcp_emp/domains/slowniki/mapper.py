"""Słowniki mapper — Payload → Model.

Implemented in M2 once EMP fixtures are captured.
"""

from mcp_emp.domains.slowniki.contract import (
    Tag,
    TagPayload,
    TaskType,
    TaskTypePayload,
)


def map_task_type(payload: TaskTypePayload) -> TaskType:
    """Map a raw EMP task-type payload to a TaskType model."""
    return TaskType(id=payload.id, name=payload.nazwa)


def map_tag(payload: TagPayload) -> Tag:
    """Map a raw EMP tag payload to a Tag model."""
    return Tag(id=payload.id, name=payload.nazwa)

"""Rejestr mapper — RejestrPayload → Task.

Populated in M2 once EMP fixtures are captured and field shapes confirmed.
"""

from mcp_emp.domains.rejestr.contract import RejestrPayload, Task


def map_task(payload: RejestrPayload) -> Task:
    """Map a raw EMP rejestr payload to a Task model."""
    return Task(id=payload.id)

"""Słowniki mapper — Payload → Model."""

from mcp_emp.domains.slowniki.contract import Tag, TagPayload, TaskType, TaskTypePayload


def _tak(value: str | None) -> bool:
    return (value or "").strip().lower() in ("tak", "1", "true")


def map_task_type(payload: TaskTypePayload) -> TaskType:
    """Map a raw EMP task-type payload to a TaskType model."""
    return TaskType(
        id=payload.id,
        name=payload.nazwa,
        team_id=payload.slownik_team_id,
        subteam_id=payload.slownik_subteam_id,
        requires_quantity=_tak(payload.czy_ilosciowy),
        requires_time=_tak(payload.czy_czasowy),
        requires_evaluation=_tak(payload.czy_ocena_wykonania),
        is_container=_tak(payload.czy_kontener),
        points=payload.punkty,
        description=payload.opis,
    )


def map_tag(payload: TagPayload) -> Tag:
    """Map a raw EMP tag payload to a Tag model."""
    return Tag(id=payload.id, name=payload.nazwa)

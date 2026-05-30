"""Rejestr mapper — Payload → Task model."""

from __future__ import annotations

from datetime import datetime

from mcp_emp.domains.rejestr.contract import (
    Permissions,
    RejestrDetailPayload,
    RejestrListItemPayload,
    Task,
    TaskTypeInfo,
)
from mcp_emp.domains.rejestr.status import STATUS_GLOSS, Status

_EMP_FMT = "%Y-%m-%d %H:%M:%S"


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, _EMP_FMT)
    except ValueError:
        return None


def _tak(value: str | None) -> bool:
    return (value or "").strip().lower() in ("tak", "1", "true")


def _status_explained(status: str) -> str:
    try:
        return STATUS_GLOSS.get(Status(status), status)
    except ValueError:
        return status


def _compute_permissions(status: str) -> Permissions:
    return Permissions(
        can_complete=status in (Status.REALIZOWANE, Status.DO_OCENY),
        can_delete=status == Status.W_EDYCJI,
        can_edit=status not in (Status.ZAKONCZONE, Status.ODRZUCONE, Status.WYCOFANE),
        can_start=status == Status.PRZYDZIELONE,
    )


def _full_name(imie: str | None, nazwisko: str | None) -> str | None:
    parts = [p for p in (imie, nazwisko) if p]
    return " ".join(parts) if parts else None


def map_task_from_list(p: RejestrListItemPayload) -> Task:
    """Map a list-endpoint payload row to a Task."""
    return Task(
        id=p.id,
        subject=p.dotyczy,
        status=p.status,
        status_explained=_status_explained(p.status),
        cycle=p.nr_cyklu,
        task_type=TaskTypeInfo(
            id=p.slownik_typ_zadania_id,
            name=p.slownik_typ_zadania_nazwa,
            requires_quantity=_tak(p.slownik_typ_zadania_czy_ilosciowy),
            requires_time=_tak(p.slownik_typ_zadania_czy_czasowy),
            requires_evaluation=_tak(p.slownik_typ_zadania_czy_ocena_wykonania),
        ),
        assigned_to=_full_name(p.assigned_user_imie, p.assigned_user_nazwisko),
        created_by=_full_name(p.created_user_imie, p.created_user_nazwisko),
        ordered_at=_dt(p.data_zlecenia),
        deadline=_dt(p.data_termin),
        started_at=_dt(p.data_rozpoczecia),
        completed_at=_dt(p.data_zakonczenia),
        quantity=p.ilosc,
        time=p.czas,
        points=p.punkty_pracownik,
        sod_number=p.nr_sprawy_sod,
        sod_letter=p.nr_pisma_sod,
        url=p.url,
        notes=p.uwagi,
        parent_id=p.rejestr_id,
        tags=p.tags if p.tags else [],       # list endpoint: tags are plain strings
        open_children=p.open_children_count or 0,
        permissions=None,
    )


def map_task_from_detail(p: RejestrDetailPayload) -> Task:
    """Map a detail-endpoint payload to a Task (includes permissions)."""
    return Task(
        id=p.id,
        subject=p.dotyczy,
        status=p.status,
        status_explained=_status_explained(p.status),
        cycle=p.nr_cyklu,
        task_type=TaskTypeInfo(
            id=p.slownik_typ_zadania_id,
            name=p.slownik_typ_zadania_nazwa,
            requires_quantity=_tak(p.slownik_typ_zadania_czy_ilosciowy),
            requires_time=_tak(p.slownik_typ_zadania_czy_czasowy),
            requires_evaluation=_tak(p.slownik_typ_zadania_czy_ocena_wykonania),
        ),
        assigned_to=None,
        created_by=None,
        ordered_at=_dt(p.data_zlecenia),
        deadline=_dt(p.data_termin),
        started_at=_dt(p.data_rozpoczecia),
        completed_at=_dt(p.data_zakonczenia),
        quantity=p.ilosc,
        time=p.czas,
        points=p.punkty_pracownik,
        sod_number=p.nr_sprawy_sod,
        sod_letter=p.nr_pisma_sod,
        url=p.url,
        notes=p.uwagi,
        parent_id=p.rejestr_id,
        tags=[t.nazwa for t in p.tags] if p.tags else [],  # detail: TagRef objects
        open_children=p.open_children_count or 0,
        permissions=_compute_permissions(p.status),
        rejection_reason=p.uzasadnienie_odrzucenia,
        correction_reason=p.uzasadnienie_poprawy,
    )

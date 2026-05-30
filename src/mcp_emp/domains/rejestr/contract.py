"""Rejestr contract — Payload and Model types for task CRUD.

Shapes confirmed from live EMP fixtures (tests/rejestr/).
List endpoint wraps in {"list": [...]}.
Single-task endpoint wraps in {"item": {...}, "status": "success"}.
"""

from __future__ import annotations

from pydantic import BaseModel

# ── Shared tag shape (appears in both list + detail) ─────────────────────────

class TagRef(BaseModel):
    """Tag reference embedded in a task."""

    id: int
    nazwa: str


# ── List payload (GET /rejestr/lista/moje and /moje-wszystkie) ────────────────

class RejestrListItemPayload(BaseModel):
    """One row from the list endpoints — joined fields included."""

    id: int
    created_user_id: int | None = None
    assigned_user_id: int | None = None
    data_zlecenia: str | None = None
    data_termin: str | None = None
    data_rozpoczecia: str | None = None
    data_gotowe: str | None = None
    data_do_oceny: str | None = None
    data_zakonczenia: str | None = None
    nr_cyklu: int | None = None
    slownik_typ_zadania_id: int | None = None
    slownik_typ_zadania_nazwa: str | None = None
    slownik_typ_zadania_czy_ilosciowy: str | None = None
    slownik_typ_zadania_czy_czasowy: str | None = None
    slownik_typ_zadania_czy_ocena_wykonania: str | None = None
    dotyczy: str | None = None
    punkty_domyslne: float | None = None
    punkty_przelozony: float | None = None
    punkty_pracownik: float | None = None
    waga: float | None = None
    punkty_wagi: float | None = None
    uwagi: str | None = None
    nr_sprawy_sod: str | None = None
    nr_pisma_sod: str | None = None
    url: str | None = None
    rodzaj_zadania: str | None = None
    rejestr_id: int | None = None
    status: str
    ilosc: float | None = None
    czas: str | None = None
    uzasadnienie_poprawy: str | None = None
    uzasadnienie_odrzucenia: str | None = None
    assigned_user_imie: str | None = None
    assigned_user_nazwisko: str | None = None
    assigned_user_slownik_unit_id: str | None = None
    assigned_user_slownik_team_id: str | None = None
    assigned_user_slownik_subteam_id: str | None = None
    assigned_user_symbol: int | None = None
    created_user_imie: str | None = None
    created_user_nazwisko: str | None = None
    data_przydzielenia: str | None = None
    liczba_przedluzen_terminu: int | None = None
    tags: list[str] | None = None
    open_children_count: int | None = None


class RejestrListPayload(BaseModel):
    """Wrapper returned by /rejestr/lista/* endpoints."""

    list: list[RejestrListItemPayload]


# ── Single-task payload (GET /rejestr/{id}) ───────────────────────────────────

class RejestrDetailPayload(BaseModel):
    """One full task from GET /rejestr/{id}."""

    id: int
    created_user_id: int | None = None
    assigned_user_id: int | None = None
    data_zlecenia: str | None = None
    data_termin: str | None = None
    data_rozpoczecia: str | None = None
    data_do_oceny: str | None = None
    data_zakonczenia: str | None = None
    nr_cyklu: int | None = None
    slownik_typ_zadania_id: int | None = None
    slownik_typ_zadania_nazwa: str | None = None
    slownik_typ_zadania_czy_ilosciowy: str | None = None
    slownik_typ_zadania_czy_czasowy: str | None = None
    slownik_typ_zadania_czy_ocena_wykonania: str | None = None
    slownik_typ_zadania_punkty: float | None = None
    slownik_typ_zadania_waga: float | None = None
    slownik_typ_zadania_opis: str | None = None
    dotyczy: str | None = None
    punkty_domyslne: float | None = None
    punkty_przelozony: float | None = None
    punkty_pracownik: float | None = None
    waga: float | None = None
    punkty_wagi: float | None = None
    uwagi: str | None = None
    nr_sprawy_sod: str | None = None
    nr_pisma_sod: str | None = None
    url: str | None = None
    rodzaj_zadania: str | None = None
    rejestr_id: int | None = None
    status: str
    ilosc: float | None = None
    czas: str | None = None
    uzasadnienie_poprawy: str | None = None
    uzasadnienie_odrzucenia: str | None = None
    liczba_przedluzen_terminu: int | None = None
    tags: list[TagRef] | None = None
    open_children_count: int | None = None


class RejestrDetailWrapperPayload(BaseModel):
    """Wrapper returned by GET /rejestr/{id}."""

    item: RejestrDetailPayload
    status: str


# ── MCP-facing models ─────────────────────────────────────────────────────────

class TaskTypeInfo(BaseModel):
    """Embedded task-type metadata on a Task."""

    id: int | None
    name: str | None
    requires_quantity: bool
    requires_time: bool
    requires_evaluation: bool


class Permissions(BaseModel):
    """What the current user is allowed to do with this task."""

    can_complete: bool
    can_delete: bool
    can_edit: bool
    can_start: bool


class Task(BaseModel):
    """MCP-facing task model — returned by list_my_tasks and get_task."""

    id: int
    subject: str | None
    status: str
    status_explained: str
    cycle: int | None
    task_type: TaskTypeInfo
    assigned_to: str | None
    created_by: str | None
    ordered_at: str | None  # ISO 8601
    deadline: str | None
    started_at: str | None
    completed_at: str | None
    quantity: float | None
    time: str | None
    points: float | None
    sod_number: str | None
    sod_letter: str | None
    url: str | None
    notes: str | None
    parent_id: int | None
    tags: list[str]
    open_children: int
    # detail-only (None in list context)
    permissions: Permissions | None = None
    rejection_reason: str | None = None
    correction_reason: str | None = None

"""Stat contract — Payload and Model types for statistics endpoints."""

from __future__ import annotations

from pydantic import BaseModel

# ── Cycle stats (/rejestr/stat/cykle) ────────────────────────────────────────

class CyclePointsPayload(BaseModel):
    nr_cyklu: int
    suma_domyslne: float | None = None
    suma_przelozony: float | None = None
    suma_pracownik: float | None = None


class CycleStatsPayload(BaseModel):
    cykle_zaspol_punkty: list[CyclePointsPayload] = []


class TeamCycleStatsPayload(BaseModel):
    """Richer payload from /rejestr/kierownik/stat/cykle."""
    cykle_zaspol_punkty: list[CyclePointsPayload] = []
    cykle_pracownicy_punkty_kier: list[dict[str, object]] = []
    cykle_liczba: list[dict[str, object]] = []
    cykle_liczba_zespol: list[dict[str, object]] = []
    cykle_tagi: list[dict[str, object]] = []
    current_user_symbol: int | None = None


class CyclePoints(BaseModel):
    cycle: int
    points_default: float | None
    points_manager: float | None
    points_employee: float | None


class CycleStats(BaseModel):
    cycles: list[CyclePoints]


class TeamCycleStats(BaseModel):
    """Kierownik-scoped cycle statistics."""
    cycles: list[CyclePoints]
    employee_points: list[dict[str, object]]
    task_counts: list[dict[str, object]]
    team_task_counts: list[dict[str, object]]
    tag_breakdown: list[dict[str, object]]


# ── Daily stats (/rejestr/stat/dzienny) ──────────────────────────────────────

class DailyTaskPayload(BaseModel):
    id: int
    slownik_typ_zadania_nazwa: str | None = None
    dotyczy: str | None = None
    data_rozpoczecia: str | None = None
    data_zakonczenia: str | None = None
    punkty: float | None = None
    rodzaj_zadania: str | None = None
    ilosc: float | None = None
    waga: float | None = None
    punkty_wagi: float | None = None
    czas: str | None = None
    nr_sprawy_sod: str | None = None
    tags: list[str] | None = None


class DailyStatsPayload(BaseModel):
    moje: list[DailyTaskPayload] = []


class DailyTask(BaseModel):
    id: int
    task_type: str | None
    subject: str | None
    started_at: str | None
    completed_at: str | None
    points: float | None
    points_weighted: float | None
    quantity: float | None
    time: str | None
    sod_number: str | None
    tags: list[str]


class DailyStats(BaseModel):
    date: str
    tasks: list[DailyTask]
    total_points: float
    total_tasks: int

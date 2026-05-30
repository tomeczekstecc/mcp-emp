"""Słowniki contract — Payload and Model types for reference data.

Shapes confirmed from live EMP fixtures (tests/slowniki/).
"""

from __future__ import annotations

from pydantic import BaseModel

# ── Task types ───────────────────────────────────────────────────────────────

class TaskTypePayload(BaseModel):
    """Raw EMP slownik_typ_zadania entry."""

    id: int
    nazwa: str
    punkty: float | None = None
    waga: float | None = None
    slownik_team_id: str | None = None
    slownik_subteam_id: str | None = None
    czy_ilosciowy: str | None = None    # "Tak" / "Nie" / null
    czy_czasowy: str | None = None      # "Tak" / "Nie" / null
    czy_ocena_wykonania: str | None = None
    czy_kontener: str | None = None
    opis: str | None = None


class TaskType(BaseModel):
    """MCP-facing task type."""

    id: int
    name: str
    team_id: str | None
    subteam_id: str | None
    requires_quantity: bool   # czy_ilosciowy == "Tak"
    requires_time: bool       # czy_czasowy == "Tak"
    requires_evaluation: bool # czy_ocena_wykonania == "Tak"
    is_container: bool        # czy_kontener == "Tak"
    points: float | None
    description: str | None


# ── Tags ─────────────────────────────────────────────────────────────────────

class TagPayload(BaseModel):
    """Raw EMP tag entry (both /tag and /tag/pelna-lista)."""

    id: int
    nazwa: str


class Tag(BaseModel):
    """MCP-facing tag."""

    id: int
    name: str


# ── List wrappers ─────────────────────────────────────────────────────────────

class SlownikListPayload(BaseModel):
    """EMP wraps slownik lists in {list: [...]}."""

    list: list[TaskTypePayload]


class TagListPayload(BaseModel):
    """EMP wraps tag lists in {list: [...]}."""

    list: list[TagPayload]

"""Uzytkownik contract — Payload and Model types."""

from __future__ import annotations

from pydantic import BaseModel

# ── Payloads ──────────────────────────────────────────────────────────────────

class UserProfilePayload(BaseModel):
    id: int
    name: str
    email: str | None = None
    imie: str | None = None
    nazwisko: str | None = None
    telefon: str | None = None
    unit: str | None = None
    team: str | None = None
    subteam: str | None = None


class UserProfileWrapperPayload(BaseModel):
    item: UserProfilePayload
    status: str


class UserPermissionsPayload(BaseModel):
    user_id: int
    czy_ma_subteams: str | None = None
    perms: list[str] = []


class UserListItemPayload(BaseModel):
    id: int
    name: str
    email: str | None = None
    imie: str | None = None
    nazwisko: str | None = None
    slownik_unit_id: str | None = None
    slownik_team_id: str | None = None
    slownik_subteam_id: str | None = None
    czy_manager: str | None = None
    symbol: int | None = None
    perms: list[str] = []


class UserListPayload(BaseModel):
    status: str
    count: int
    totalCount: int
    list: list[UserListItemPayload]


# ── Models ────────────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    """Current user's EMP profile."""

    id: int
    username: str
    email: str | None
    first_name: str | None
    last_name: str | None
    phone: str | None
    unit: str | None
    team: str | None
    subteam: str | None


class UserPermissions(BaseModel):
    """Current user's EMP permissions."""

    user_id: int
    has_subteams: bool
    permissions: list[str]


class EmpUser(BaseModel):
    """One user from the EMP user list."""

    id: int
    username: str
    email: str | None
    first_name: str | None
    last_name: str | None
    unit: str | None
    team: str | None
    subteam: str | None
    is_manager: bool
    symbol: int | None
    permissions: list[str]

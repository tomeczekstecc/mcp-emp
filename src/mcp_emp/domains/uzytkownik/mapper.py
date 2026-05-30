"""Uzytkownik mapper — Payload → Model."""

from __future__ import annotations

from mcp_emp.domains.uzytkownik.contract import (
    EmpUser,
    UserListItemPayload,
    UserPermissions,
    UserPermissionsPayload,
    UserProfile,
    UserProfilePayload,
)


def map_user_profile(p: UserProfilePayload) -> UserProfile:
    return UserProfile(
        id=p.id,
        username=p.name,
        email=p.email,
        first_name=p.imie,
        last_name=p.nazwisko,
        phone=p.telefon,
        unit=p.unit,
        team=p.team,
        subteam=p.subteam,
    )


def map_user_permissions(p: UserPermissionsPayload) -> UserPermissions:
    return UserPermissions(
        user_id=p.user_id,
        has_subteams=(p.czy_ma_subteams or "").strip().lower() == "tak",
        permissions=p.perms,
    )


def map_emp_user(p: UserListItemPayload) -> EmpUser:
    return EmpUser(
        id=p.id,
        username=p.name,
        email=p.email,
        first_name=p.imie,
        last_name=p.nazwisko,
        unit=p.slownik_unit_id,
        team=p.slownik_team_id,
        subteam=p.slownik_subteam_id,
        is_manager=(p.czy_manager or "").strip().lower() == "tak",
        symbol=p.symbol,
        permissions=p.perms,
    )

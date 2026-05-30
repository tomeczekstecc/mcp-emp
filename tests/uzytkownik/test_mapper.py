"""Tests for uzytkownik mapper."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_emp.domains.uzytkownik.contract import (
    UserListPayload,
    UserPermissionsPayload,
    UserProfileWrapperPayload,
)
from mcp_emp.domains.uzytkownik.mapper import (
    map_emp_user,
    map_user_permissions,
    map_user_profile,
)

FIXTURES = Path(__file__).parent


def test_my_profile_from_fixture() -> None:
    raw = json.loads((FIXTURES / "me.json").read_text(encoding="utf-8"))
    wrapper = UserProfileWrapperPayload.model_validate(raw)
    profile = map_user_profile(wrapper.item)
    assert profile.username == "stect"
    assert profile.unit == "CI"
    assert profile.team == "CI-PRS"
    assert profile.id == 3


def test_my_permissions_from_fixture() -> None:
    raw = json.loads((FIXTURES / "uprawnienia.json").read_text(encoding="utf-8"))
    perms = map_user_permissions(UserPermissionsPayload.model_validate(raw))
    assert perms.user_id == 3
    assert "rejestr_modyfikacja" in perms.permissions
    assert isinstance(perms.has_subteams, bool)


def test_user_list_from_fixture() -> None:
    raw = json.loads((FIXTURES / "lista.json").read_text(encoding="utf-8"))
    payload = UserListPayload.model_validate(raw)
    users = [map_emp_user(u) for u in payload.list]
    assert len(users) == 9
    assert all(u.username for u in users)
    assert all(isinstance(u.is_manager, bool) for u in users)

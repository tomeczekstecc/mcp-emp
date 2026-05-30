"""Uzytkownik async HTTP client."""

from __future__ import annotations

from mcp_emp.core.auth import get_auth
from mcp_emp.core.errors import EmpRejected
from mcp_emp.core.http import get_client
from mcp_emp.domains.uzytkownik.contract import (
    EmpUser,
    UserListPayload,
    UserPermissions,
    UserPermissionsPayload,
    UserProfile,
    UserProfileWrapperPayload,
)
from mcp_emp.domains.uzytkownik.mapper import (
    map_emp_user,
    map_user_permissions,
    map_user_profile,
)


async def _bearer() -> dict[str, str]:
    token = await get_auth().get_token()
    return {"Authorization": f"Bearer {token}"}


async def fetch_my_profile() -> UserProfile:
    r = await get_client().get("/uzytkownik/", headers=await _bearer())
    if r.status_code != 200:
        raise EmpRejected(f"EMP {r.status_code} on /uzytkownik/",
                          {"status_code": r.status_code})
    wrapper = UserProfileWrapperPayload.model_validate(r.json())
    return map_user_profile(wrapper.item)


async def fetch_my_permissions() -> UserPermissions:
    r = await get_client().get("/uzytkownik/uprawnienia", headers=await _bearer())
    if r.status_code != 200:
        raise EmpRejected(f"EMP {r.status_code} on /uzytkownik/uprawnienia",
                          {"status_code": r.status_code})
    return map_user_permissions(UserPermissionsPayload.model_validate(r.json()))


async def fetch_users() -> list[EmpUser]:
    r = await get_client().get("/uzytkownicy/", headers=await _bearer())
    if r.status_code != 200:
        raise EmpRejected(f"EMP {r.status_code} on /uzytkownicy/",
                          {"status_code": r.status_code})
    payload = UserListPayload.model_validate(r.json())
    return [map_emp_user(u) for u in payload.list]

"""Uzytkownik MCP tool registrations."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.modes import readable
from mcp_emp.domains.uzytkownik.client import (
    fetch_my_permissions,
    fetch_my_profile,
    fetch_users,
)
from mcp_emp.domains.uzytkownik.contract import EmpUser, UserPermissions, UserProfile


def register(server: FastMCP) -> None:
    """Register uzytkownik tools on *server*."""

    @server.tool()
    @readable
    async def get_my_profile() -> UserProfile:
        """Get my EMP user profile (name, email, unit, team).

        Returns the profile of the currently authenticated EMP user.
        """
        return await fetch_my_profile()

    @server.tool()
    @readable
    async def get_my_permissions() -> UserPermissions:
        """Get my EMP permissions list.

        Returns the list of EMP permission strings the current user holds,
        e.g. 'rejestr_modyfikacja', 'kierownik_podglad'.
        """
        return await fetch_my_permissions()

    @server.tool()
    @readable
    async def list_users(
        search: str = "",
        team_id: str = "",
    ) -> list[EmpUser]:
        """List all EMP users visible to me.

        Requires the 'uzytkownicy_podglad' permission. Returns an empty list
        if the current user lacks that permission (rather than raising).

        Args:
            search:  Substring filter on username, first or last name.
            team_id: Filter by team ID (e.g. 'CI-PRS').
        """
        try:
            users = await fetch_users()
        except Exception:  # noqa: BLE001
            return []

        if search:
            q = search.casefold()
            users = [
                u for u in users
                if q in (u.username or "").casefold()
                or q in (u.first_name or "").casefold()
                or q in (u.last_name or "").casefold()
            ]
        if team_id:
            users = [u for u in users if u.team == team_id]

        return sorted(users, key=lambda u: u.username)

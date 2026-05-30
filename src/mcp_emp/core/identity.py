"""Identity — current user and roles derived from the Keycloak token.

Parsed once after login and cached for the process lifetime.
`unit` and `team` fall back to MCP_EMP_KC_UNIT / MCP_EMP_KC_TEAM when the
JWT access token does not carry those claims (KC mapper not configured).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import jwt as pyjwt


@dataclass
class Identity:
    """Current user identity, derived from the KC access token claims."""

    user_id: str
    username: str
    display_name: str
    email: str
    roles: list[str] = field(default_factory=list)
    unit: str = ""   # e.g. "CI"
    team: str = ""   # e.g. "CI-PRS"

    def has_role(self, role: str) -> bool:
        """Return True when the user holds *role*."""
        return role in self.roles


_identity: Identity | None = None


def parse_identity(
    access_token: str,
    realm_name: str,
    *,
    fallback_unit: str = "",
    fallback_team: str = "",
) -> Identity:
    """Decode *access_token* and extract identity claims.

    `fallback_unit` / `fallback_team` are used when the token does not carry
    those claims (KC mapper not configured on the API client).
    """
    claims = pyjwt.decode(
        access_token,
        options={"verify_signature": False},
        algorithms=["RS256"],
    )
    resource_access: dict[str, dict[str, list[str]]] = claims.get("resource_access", {})
    roles: list[str] = (
        resource_access.get(realm_name, {}).get("roles", [])
        or resource_access.get("eMP", {}).get("roles", [])
        or claims.get("realm_access", {}).get("roles", [])
    )
    return Identity(
        user_id=claims.get("sub", ""),
        username=claims.get("preferred_username", ""),
        display_name=claims.get("name", ""),
        email=claims.get("email", ""),
        roles=roles,
        unit=claims.get("unit", "") or fallback_unit,
        team=claims.get("team", "") or fallback_team,
    )


def get_identity() -> Identity:
    """Return the process-wide Identity singleton."""
    if _identity is None:
        raise RuntimeError("Identity has not been initialised (lifespan not started)")
    return _identity


def _set_identity(identity: Identity) -> None:
    """Set the singleton — called from lifespan only (and tests)."""
    global _identity
    _identity = identity

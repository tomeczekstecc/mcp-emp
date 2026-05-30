"""Identity — current user and roles derived from the Keycloak token.

Parsed once after login and cached for the process lifetime.
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

    def has_role(self, role: str) -> bool:
        """Return True when the user holds *role*."""
        return role in self.roles


_identity: Identity | None = None


def parse_identity(access_token: str, realm_name: str) -> Identity:
    """Decode *access_token* without verification and extract identity claims.

    KC tokens are signed; for local dev we skip verification.  In production,
    pass the KC public key here.
    """
    claims = pyjwt.decode(
        access_token,
        options={"verify_signature": False},
        algorithms=["RS256"],
    )
    resource_access: dict[str, dict[str, list[str]]] = claims.get("resource_access", {})
    # Prefer roles from the specific client resource, fall back to realm roles
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

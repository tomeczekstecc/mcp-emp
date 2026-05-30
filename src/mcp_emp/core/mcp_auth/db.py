"""SQLite database for MCP API-key auth.

Schema:
  users(id, username UNIQUE, api_key_hash, api_key_prefix,
        is_superuser, created_at, active)
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_key(username: str) -> str:
    """Generate a new API key: emp_<username>_<32 hex chars>."""
    return f"emp_{username}_{secrets.token_hex(16)}"


@dataclass
class AuthUser:
    id: int
    username: str
    api_key_prefix: str   # first 8 chars of key (for display)
    is_superuser: bool
    created_at: str
    active: bool


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            api_key_hash  TEXT NOT NULL,
    api_key_prefix TEXT NOT NULL,  -- first 12 chars + '...' suffix
            is_superuser  INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT NOT NULL,
            active        INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.commit()
    return conn


def add_user(
    conn: sqlite3.Connection,
    username: str,
    *,
    superuser: bool = False,
) -> str:
    """Create a user and return the plaintext API key (shown once)."""
    key = generate_key(username)
    conn.execute(
        """INSERT INTO users (username, api_key_hash, api_key_prefix, is_superuser, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (username, _hash(key), key[:12] + "...", int(superuser), _now()),
    )
    conn.commit()
    return key


def delete_user(conn: sqlite3.Connection, username: str) -> bool:
    cur = conn.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    return cur.rowcount > 0


def revoke_key(conn: sqlite3.Connection, username: str) -> str | None:
    """Regenerate the API key for *username*. Returns the new key or None."""
    key = generate_key(username)
    cur = conn.execute(
        "UPDATE users SET api_key_hash=?, api_key_prefix=? WHERE username=?",
        (_hash(key), key[:12] + "...", username),
    )
    conn.commit()
    return key if cur.rowcount > 0 else None


def list_users(conn: sqlite3.Connection) -> list[AuthUser]:
    rows = conn.execute(
        "SELECT id, username, api_key_prefix, is_superuser, created_at, active "
        "FROM users ORDER BY username"
    ).fetchall()
    return [
        AuthUser(
            id=r["id"],
            username=r["username"],
            api_key_prefix=r["api_key_prefix"],
            is_superuser=bool(r["is_superuser"]),
            created_at=r["created_at"],
            active=bool(r["active"]),
        )
        for r in rows
    ]


def verify_key(conn: sqlite3.Connection, key: str) -> AuthUser | None:
    """Return the AuthUser for *key*, or None if invalid/inactive."""
    row = conn.execute(
        "SELECT id, username, api_key_prefix, is_superuser, created_at, active "
        "FROM users WHERE api_key_hash=? AND active=1",
        (_hash(key),),
    ).fetchone()
    if row is None:
        return None
    return AuthUser(
        id=row["id"],
        username=row["username"],
        api_key_prefix=row["api_key_prefix"],
        is_superuser=bool(row["is_superuser"]),
        created_at=row["created_at"],
        active=bool(row["active"]),
    )


def has_any_user(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None

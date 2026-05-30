"""Tests for MCP auth DB — user/key lifecycle."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from mcp_emp.core.mcp_auth.db import (
    add_user,
    delete_user,
    generate_key,
    has_any_user,
    list_users,
    open_db,
    revoke_key,
    verify_key,
)


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    with tempfile.TemporaryDirectory() as tmp:
        conn = open_db(Path(tmp) / "test_auth.db")
        yield conn
        conn.close()


def test_generate_key_format() -> None:
    key = generate_key("tomasz")
    assert key.startswith("emp_tomasz_")
    assert len(key) == len("emp_tomasz_") + 32


def test_add_and_verify_user(db) -> None:  # type: ignore[no-untyped-def]
    key = add_user(db, "alice")
    user = verify_key(db, key)
    assert user is not None
    assert user.username == "alice"
    assert not user.is_superuser


def test_add_superuser(db) -> None:  # type: ignore[no-untyped-def]
    key = add_user(db, "admin", superuser=True)
    user = verify_key(db, key)
    assert user is not None
    assert user.is_superuser


def test_invalid_key_returns_none(db) -> None:  # type: ignore[no-untyped-def]
    assert verify_key(db, "emp_nobody_0000000000000000000000000000000000") is None


def test_delete_user(db) -> None:  # type: ignore[no-untyped-def]
    key = add_user(db, "bob")
    assert delete_user(db, "bob") is True
    assert verify_key(db, key) is None


def test_delete_nonexistent_user(db) -> None:  # type: ignore[no-untyped-def]
    assert delete_user(db, "ghost") is False


def test_revoke_key(db) -> None:  # type: ignore[no-untyped-def]
    old_key = add_user(db, "carol")
    new_key = revoke_key(db, "carol")
    assert new_key is not None
    assert new_key != old_key
    assert verify_key(db, old_key) is None     # old key invalid
    assert verify_key(db, new_key) is not None  # new key valid


def test_revoke_nonexistent_returns_none(db) -> None:  # type: ignore[no-untyped-def]
    assert revoke_key(db, "nobody") is None


def test_list_users(db) -> None:  # type: ignore[no-untyped-def]
    add_user(db, "alice")
    add_user(db, "bob", superuser=True)
    users = list_users(db)
    names = [u.username for u in users]
    assert "alice" in names
    assert "bob" in names
    bob = next(u for u in users if u.username == "bob")
    assert bob.is_superuser


def test_has_any_user(db) -> None:  # type: ignore[no-untyped-def]
    assert not has_any_user(db)
    add_user(db, "first")
    assert has_any_user(db)


def test_key_prefix_in_listing(db) -> None:  # type: ignore[no-untyped-def]
    add_user(db, "dave")
    users = list_users(db)
    dave = next(u for u in users if u.username == "dave")
    assert dave.api_key_prefix.startswith("emp_dave_")
    assert "..." in dave.api_key_prefix  # truncated

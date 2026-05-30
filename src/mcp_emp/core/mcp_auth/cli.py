"""CLI for MCP API-key auth management.

Usage:
    mcp-emp auth init
    mcp-emp auth add-user <username> [--superuser]
    mcp-emp auth delete-user <username>
    mcp-emp auth revoke-key <username>
    mcp-emp auth list-users
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _get_db_path() -> Path:
    from mcp_emp.core.config import get_settings  # noqa: PLC0415

    try:
        s = get_settings()
        return Path(s.auth_db_path).expanduser()
    except Exception:  # noqa: BLE001
        return Path("~/.mcp_emp/auth.db").expanduser()


def cmd_init(args: argparse.Namespace) -> None:
    from mcp_emp.core.mcp_auth.db import has_any_user, open_db  # noqa: PLC0415

    conn = open_db(_get_db_path())
    if has_any_user(conn):
        print("Auth DB already initialised.")
    else:
        print(f"Auth DB initialised at {_get_db_path()}")
        print("Add a superuser with:  mcp-emp auth add-user <name> --superuser")


def cmd_add_user(args: argparse.Namespace) -> None:
    from mcp_emp.core.mcp_auth.db import add_user, list_users, open_db  # noqa: PLC0415

    conn = open_db(_get_db_path())
    users = list_users(conn)

    # only superusers may add users; first user is exempt (bootstrapping)
    if users and not args.force and not any(u.is_superuser for u in users):
        print("ERROR: no superuser exists yet. Use --force to bootstrap.")
        sys.exit(1)

    try:
        key = add_user(conn, args.username, superuser=args.superuser)
        role = "superuser" if args.superuser else "user"
        print(f"Created {role} '{args.username}'.")
        print(f"API key (shown once): {key}")
        print("Store this key securely — it cannot be retrieved again.")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_delete_user(args: argparse.Namespace) -> None:
    from mcp_emp.core.mcp_auth.db import delete_user, open_db  # noqa: PLC0415

    conn = open_db(_get_db_path())
    if delete_user(conn, args.username):
        print(f"Deleted user '{args.username}'.")
    else:
        print(f"User '{args.username}' not found.")
        sys.exit(1)


def cmd_revoke_key(args: argparse.Namespace) -> None:
    from mcp_emp.core.mcp_auth.db import open_db, revoke_key  # noqa: PLC0415

    conn = open_db(_get_db_path())
    key = revoke_key(conn, args.username)
    if key:
        print(f"New API key for '{args.username}' (shown once): {key}")
    else:
        print(f"User '{args.username}' not found.")
        sys.exit(1)


def cmd_list_users(args: argparse.Namespace) -> None:
    from mcp_emp.core.mcp_auth.db import list_users, open_db  # noqa: PLC0415

    conn = open_db(_get_db_path())
    users = list_users(conn)
    if not users:
        print("No users registered.")
        return
    print(f"{'USERNAME':<20} {'ROLE':<12} {'KEY PREFIX':<16} {'ACTIVE':<8} CREATED")
    print("-" * 75)
    for u in users:
        role = "superuser" if u.is_superuser else "user"
        active = "yes" if u.active else "no"
        print(f"{u.username:<20} {role:<12} {u.api_key_prefix:<16} {active:<8} {u.created_at[:19]}")


def run_auth_cli(argv: list[str]) -> None:
    """Entry point for `mcp-emp auth <subcommand>`."""
    parser = argparse.ArgumentParser(prog="mcp-emp auth",
                                     description="Manage MCP API-key authentication")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialise the auth database")

    p_add = sub.add_parser("add-user", help="Create a user and generate an API key")
    p_add.add_argument("username")
    p_add.add_argument("--superuser", action="store_true",
                       help="Grant superuser privileges")
    p_add.add_argument("--force", action="store_true",
                       help="Allow creation even without an existing superuser")

    p_del = sub.add_parser("delete-user", help="Remove a user")
    p_del.add_argument("username")

    p_rev = sub.add_parser("revoke-key", help="Regenerate a user's API key")
    p_rev.add_argument("username")

    sub.add_parser("list-users", help="List all registered users")

    args = parser.parse_args(argv)
    handlers = {
        "init": cmd_init,
        "add-user": cmd_add_user,
        "delete-user": cmd_delete_user,
        "revoke-key": cmd_revoke_key,
        "list-users": cmd_list_users,
    }
    handlers[args.command](args)

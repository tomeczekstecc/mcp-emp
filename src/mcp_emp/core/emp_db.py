"""Direct EMP PostgreSQL access — for operations not available via the API.

Used only for date backdating (setting data_zlecenia, data_zakonczenia, etc.)
on tasks that have already been created/completed through the API.

Connection is created on demand and closed after each operation.
Credentials come from MCP_EMP_DB_* env vars.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg


def _clean_host(host: str) -> str:
    """Strip http:// or https:// scheme prefix from host."""
    return re.sub(r"^https?://", "", host).rstrip("/")


@asynccontextmanager
async def emp_db_connection() -> AsyncIterator[asyncpg.Connection]:
    """Open a short-lived connection to the EMP PostgreSQL database."""
    from mcp_emp.core.config import get_settings  # noqa: PLC0415

    s = get_settings()
    if not s.db_host or not s.db_user or not s.db_database:
        raise RuntimeError(
            "EMP DB not configured. Set MCP_EMP_DB_HOST, MCP_EMP_DB_USER, "
            "MCP_EMP_DB_PASS and MCP_EMP_DB_DATABASE."
        )

    host = _clean_host(s.db_host)
    conn: asyncpg.Connection = await asyncpg.connect(
        host=host,
        port=s.db_port,
        user=s.db_user,
        password=s.db_pass.get_secret_value(),
        database=s.db_database,
        ssl="disable",  # EMP DB does not use SSL (scheme in host is cosmetic)
        timeout=10,
    )
    try:
        yield conn
    finally:
        await conn.close()


async def backdate_rejestr(
    task_id: int,
    target_date: str,
    *,
    set_zakonczenia: bool = False,
) -> dict[str, str | None]:
    """Directly update date fields on a rejestr row.

    Sets:
    - data_zlecenia      (order date — used for monthly attribution)
    - data_rozpoczecia   (start date)
    - data_gotowe        (ready date)
    - data_przydzielenia (assignment date)
    - data_zakonczenia   (completion date) — only when set_zakonczenia=True

    Returns the updated row's date fields for confirmation.
    """
    from datetime import datetime as _dt  # noqa: PLC0415

    # Normalise: accept ISO 8601 or YYYY-MM-DD, convert to Python datetime
    dt_str = target_date.replace("T", " ").replace("+00:00", "")[:19]
    if len(dt_str) == 10:  # date only
        dt_str = dt_str + " 00:00:00"
    dt_obj = _dt.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

    cols = [
        "data_zlecenia",
        "data_rozpoczecia",
        "data_gotowe",
        "data_przydzielenia",
    ]
    if set_zakonczenia:
        cols.append("data_zakonczenia")

    # Each param needs a unique $N — asyncpg requires this
    params = [dt_obj] * len(cols) + [task_id]
    set_clause = ", ".join(f"{c} = ${i + 1}" for i, c in enumerate(cols))
    sql = f"UPDATE rejestr SET {set_clause} WHERE id = ${len(cols) + 1}"

    async with emp_db_connection() as conn:
        result = await conn.execute(sql, *params)
        # Fetch confirmation
        row = await conn.fetchrow(
            "SELECT id, data_zlecenia, data_rozpoczecia, data_zakonczenia, "
            "status, nr_cyklu FROM rejestr WHERE id = $1",
            task_id,
        )

    if not row:
        raise ValueError(f"Task {task_id} not found in EMP database")

    return {
        "task_id": str(row["id"]),
        "data_zlecenia": str(row["data_zlecenia"]) if row["data_zlecenia"] else None,
        "data_zakonczenia": str(row["data_zakonczenia"]) if row["data_zakonczenia"] else None,
        "status": str(row["status"]),
        "nr_cyklu": str(row["nr_cyklu"]) if row["nr_cyklu"] else None,
        "rows_updated": result.split()[-1],  # "UPDATE N"
    }

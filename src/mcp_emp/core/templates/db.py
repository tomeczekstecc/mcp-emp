"""SQLite-backed task template store."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class TaskTemplate:
    id: int
    name: str
    task_type_id: int
    subject_template: str | None
    notes_template: str | None
    deadline_offset_days: int | None
    tag_ids: list[int]
    created_at: str
    updated_at: str

    def render(
        self,
        subject_override: str | None = None,
        notes_override: str | None = None,
        deadline_override: str | None = None,
        cycle: int | None = None,
    ) -> dict[str, object]:
        """Return a dict suitable for passing to create_my_task."""
        today = date.today().isoformat()
        ctx: dict[str, str] = {
            "date": today,
            "today": today,
            "cycle": str(cycle or ""),
        }

        def _fill(tmpl: str | None) -> str | None:
            if not tmpl:
                return None
            try:
                return tmpl.format(**ctx)
            except KeyError:
                return tmpl

        subject = subject_override or _fill(self.subject_template)
        notes = notes_override or _fill(self.notes_template)
        deadline: str | None = deadline_override
        if not deadline and self.deadline_offset_days is not None:
            dl = date.today() + timedelta(days=self.deadline_offset_days)
            deadline = dl.isoformat()

        return {
            "task_type_id": self.task_type_id,
            "subject": subject,
            "notes": notes,
            "deadline": deadline,
            "tag_ids": self.tag_ids or None,
        }


def open_templates_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            name                 TEXT UNIQUE NOT NULL,
            task_type_id         INTEGER NOT NULL,
            subject_template     TEXT,
            notes_template       TEXT,
            deadline_offset_days INTEGER,
            tag_ids              TEXT NOT NULL DEFAULT '[]',
            created_at           TEXT NOT NULL,
            updated_at           TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def _row_to_template(row: sqlite3.Row) -> TaskTemplate:
    return TaskTemplate(
        id=row["id"],
        name=row["name"],
        task_type_id=row["task_type_id"],
        subject_template=row["subject_template"],
        notes_template=row["notes_template"],
        deadline_offset_days=row["deadline_offset_days"],
        tag_ids=json.loads(row["tag_ids"] or "[]"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def add_template(
    conn: sqlite3.Connection,
    name: str,
    task_type_id: int,
    *,
    subject_template: str | None = None,
    notes_template: str | None = None,
    deadline_offset_days: int | None = None,
    tag_ids: list[int] | None = None,
) -> TaskTemplate:
    now = _now()
    conn.execute(
        """INSERT INTO templates
           (name, task_type_id, subject_template, notes_template,
            deadline_offset_days, tag_ids, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, task_type_id, subject_template, notes_template,
         deadline_offset_days, json.dumps(tag_ids or []), now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM templates WHERE name=?", (name,)).fetchone()
    return _row_to_template(row)


def get_template(conn: sqlite3.Connection, name: str) -> TaskTemplate | None:
    row = conn.execute("SELECT * FROM templates WHERE name=?", (name,)).fetchone()
    return _row_to_template(row) if row else None


def list_templates(
    conn: sqlite3.Connection, search: str = ""
) -> list[TaskTemplate]:
    if search:
        rows = conn.execute(
            "SELECT * FROM templates WHERE name LIKE ? ORDER BY name",
            (f"%{search}%",),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM templates ORDER BY name").fetchall()
    return [_row_to_template(r) for r in rows]


def delete_template(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute("DELETE FROM templates WHERE name=?", (name,))
    conn.commit()
    return cur.rowcount > 0

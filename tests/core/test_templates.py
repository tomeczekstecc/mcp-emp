"""Tests for task templates (SQLite store + CLI)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from mcp_emp.core.templates.db import (
    add_template,
    delete_template,
    get_template,
    list_templates,
    open_templates_db,
)


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    with tempfile.TemporaryDirectory() as tmp:
        conn = open_templates_db(Path(tmp) / "test_templates.db")
        yield conn
        conn.close()


def test_add_and_get(db) -> None:  # type: ignore[no-untyped-def]
    t = add_template(db, "daily_standup", 28, subject_template="Standup {today}")
    assert t.name == "daily_standup"
    assert t.task_type_id == 28
    assert t.subject_template == "Standup {today}"

    fetched = get_template(db, "daily_standup")
    assert fetched is not None
    assert fetched.name == "daily_standup"


def test_get_missing_returns_none(db) -> None:  # type: ignore[no-untyped-def]
    assert get_template(db, "nonexistent") is None


def test_list_templates(db) -> None:  # type: ignore[no-untyped-def]
    add_template(db, "alpha", 1)
    add_template(db, "beta", 2)
    templates = list_templates(db)
    names = [t.name for t in templates]
    assert "alpha" in names
    assert "beta" in names
    assert names == sorted(names)  # sorted by name


def test_list_templates_search(db) -> None:  # type: ignore[no-untyped-def]
    add_template(db, "standup_daily", 28)
    add_template(db, "report_weekly", 5)
    results = list_templates(db, search="standup")
    assert len(results) == 1
    assert results[0].name == "standup_daily"


def test_delete_template(db) -> None:  # type: ignore[no-untyped-def]
    add_template(db, "to_delete", 1)
    assert delete_template(db, "to_delete") is True
    assert get_template(db, "to_delete") is None


def test_delete_missing_returns_false(db) -> None:  # type: ignore[no-untyped-def]
    assert delete_template(db, "ghost") is False


def test_render_date_placeholder(db) -> None:  # type: ignore[no-untyped-def]
    from datetime import date  # noqa: PLC0415

    t = add_template(db, "dated", 28, subject_template="Report {today}")
    rendered = t.render()
    today = date.today().isoformat()
    assert rendered["subject"] == f"Report {today}"


def test_render_deadline_offset(db) -> None:  # type: ignore[no-untyped-def]
    from datetime import date, timedelta  # noqa: PLC0415

    t = add_template(db, "deadline_test", 28, deadline_offset_days=7)
    rendered = t.render()
    expected = (date.today() + timedelta(days=7)).isoformat()
    assert rendered["deadline"] == expected


def test_render_override_subject(db) -> None:  # type: ignore[no-untyped-def]
    t = add_template(db, "override_test", 28, subject_template="Default subject")
    rendered = t.render(subject_override="Custom subject")
    assert rendered["subject"] == "Custom subject"


def test_render_tag_ids(db) -> None:  # type: ignore[no-untyped-def]
    t = add_template(db, "tagged", 28, tag_ids=[1, 5, 8])
    rendered = t.render()
    assert rendered["tag_ids"] == [1, 5, 8]


def test_duplicate_name_raises(db) -> None:  # type: ignore[no-untyped-def]
    add_template(db, "unique", 1)
    with pytest.raises(Exception, match="UNIQUE"):  # sqlite UNIQUE constraint
        add_template(db, "unique", 2)

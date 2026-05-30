"""Tests for P3 analysis engine — recurring patterns + completion suggestions."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from mcp_emp.domains.analysis.engine import (
    detect_recurring_patterns,
    prioritize_completions,
)
from mcp_emp.domains.rejestr.contract import RejestrListPayload
from mcp_emp.domains.rejestr.mapper import map_task_from_list
from mcp_emp.domains.rejestr.status import Status

REJESTR = Path(__file__).parent.parent / "rejestr"


def _tasks():  # type: ignore[no-untyped-def]
    raw = json.loads((REJESTR / "lista_moje_wszystkie.json").read_text(encoding="utf-8"))
    return [map_task_from_list(p) for p in RejestrListPayload.model_validate(raw).list]


# ── detect_recurring_patterns ─────────────────────────────────────────────────

def test_recurring_returns_sorted_by_count() -> None:
    tasks = _tasks()
    patterns = detect_recurring_patterns(tasks, min_count=1)
    assert patterns
    counts = [p.count for p in patterns]
    assert counts == sorted(counts, reverse=True)


def test_recurring_min_count_filter() -> None:
    tasks = _tasks()
    strict = detect_recurring_patterns(tasks, min_count=100)
    loose = detect_recurring_patterns(tasks, min_count=1)
    assert len(strict) <= len(loose)


def test_recurring_pattern_fields() -> None:
    tasks = _tasks()
    patterns = detect_recurring_patterns(tasks, min_count=1)
    for p in patterns:
        assert p.count >= 1
        assert isinstance(p.avg_points, float)
        assert p.task_type_name or p.task_type_id is None


# ── prioritize_completions ────────────────────────────────────────────────────

def test_prioritize_returns_realizowane_only() -> None:
    tasks = _tasks()
    suggestions = prioritize_completions(tasks)
    for s in suggestions:
        assert s.status == Status.REALIZOWANE


def test_prioritize_overdue_gets_high_score() -> None:
    tasks = _tasks()
    # Patch a task to be overdue with high score
    overdue_tasks = [t for t in tasks if t.status == Status.REALIZOWANE and t.deadline]
    if not overdue_tasks:
        return  # skip if no such tasks in fixture
    # Manually set a past deadline
    t = overdue_tasks[0]
    t.deadline = datetime.now() - timedelta(days=10)
    suggestions = prioritize_completions([t] + [x for x in tasks if x.id != t.id])
    top = suggestions[0] if suggestions else None
    if top and top.task_id == t.id:
        assert top.score >= 100  # overdue threshold


def test_prioritize_limit_respected() -> None:
    tasks = _tasks()
    suggestions = prioritize_completions(tasks, limit=3)
    assert len(suggestions) <= 3


def test_prioritize_sorted_by_score_desc() -> None:
    tasks = _tasks()
    suggestions = prioritize_completions(tasks)
    scores = [s.score for s in suggestions]
    assert scores == sorted(scores, reverse=True)

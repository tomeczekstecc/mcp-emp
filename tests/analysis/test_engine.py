"""Tests for analysis engine — work context, problem detection, tag suggestion, type stats."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from mcp_emp.domains.analysis.engine import (
    build_work_context,
    compute_task_type_stats,
    detect_problems,
    suggest_tags,
)
from mcp_emp.domains.rejestr.contract import RejestrListPayload
from mcp_emp.domains.rejestr.mapper import map_task_from_list
from mcp_emp.domains.rejestr.status import Status
from mcp_emp.domains.slowniki.contract import TagListPayload
from mcp_emp.domains.slowniki.mapper import map_tag

REJESTR = Path(__file__).parent.parent / "rejestr"
SLOWNIKI = Path(__file__).parent.parent / "slowniki"


def _tasks():  # type: ignore[no-untyped-def]
    raw = json.loads((REJESTR / "lista_moje_wszystkie.json").read_text(encoding="utf-8"))
    return [map_task_from_list(p) for p in RejestrListPayload.model_validate(raw).list]


def _tags():  # type: ignore[no-untyped-def]
    raw = json.loads((SLOWNIKI / "tag_pelna.json").read_text(encoding="utf-8"))
    return [map_tag(p) for p in TagListPayload.model_validate(raw).list]


# ── WorkContext ───────────────────────────────────────────────────────────────

def test_work_context_structure() -> None:
    tasks = _tasks()
    ctx = build_work_context(tasks, [])
    assert isinstance(ctx.in_progress, list)
    assert isinstance(ctx.overdue, list)
    assert isinstance(ctx.upcoming_deadlines, list)
    assert isinstance(ctx.summary, str)
    assert ctx.summary  # non-empty
    assert ctx.as_of  # ISO timestamp


def test_work_context_status_categorisation() -> None:
    tasks = _tasks()
    ctx = build_work_context(tasks, [])
    for t in ctx.in_progress:
        assert t.status == Status.REALIZOWANE
    for t in ctx.pending_review:
        assert t.status == Status.DO_OCENY
    for t in ctx.waiting:
        assert t.status == Status.OCZEKUJACE


def test_work_context_overdue_all_past_deadline() -> None:
    tasks = _tasks()
    ctx = build_work_context(tasks, [])
    today = date.today()
    for t in ctx.overdue:
        if t.deadline:
            dl = t.deadline.date() if isinstance(t.deadline, datetime) else t.deadline
            assert dl < today


# ── ProblemReport ─────────────────────────────────────────────────────────────

def test_detect_problems_returns_report() -> None:
    tasks = _tasks()
    report = detect_problems(tasks)
    assert report.checked_tasks == len(tasks)
    assert report.total_problems == len(report.problems)
    assert isinstance(report.note, str)


def test_detect_problems_severity_order() -> None:
    tasks = _tasks()
    report = detect_problems(tasks)
    severities = [p.severity for p in report.problems]
    order = {"high": 0, "medium": 1, "low": 2}
    sorted_sev = sorted(severities, key=lambda s: order.get(s, 9))
    assert severities == sorted_sev  # high before medium


def test_detect_problems_completed_tasks_skipped() -> None:
    tasks = _tasks()
    report = detect_problems(tasks)
    completed_ids = {t.id for t in tasks if t.status == Status.ZAKONCZONE}
    problem_ids = {p.task_id for p in report.problems}
    # No completed task should appear as a problem
    assert not (completed_ids & problem_ids)


def test_detect_problems_stalled_threshold() -> None:
    """With stalled_days=1, nearly all REALIZOWANE tasks are stalled."""
    tasks = _tasks()
    report_strict = detect_problems(tasks, stalled_days=1)
    report_loose = detect_problems(tasks, stalled_days=365)
    stalled_strict = [p for p in report_strict.problems if p.problem_type == "stalled"]
    stalled_loose = [p for p in report_loose.problems if p.problem_type == "stalled"]
    assert len(stalled_strict) >= len(stalled_loose)


# ── TagSuggestion ─────────────────────────────────────────────────────────────

def test_suggest_tags_returns_list() -> None:
    tasks = _tasks()
    tags = _tags()
    suggestions = suggest_tags("eDrogi eksport raport", tasks, tags)
    assert isinstance(suggestions, list)
    for s in suggestions:
        assert 0.0 <= s.relevance_score <= 1.0
        assert s.name
        assert s.id > 0


def test_suggest_tags_empty_subject() -> None:
    tasks = _tasks()
    tags = _tags()
    assert suggest_tags("", tasks, tags) == []


def test_suggest_tags_no_match() -> None:
    tasks = _tasks()
    tags = _tags()
    # Very unlikely to match anything
    result = suggest_tags("xyzzy_completely_unique_subject_99999", tasks, tags)
    assert result == []


def test_suggest_tags_top_n_respected() -> None:
    tasks = _tasks()
    tags = _tags()
    result = suggest_tags("eDrogi zmiana", tasks, tags, top_n=2)
    assert len(result) <= 2


# ── TaskTypeStats ─────────────────────────────────────────────────────────────

def test_task_type_stats_structure() -> None:
    tasks = _tasks()
    stats = compute_task_type_stats(tasks, days=365)
    assert stats.total_tasks > 0
    assert len(stats.task_types) > 0
    assert all(ts.count > 0 for ts in stats.task_types)
    # sorted by frequency descending
    counts = [ts.count for ts in stats.task_types]
    assert counts == sorted(counts, reverse=True)


def test_task_type_stats_days_filter() -> None:
    tasks = _tasks()
    wide = compute_task_type_stats(tasks, days=9999)
    narrow = compute_task_type_stats(tasks, days=1)
    assert wide.total_tasks >= narrow.total_tasks


def test_task_type_stats_points_consistent() -> None:
    tasks = _tasks()
    stats = compute_task_type_stats(tasks, days=365)
    for ts in stats.task_types:
        assert ts.total_points >= 0
        assert ts.completed + ts.in_progress <= ts.count
        if ts.count > 0:
            assert abs(ts.avg_points - ts.total_points / ts.count) < 0.01

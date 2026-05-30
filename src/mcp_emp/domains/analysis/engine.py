"""Analysis engine — local computation functions for smart-assistance tools.

No HTTP calls here. All inputs come from other domain clients.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from mcp_emp.domains.analysis.contract import (
    Problem,
    ProblemReport,
    TagSuggestion,
    TaskTypeStat,
    TaskTypeStats,
    WorkContext,
)
from mcp_emp.domains.rejestr.contract import Task
from mcp_emp.domains.rejestr.status import Status
from mcp_emp.domains.slowniki.contract import Tag
from mcp_emp.domains.stat.contract import DailyTask

_STALLED_DAYS = 14   # REALIZOWANE without completion for > N days = stalled


# ── WorkContext ───────────────────────────────────────────────────────────────

def build_work_context(
    tasks: list[Task],
    today_tasks: list[DailyTask],
    *,
    lookahead_days: int = 7,
) -> WorkContext:
    """Derive a WorkContext from the full task list + today's stats."""
    now = datetime.now()
    today = date.today()
    horizon = today + timedelta(days=lookahead_days)

    in_progress: list[Task] = []
    pending_review: list[Task] = []
    waiting: list[Task] = []
    upcoming: list[Task] = []
    overdue: list[Task] = []

    for t in tasks:
        if t.status == Status.REALIZOWANE:
            in_progress.append(t)
        elif t.status == Status.DO_OCENY:
            pending_review.append(t)
        elif t.status == Status.OCZEKUJACE:
            waiting.append(t)

        if t.deadline and t.status not in (
            Status.ZAKONCZONE, Status.ODRZUCONE, Status.WYCOFANE
        ):
            dl = t.deadline.date() if isinstance(t.deadline, datetime) else t.deadline
            if dl < today:
                overdue.append(t)
            elif dl <= horizon:
                upcoming.append(t)

    # Sort: overdue by deadline asc, upcoming by deadline asc
    overdue.sort(key=lambda t: t.deadline or datetime.min)
    upcoming.sort(key=lambda t: t.deadline or datetime.max)

    # Build human-readable summary
    parts: list[str] = []
    if in_progress:
        names = [t.subject or f"#{t.id}" for t in in_progress[:3]]
        suffix = f" (+{len(in_progress) - 3} more)" if len(in_progress) > 3 else ""
        parts.append(f"{len(in_progress)} task(s) in progress: {', '.join(names)}{suffix}.")
    if today_tasks:
        pts = sum(t.points or 0 for t in today_tasks)
        parts.append(f"{len(today_tasks)} task(s) completed today ({pts:.0f} pts).")
    if pending_review:
        parts.append(f"{len(pending_review)} task(s) pending manager review.")
    if waiting:
        parts.append(f"{len(waiting)} task(s) waiting in queue (rejected by manager).")
    if overdue:
        parts.append(f"⚠ {len(overdue)} overdue task(s) need attention.")
    if upcoming:
        parts.append(f"{len(upcoming)} deadline(s) within the next {lookahead_days} days.")
    if not parts:
        parts.append("No active tasks. All clear!")

    return WorkContext(
        as_of=now.isoformat(timespec="seconds"),
        in_progress=in_progress,
        pending_review=pending_review,
        waiting=waiting,
        completed_today=today_tasks,
        upcoming_deadlines=upcoming,
        overdue=overdue,
        summary=" ".join(parts),
    )


# ── ProblemReport ─────────────────────────────────────────────────────────────

def detect_problems(tasks: list[Task], *, stalled_days: int = _STALLED_DAYS) -> ProblemReport:
    """Scan tasks for actionable problems."""
    today = date.today()
    problems: list[Problem] = []

    for t in tasks:
        if t.status in (Status.ZAKONCZONE, Status.ODRZUCONE, Status.WYCOFANE):
            continue

        deadline_date: date | None = None
        if t.deadline:
            dl = t.deadline
            deadline_date = dl.date() if isinstance(dl, datetime) else dl

        # Overdue
        if deadline_date and deadline_date < today and t.status not in (
            Status.ZAKONCZONE, Status.DO_OCENY
        ):
            days_over = (today - deadline_date).days
            problems.append(Problem(
                task_id=t.id,
                subject=t.subject,
                status=t.status,
                problem_type="overdue",
                severity="high" if days_over > 7 else "medium",
                detail=f"Deadline was {deadline_date.isoformat()} ({days_over} day(s) ago).",
                days_overdue=days_over,
                deadline=deadline_date.isoformat(),
            ))
            continue  # don't double-report

        # Stalled — REALIZOWANE with no movement for too long
        if t.status == Status.REALIZOWANE and t.started_at:
            started = t.started_at
            started_date = started.date() if isinstance(started, datetime) else started
            days_running = (today - started_date).days
            if days_running >= stalled_days:
                problems.append(Problem(
                    task_id=t.id,
                    subject=t.subject,
                    status=t.status,
                    problem_type="stalled",
                    severity="medium" if days_running < 30 else "high",
                    detail=(
                        f"In progress for {days_running} day(s) with no completion. "
                        "Consider completing or updating the deadline."
                    ),
                    days_since_start=days_running,
                    deadline=deadline_date.isoformat() if deadline_date else None,
                ))

        # Waiting in queue (rejected by manager) — needs attention
        if t.status == Status.OCZEKUJACE:
            problems.append(Problem(
                task_id=t.id,
                subject=t.subject,
                status=t.status,
                problem_type="awaiting",
                severity="medium",
                detail=(
                    "Task is waiting in the manager's queue (OCZEKUJĄCE). "
                    "Use withdraw_task to pull it back for editing, or contact your manager."
                ),
                deadline=deadline_date.isoformat() if deadline_date else None,
            ))

    # Sort: high first, then medium, then by task_id
    severity_order = {"high": 0, "medium": 1, "low": 2}
    problems.sort(key=lambda p: (severity_order.get(p.severity, 9), p.task_id))

    note = (
        "No problems detected — all tasks look healthy."
        if not problems
        else f"{len(problems)} problem(s) found. High-severity items listed first."
    )

    return ProblemReport(
        checked_tasks=len(tasks),
        total_problems=len(problems),
        problems=problems,
        note=note,
    )


# ── TagSuggestion ─────────────────────────────────────────────────────────────

def suggest_tags(
    subject: str,
    task_history: list[Task],
    all_tags: list[Tag],
    *,
    top_n: int = 5,
) -> list[TagSuggestion]:
    """Suggest tags for a new task based on keyword similarity to past tasks."""
    if not subject.strip():
        return []

    subject_words = set(subject.casefold().split())
    tag_scores: Counter[int] = Counter()
    tag_names: dict[int, str] = {t.id: t.name for t in all_tags}
    tag_reasons: dict[int, list[str]] = defaultdict(list)

    for task in task_history:
        if not task.tags:
            continue
        # Keyword overlap between new subject and past task subject
        if task.subject:
            task_words = set(task.subject.casefold().split())
            overlap = subject_words & task_words
            if overlap:
                for tag_name in task.tags:
                    # Resolve tag name → id
                    tag_id = next(
                        (t.id for t in all_tags if t.name == tag_name), None
                    )
                    if tag_id:
                        tag_scores[tag_id] += len(overlap)
                        if len(overlap) >= 2:
                            tag_reasons[tag_id].append(
                                f"used on similar task: '{task.subject[:40]}'"
                            )

    if not tag_scores:
        return []

    max_score = max(tag_scores.values())
    suggestions = [
        TagSuggestion(
            id=tid,
            name=tag_names.get(tid, f"tag#{tid}"),
            relevance_score=round(score / max_score, 2),
            reason=tag_reasons[tid][0] if tag_reasons[tid] else "frequently co-occurring",
        )
        for tid, score in tag_scores.most_common(top_n)
        if tid in tag_names
    ]
    return suggestions


# ── TaskTypeStats ─────────────────────────────────────────────────────────────

def compute_task_type_stats(tasks: list[Task], *, days: int = 30) -> TaskTypeStats:
    """Aggregate task counts and points by task type for a date window."""
    cutoff = datetime.now() - timedelta(days=days)

    recent = [
        t for t in tasks
        if t.ordered_at and (
            t.ordered_at if isinstance(t.ordered_at, datetime) else datetime.min
        ) >= cutoff
    ]

    # Group by task_type_id
    by_type: dict[int | None, list[Task]] = defaultdict(list)
    for t in recent:
        by_type[t.task_type.id].append(t)

    stats: list[TaskTypeStat] = []
    for tid, ttasks in sorted(by_type.items(), key=lambda x: -len(x[1])):
        total_pts = sum(t.points or 0 for t in ttasks)
        completed = sum(1 for t in ttasks if t.status == Status.ZAKONCZONE)
        in_prog = sum(1 for t in ttasks if t.status == Status.REALIZOWANE)
        stats.append(TaskTypeStat(
            task_type_id=tid,
            task_type_name=ttasks[0].task_type.name if ttasks else None,
            count=len(ttasks),
            total_points=total_pts,
            avg_points=round(total_pts / len(ttasks), 2) if ttasks else 0.0,
            completed=completed,
            in_progress=in_prog,
        ))

    return TaskTypeStats(
        days=days,
        total_tasks=len(recent),
        task_types=stats,
    )


# ── Recurring patterns ────────────────────────────────────────────────────────



@dataclass
class RecurringPattern:
    """A detected recurring work pattern."""
    task_type_id: int | None
    task_type_name: str | None
    example_subject: str | None
    count: int
    avg_points: float
    suggested_subject: str | None


def detect_recurring_patterns(
    tasks: list[Task],
    *,
    min_count: int = 3,
) -> list[RecurringPattern]:
    """Find task types + subject patterns that appear repeatedly."""
    from collections import defaultdict as _dd

    # Group by task_type_id
    by_type: dict[int | None, list[Task]] = _dd(list)
    for t in tasks:
        by_type[t.task_type.id].append(t)

    patterns = []
    for tid, ttasks in by_type.items():
        if len(ttasks) < min_count:
            continue
        avg_pts = sum(t.points or 0 for t in ttasks) / len(ttasks)
        # pick most common subject words as suggested subject
        subjects = [t.subject or "" for t in ttasks if t.subject]
        suggested = _most_common_subject(subjects)
        patterns.append(RecurringPattern(
            task_type_id=tid,
            task_type_name=ttasks[0].task_type.name,
            example_subject=subjects[0] if subjects else None,
            count=len(ttasks),
            avg_points=round(avg_pts, 2),
            suggested_subject=suggested,
        ))

    return sorted(patterns, key=lambda p: -p.count)


def _most_common_subject(subjects: list[str]) -> str | None:
    if not subjects:
        return None
    from collections import Counter as _C
    words: _C[str] = _C()
    for s in subjects:
        words.update(s.casefold().split())
    # Remove very short words
    top = [w for w, _ in words.most_common(5) if len(w) > 3]
    return " ".join(top[:3]).title() if top else subjects[0][:40]


# ── Completion suggestions ────────────────────────────────────────────────────

@dataclass
class CompletionSuggestion:
    """A task suggested for completion with a priority score."""
    task_id: int
    subject: str | None
    status: str
    score: float         # higher = more urgent
    reason: str
    deadline: str | None
    days_running: int | None


def prioritize_completions(
    tasks: list[Task],
    *,
    limit: int = 10,
) -> list[CompletionSuggestion]:
    """Rank REALIZOWANE tasks by completion urgency."""
    today = date.today()
    candidates = [t for t in tasks if t.status == Status.REALIZOWANE]
    suggestions = []

    for t in candidates:
        score = 0.0
        reasons: list[str] = []

        deadline_date: date | None = None
        if t.deadline:
            d = t.deadline
            deadline_date = d.date() if isinstance(d, datetime) else d

        # Overdue: very high urgency
        if deadline_date and deadline_date < today:
            days_over = (today - deadline_date).days
            score += 100 + days_over * 5
            reasons.append(f"overdue by {days_over} day(s)")

        # Near deadline (within 3 days)
        elif deadline_date and (deadline_date - today).days <= 3:
            score += 60
            reasons.append(f"deadline in {(deadline_date - today).days} day(s)")

        # High points
        if (t.points or 0) >= 5:
            score += 20
            reasons.append(f"{t.points} points")

        # Long running without deadline
        days_running: int | None = None
        if t.started_at:
            s = t.started_at
            start = s.date() if isinstance(s, datetime) else s
            days_running = (today - start).days
            if days_running >= 7 and not deadline_date:
                score += 10 + days_running
                reasons.append(f"running {days_running} days, no deadline")

        if score > 0 or days_running:
            suggestions.append(CompletionSuggestion(
                task_id=t.id,
                subject=t.subject,
                status=t.status,
                score=round(score, 1),
                reason="; ".join(reasons) if reasons else "in progress",
                deadline=deadline_date.isoformat() if deadline_date else None,
                days_running=days_running,
            ))

    return sorted(suggestions, key=lambda s: -s.score)[:limit]

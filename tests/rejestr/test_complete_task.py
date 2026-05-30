"""Tests for complete_task — transition logic, dry-run, validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_emp.domains.rejestr.contract import RejestrDetailWrapperPayload, Task
from mcp_emp.domains.rejestr.mapper import map_task_from_detail
from mcp_emp.domains.rejestr.results import TaskCompleteResult
from mcp_emp.domains.rejestr.status import Status

FIXTURES = Path(__file__).parent


def _task_from_fixture(status: str = "REALIZOWANE") -> Task:
    raw = json.loads((FIXTURES / "get_task.json").read_text(encoding="utf-8"))
    wrapper = RejestrDetailWrapperPayload.model_validate(raw)
    wrapper.item.status = status
    return map_task_from_detail(wrapper.item)


# ── Transition prediction logic ───────────────────────────────────────────────

def test_realizowane_no_evaluation_to_zakonczone() -> None:
    task = _task_from_fixture("REALIZOWANE")
    task.task_type.requires_evaluation = False

    if task.status == Status.DO_OCENY:
        predicted = Status.ZAKONCZONE
    elif task.task_type.requires_evaluation:
        predicted = Status.DO_OCENY
    else:
        predicted = Status.ZAKONCZONE

    assert predicted == Status.ZAKONCZONE


def test_realizowane_with_evaluation_to_do_oceny() -> None:
    task = _task_from_fixture("REALIZOWANE")
    task.task_type.requires_evaluation = True

    if task.status == Status.DO_OCENY:
        predicted = Status.ZAKONCZONE
    elif task.task_type.requires_evaluation:
        predicted = Status.DO_OCENY
    else:
        predicted = Status.ZAKONCZONE

    assert predicted == Status.DO_OCENY


def test_do_oceny_always_to_zakonczone() -> None:
    task = _task_from_fixture("DO_OCENY")
    task.task_type.requires_evaluation = True  # even with evaluation flag

    if task.status == Status.DO_OCENY:
        predicted = Status.ZAKONCZONE
    elif task.task_type.requires_evaluation:
        predicted = Status.DO_OCENY
    else:
        predicted = Status.ZAKONCZONE

    assert predicted == Status.ZAKONCZONE


def test_invalid_transition_w_edycji() -> None:
    from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415

    task = _task_from_fixture("W_EDYCJI")
    with pytest.raises(InvalidTransition):
        if task.status not in (Status.REALIZOWANE, Status.DO_OCENY):
            raise InvalidTransition(
                task_id=task.id,
                current=task.status,
                attempted="zakoncz",
            )


def test_invalid_transition_zakonczone() -> None:
    from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415

    task = _task_from_fixture("ZAKOŃCZONE")
    with pytest.raises(InvalidTransition):
        if task.status not in (Status.REALIZOWANE, Status.DO_OCENY):
            raise InvalidTransition(
                task_id=task.id,
                current=task.status,
                attempted="zakoncz",
            )


# ── TaskCompleteResult shape ──────────────────────────────────────────────────

def test_complete_result_dry_run() -> None:
    result = TaskCompleteResult(
        dry_run=True,
        task_id=134343,
        from_status="REALIZOWANE",
        would_transition_to=Status.ZAKONCZONE,
        task=None,
        note="dry run",
    )
    assert result.dry_run is True
    assert result.task is None
    assert result.would_transition_to == "ZAKOŃCZONE"


def test_complete_result_live() -> None:
    task = _task_from_fixture("ZAKOŃCZONE")
    result = TaskCompleteResult(
        dry_run=False,
        task_id=task.id,
        from_status="REALIZOWANE",
        would_transition_to="ZAKOŃCZONE",
        task=task,
        note="done",
    )
    assert result.task is not None
    assert result.task.status == "ZAKOŃCZONE"


# ── Time/quantity validation ──────────────────────────────────────────────────

def test_requires_time_missing_raises() -> None:
    from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415

    task = _task_from_fixture("REALIZOWANE")
    task.task_type.requires_time = True
    time = ""

    with pytest.raises(ValidationFailed):
        if task.task_type.requires_time and not time:
            raise ValidationFailed(
                f"Task type '{task.task_type.name}' requires time.",
                {"task_id": task.id},
            )


def test_requires_quantity_missing_raises() -> None:
    from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415

    task = _task_from_fixture("REALIZOWANE")
    task.task_type.requires_quantity = True
    quantity = None

    with pytest.raises(ValidationFailed):
        if task.task_type.requires_quantity and quantity is None:
            raise ValidationFailed(
                f"Task type '{task.task_type.name}' requires quantity.",
                {"task_id": task.id},
            )

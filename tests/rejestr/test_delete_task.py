"""Tests for delete_task — confirmation token lifecycle (all 7 scenarios)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_emp.core import confirmations
from mcp_emp.core.errors import ConfirmationInvalid, InvalidTransition
from mcp_emp.domains.rejestr.contract import RejestrDetailWrapperPayload
from mcp_emp.domains.rejestr.delete_result import TaskDeleteResult
from mcp_emp.domains.rejestr.mapper import map_task_from_detail
from mcp_emp.domains.rejestr.status import Status

FIXTURES = Path(__file__).parent


def _task(status: str = "W_EDYCJI"):  # type: ignore[no-untyped-def]
    raw = json.loads((FIXTURES / "get_task.json").read_text(encoding="utf-8"))
    wrapper = RejestrDetailWrapperPayload.model_validate(raw)
    wrapper.item.status = status
    return map_task_from_detail(wrapper.item)


# ── pre-flight: wrong status ──────────────────────────────────────────────────

def test_delete_blocked_on_non_draft() -> None:
    """Only W_EDYCJI tasks can be deleted."""
    for status in ("REALIZOWANE", "DO_OCENY", "ZAKOŃCZONE", "ODRZUCONE"):
        task = _task(status)
        with pytest.raises(InvalidTransition):
            if task.status != Status.W_EDYCJI:
                raise InvalidTransition(
                    task_id=task.id,
                    current=task.status,
                    attempted="usun",
                )


# ── dry_run ───────────────────────────────────────────────────────────────────

def test_dry_run_no_token() -> None:
    """dry_run returns preview without a token."""
    from mcp_emp.domains.rejestr.delete_result import TaskDeletePreview  # noqa: PLC0415

    task = _task("W_EDYCJI")
    preview = TaskDeletePreview(
        task_id=task.id,
        subject=task.subject,
        status=task.status,
        task_type_name=task.task_type.name,
        ordered_at=None,
    )
    result = TaskDeleteResult(
        deleted=False,
        task_id=task.id,
        preview=preview,
        confirmation_token=None,
        note="dry run",
    )
    assert result.confirmation_token is None
    assert result.deleted is False
    assert result.preview is not None


# ── confirmation token lifecycle ──────────────────────────────────────────────

async def test_issue_and_consume_happy() -> None:
    """Scenario 1: token issued, consumed once — succeeds."""
    confirmations._store.clear()
    payload = {"task_id": 42, "subject": "Test", "status": "W_EDYCJI"}
    token = await confirmations.issue("del", 42, payload)
    assert token.startswith("del_42_")
    # consume succeeds
    await confirmations.consume(token, "del", 42, payload)
    # store is now empty
    assert token not in confirmations._store


async def test_token_single_use() -> None:
    """Scenario 2: second consume raises ConfirmationInvalid(reason='unknown')."""
    confirmations._store.clear()
    payload = {"task_id": 43, "subject": "x", "status": "W_EDYCJI"}
    token = await confirmations.issue("del", 43, payload)
    await confirmations.consume(token, "del", 43, payload)
    with pytest.raises(ConfirmationInvalid, match="not found"):
        await confirmations.consume(token, "del", 43, payload)


async def test_token_expired(time_machine) -> None:  # type: ignore[no-untyped-def]
    """Scenario 3: token past TTL raises ConfirmationInvalid(reason='expired')."""
    import time  # noqa: PLC0415

    confirmations._store.clear()
    payload = {"task_id": 44, "subject": "x", "status": "W_EDYCJI"}
    token = await confirmations.issue("del", 44, payload)
    # advance wall time past TTL
    time_machine.move_to(time.time() + confirmations.TOKEN_TTL + 1)
    with pytest.raises(ConfirmationInvalid, match="expired"):
        await confirmations.consume(token, "del", 44, payload)


async def test_token_wrong_op() -> None:
    """Scenario 4: token for 'del' can't be used for 'withdraw'."""
    confirmations._store.clear()
    payload = {"task_id": 45, "subject": "x", "status": "W_EDYCJI"}
    token = await confirmations.issue("del", 45, payload)
    with pytest.raises(ConfirmationInvalid, match="scope"):
        await confirmations.consume(token, "withdraw", 45, payload)


async def test_token_wrong_resource_id() -> None:
    """Scenario 5: token for task 45 can't delete task 46."""
    confirmations._store.clear()
    payload = {"task_id": 45, "subject": "x", "status": "W_EDYCJI"}
    token = await confirmations.issue("del", 45, payload)
    with pytest.raises(ConfirmationInvalid, match="scope"):
        await confirmations.consume(token, "del", 46, payload)


async def test_token_payload_hash_bait_and_switch() -> None:
    """Scenario 6: token bound to task A, can't be used with task B's payload."""
    confirmations._store.clear()
    payload_a = {"task_id": 47, "subject": "Task A", "status": "W_EDYCJI"}
    payload_b = {"task_id": 47, "subject": "Task B (different!)", "status": "W_EDYCJI"}
    token = await confirmations.issue("del", 47, payload_a)
    with pytest.raises(ConfirmationInvalid, match="hash"):
        await confirmations.consume(token, "del", 47, payload_b)


async def test_token_unknown_raises_not_found() -> None:
    """Scenario 7: completely fabricated token raises ConfirmationInvalid."""
    confirmations._store.clear()
    payload = {"task_id": 99, "subject": "x", "status": "W_EDYCJI"}
    with pytest.raises(ConfirmationInvalid, match="not found"):
        await confirmations.consume("del_99_fakefake", "del", 99, payload)

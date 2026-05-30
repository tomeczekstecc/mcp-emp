"""Rejestr MCP tool registrations — list_my_tasks, get_task, add_my_task."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.modes import mutating, readable
from mcp_emp.domains.rejestr.client import (
    complete_my_task,
    create_my_task,
    delete_my_task,
    fetch_my_tasks,
    fetch_task,
)
from mcp_emp.domains.rejestr.contract import Task
from mcp_emp.domains.rejestr.delete_result import TaskDeletePreview, TaskDeleteResult
from mcp_emp.domains.rejestr.results import (
    PreflightReport,
    TaskCompleteResult,
    TaskCreateResult,
)
from mcp_emp.domains.rejestr.status import resolve_status


def register(server: FastMCP) -> None:
    """Register all rejestr tools on *server*."""

    @server.tool()
    @readable
    async def list_my_tasks(
        scope: str = "active",
        status: str = "",
        search: str = "",
        sod_number: str = "",
        limit: int = 50,
    ) -> list[Task]:
        """List tasks assigned to me from EMP.

        Args:
            scope:      "active" — only currently open tasks (default).
                        "all"    — full history including completed/rejected.
            status:     Filter by status. Accepts Polish identifiers
                        (e.g. "ZAKOŃCZONE") or English aliases
                        (e.g. "completed", "draft", "in_progress").
            search:     Substring filter on the task subject (case-insensitive).
            sod_number: Filter by SOD case number (exact substring match).
            limit:      Maximum number of tasks to return (default 50, max 500).

        Returns:
            List of Task objects, newest first.
        """
        emp_scope = "moje" if scope == "active" else "moje-wszystkie"
        tasks = await fetch_my_tasks(scope=emp_scope)

        if status:
            resolved = resolve_status(status)
            filter_status = resolved.value if resolved else status
            tasks = [t for t in tasks if t.status == filter_status]

        if search:
            q = search.casefold()
            tasks = [t for t in tasks if t.subject and q in t.subject.casefold()]

        if sod_number:
            tasks = [t for t in tasks if t.sod_number and sod_number in t.sod_number]

        tasks = sorted(tasks, key=lambda t: t.ordered_at or t.id, reverse=True)
        return tasks[:min(limit, 500)]

    @server.tool()
    @readable
    async def get_task(task_id: int) -> Task:
        """Fetch full details of a single EMP task by ID.

        Includes the permissions block (can_complete, can_delete, can_edit,
        can_start) and any rejection/correction reasons.

        Args:
            task_id: The numeric EMP task ID.

        Returns:
            Full Task with permissions populated.
        """
        return await fetch_task(task_id)

    @server.tool()
    @mutating
    async def add_my_task(
        task_type_id: int,
        subject: str = "",
        deadline: str = "",
        notes: str = "",
        url: str = "",
        sod_number: str = "",
        sod_letter: str = "",
        quantity: float | None = None,
        time: str = "",
        tag_ids: list[int] | None = None,
        parent_id: int | None = None,
        dry_run: bool = False,
    ) -> TaskCreateResult:
        """Create a new task in EMP assigned to me.

        The task is immediately set to REALIZOWANE (in progress) by EMP.
        Points and weight are taken automatically from the task type.

        Call list_task_types() first to find the correct task_type_id.
        Call list_tags() to find valid tag IDs.

        Use dry_run=true to validate inputs without creating anything.

        Args:
            task_type_id: Required. ID from list_task_types().
            subject:      What the task is about.
            deadline:     ISO 8601 date/datetime (e.g. "2026-06-30").
            notes:        Internal notes (uwagi).
            url:          Related URL (e.g. Mantis ticket).
            sod_number:   SOD case number (nr_sprawy_sod).
            sod_letter:   SOD letter number (nr_pisma_sod).
            quantity:     Required when the task type requires quantity.
            time:         Time spent, HH:MM format. Required when task type
                          requires time.
            tag_ids:      List of tag IDs from list_tags().
            parent_id:    Parent task ID for sub-tasks.
            dry_run:      When true, validate and preview without creating.

        Returns:
            TaskCreateResult with the created task (or None on dry_run).
        """
        from mcp_emp.core.config import get_settings  # noqa: PLC0415
        from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415
        from mcp_emp.domains.slowniki.cache import get_or_load  # noqa: PLC0415
        from mcp_emp.domains.slowniki.client import fetch_tags, fetch_task_types  # noqa: PLC0415

        s = get_settings()

        # ── pre-flight: validate task type ────────────────────────────────────
        task_types = await get_or_load("task_types", fetch_task_types, s.task_type_ttl)
        tt_map = {t.id: t for t in task_types}
        tt = tt_map.get(task_type_id)

        if tt is None:
            raise ValidationFailed(
                f"task_type_id={task_type_id} not found in słownik.",
                {"task_type_id": task_type_id,
                 "valid_ids": [t.id for t in task_types][:20]},
            )

        # ── pre-flight: validate tags ─────────────────────────────────────────
        tag_ids_valid: list[int] = []
        tag_ids_unknown: list[int] = []
        if tag_ids:
            tags = await get_or_load("tags", lambda: fetch_tags(full=True), s.tag_ttl)
            valid_tag_ids = {t.id for t in tags}
            for tid in tag_ids:
                if tid in valid_tag_ids:
                    tag_ids_valid.append(tid)
                else:
                    tag_ids_unknown.append(tid)
            if tag_ids_unknown:
                raise ValidationFailed(
                    f"Unknown tag IDs: {tag_ids_unknown}",
                    {"unknown_tag_ids": tag_ids_unknown,
                     "valid_ids": sorted(valid_tag_ids)},
                )
            tag_ids_valid = tag_ids

        # ── pre-flight: quantity / time requirements ──────────────────────────
        if tt.requires_quantity and quantity is None:
            raise ValidationFailed(
                f"Task type '{tt.name}' requires a quantity (ilosc).",
                {"task_type_id": task_type_id, "task_type_name": tt.name},
            )
        if tt.requires_time and not time:
            raise ValidationFailed(
                f"Task type '{tt.name}' requires time in HH:MM format.",
                {"task_type_id": task_type_id, "task_type_name": tt.name},
            )

        preflight = PreflightReport(
            task_type_id=task_type_id,
            task_type_name=tt.name,
            requires_quantity=tt.requires_quantity,
            requires_time=tt.requires_time,
            quantity_provided=quantity is not None,
            time_provided=bool(time),
            tag_ids_valid=tag_ids_valid,
            tag_ids_unknown=[],
        )

        if dry_run:
            return TaskCreateResult(
                dry_run=True,
                validated=preflight,
                task=None,
                note=(
                    "Dry run — no task created. "
                    "Call again with dry_run=false to create."
                ),
            )

        # ── create ────────────────────────────────────────────────────────────
        task = await create_my_task(
            task_type_id=task_type_id,
            subject=subject or None,
            deadline=deadline or None,
            notes=notes or None,
            url=url or None,
            sod_number=sod_number or None,
            sod_letter=sod_letter or None,
            quantity=quantity,
            time=time or None,
            tag_ids=tag_ids_valid or None,
            parent_id=parent_id,
        )

        return TaskCreateResult(
            dry_run=False,
            validated=preflight,
            task=task,
            note="Task created and set to REALIZOWANE (in progress).",
        )

    @server.tool()
    @mutating
    async def complete_task(
        task_id: int,
        time: str = "",
        quantity: float | None = None,
        dry_run: bool = False,
    ) -> TaskCompleteResult:
        """Complete a task in EMP (PUT /rejestr/zakoncz).

        Transitions:
          REALIZOWANE + task type requires evaluation → DO_OCENY (pending review)
          REALIZOWANE (no evaluation required)        → ZAKOŃCZONE (completed)
          DO_OCENY                                    → ZAKOŃCZONE (completed)

        Use dry_run=true to see the predicted transition without changing anything.

        Args:
            task_id:  ID of the task to complete.
            time:     Time spent in HH:MM format (required if task type needs it).
            quantity: Quantity completed (required if task type needs it).
            dry_run:  Preview the transition without calling EMP.

        Returns:
            TaskCompleteResult with the updated task and transition info.
        """
        from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415
        from mcp_emp.domains.rejestr.status import Status  # noqa: PLC0415

        # pre-flight: fetch current task
        task = await fetch_task(task_id)
        current_status = task.status

        if current_status not in (Status.REALIZOWANE, Status.DO_OCENY):
            raise InvalidTransition(
                task_id=task_id,
                current=current_status,
                attempted="zakoncz",
            )

        # predict outcome
        if current_status == Status.DO_OCENY:
            would_transition_to = Status.ZAKONCZONE
        elif task.task_type.requires_evaluation:
            would_transition_to = Status.DO_OCENY
        else:
            would_transition_to = Status.ZAKONCZONE

        # time/quantity validation
        if task.task_type.requires_time and not time:
            from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415
            raise ValidationFailed(
                f"Task type '{task.task_type.name}' requires time in HH:MM format.",
                {"task_id": task_id, "task_type": task.task_type.name},
            )
        if task.task_type.requires_quantity and quantity is None:
            from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415
            raise ValidationFailed(
                f"Task type '{task.task_type.name}' requires a quantity.",
                {"task_id": task_id, "task_type": task.task_type.name},
            )

        note = (
            f"Will transition: {current_status} → {would_transition_to}"
            + (" (pending manager review)" if would_transition_to == Status.DO_OCENY else " (completed)")
        )

        if dry_run:
            return TaskCompleteResult(
                dry_run=True,
                task_id=task_id,
                from_status=current_status,
                would_transition_to=would_transition_to,
                task=None,
                note=note + " — dry run, nothing changed.",
            )

        updated = await complete_my_task(
            task_id=task_id,
            time=time or None,
            quantity=quantity,
        )
        return TaskCompleteResult(
            dry_run=False,
            task_id=task_id,
            from_status=current_status,
            would_transition_to=updated.status,
            task=updated,
            note=note,
        )

    @server.tool()
    @mutating
    async def delete_task(
        task_id: int,
        confirmation_token: str = "",
        dry_run: bool = False,
    ) -> TaskDeleteResult:
        """Delete a draft task (W_EDYCJI) from EMP.

        This is a two-step operation to prevent accidental deletion:

        Step 1 — call WITHOUT confirmation_token:
          Returns a preview of the task and a confirmation_token.
          Nothing is deleted yet.

        Step 2 — call WITH the confirmation_token from step 1:
          Deletes the task permanently. Tokens expire after 5 minutes
          and are single-use.

        Only tasks in W_EDYCJI (draft) status can be deleted.

        Args:
            task_id:            ID of the task to delete.
            confirmation_token: Token from the step-1 response.
            dry_run:            Preview without issuing a token (for inspection).

        Returns:
            TaskDeleteResult with preview + token (step 1) or deleted=True (step 2).
        """
        from mcp_emp.core import confirmations  # noqa: PLC0415
        from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415
        from mcp_emp.domains.rejestr.status import Status  # noqa: PLC0415

        # always fetch the task first (needed for preview + status check)
        task = await fetch_task(task_id)

        if task.status != Status.W_EDYCJI:
            raise InvalidTransition(
                task_id=task_id,
                current=task.status,
                attempted="usun",
            )

        preview = TaskDeletePreview(
            task_id=task_id,
            subject=task.subject,
            status=task.status,
            task_type_name=task.task_type.name,
            ordered_at=task.ordered_at.isoformat() if task.ordered_at else None,
        )

        # ── dry_run: preview only, no token ───────────────────────────────────
        if dry_run:
            return TaskDeleteResult(
                deleted=False,
                task_id=task_id,
                preview=preview,
                confirmation_token=None,
                note="Dry run — no token issued, nothing deleted.",
            )

        # ── step 2: confirmation token provided — execute delete ──────────────
        if confirmation_token:
            payload: dict[str, object] = {
                "task_id": task_id,
                "subject": task.subject,
                "status": task.status,
            }
            await confirmations.consume(
                token=confirmation_token,
                op="del",
                resource_id=task_id,
                payload=payload,
            )
            await delete_my_task(task_id)
            return TaskDeleteResult(
                deleted=True,
                task_id=task_id,
                preview=None,
                confirmation_token=None,
                note=f"Task {task_id} permanently deleted.",
            )

        # ── step 1: issue preview + confirmation token ────────────────────────
        payload2: dict[str, object] = {
            "task_id": task_id,
            "subject": task.subject,
            "status": task.status,
        }
        token = await confirmations.issue(
            op="del",
            resource_id=task_id,
            payload=payload2,
        )
        return TaskDeleteResult(
            deleted=False,
            task_id=task_id,
            preview=preview,
            confirmation_token=token,
            expires_in_seconds=confirmations.TOKEN_TTL,
            note=(
                "Review the preview above, then call delete_task again "
                f"with confirmation_token='{token}' to permanently delete. "
                f"Token expires in {confirmations.TOKEN_TTL // 60} minutes."
            ),
        )

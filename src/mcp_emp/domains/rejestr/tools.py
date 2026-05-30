"""Rejestr MCP tool registrations — list_my_tasks, get_task, add_my_task."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_emp.core.modes import mutating, readable
from mcp_emp.domains.rejestr.client import (
    bulk_create_my_tasks,
    bulk_delete_my_tasks,
    complete_my_task,
    create_my_task,
    delete_my_task,
    edit_my_task,
    fetch_my_tasks,
    fetch_task,
    fetch_team_tasks,
    reject_my_task,
    start_my_task,
    withdraw_my_task,
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
            ordered_at=task.ordered_at if task.ordered_at else None,
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

    @server.tool()
    @mutating
    async def edit_task(
        task_id: int,
        subject: str = "",
        deadline: str = "",
        notes: str = "",
        url: str = "",
        sod_number: str = "",
        sod_letter: str = "",
        quantity: float | None = None,
        time: str = "",
        tag_ids: list[int] | None = None,
        ordered_at: str = "",
        dry_run: bool = False,
    ) -> Task:
        """Edit an existing task's fields (PUT /rejestr).

        Works on any task not in ZAKOńCZONE, ODRZUCONE, or WYCOFANE status.
        Only the fields you provide are updated; omitted fields are unchanged.

        Args:
            task_id:    ID of the task to edit.
            subject:    New task subject.
            deadline:   New deadline in ISO 8601 format (e.g. '2026-07-01').
            notes:      Internal notes (uwagi).
            url:        Related URL.
            sod_number: SOD case number.
            sod_letter: SOD letter number.
            quantity:   Quantity (ilosc).
            time:       Time spent in HH:MM format.
            tag_ids:    Full list of tag IDs to set (replaces existing tags).
            ordered_at: Override the order date — ISO 8601 or YYYY-MM-DD (e.g.
                        "2026-01-15"). Sets data_zlecenia + data_rozpoczecia so
                        the task is attributed to the correct month in reports.
                        Useful for retroactively logging tasks from past months.
            dry_run:    Preview without calling EMP.

        Returns:
            Updated Task.
        """
        from mcp_emp.domains.rejestr.status import Status  # noqa: PLC0415

        # pre-flight: fetch and check status
        task = await fetch_task(task_id)
        if task.status in (Status.ZAKONCZONE, Status.ODRZUCONE, Status.WYCOFANE):
            from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415
            raise InvalidTransition(
                task_id=task_id, current=task.status, attempted="zapisz"
            )

        if dry_run:
            # Return current task with note — no write
            return task

        return await edit_my_task(
            task_id=task_id,
            subject=subject or None,
            deadline=deadline or None,
            notes=notes or None,
            url=url or None,
            sod_number=sod_number or None,
            sod_letter=sod_letter or None,
            quantity=quantity,
            time=time or None,
            tag_ids=tag_ids,
            ordered_at=ordered_at or None,
        )

    @server.tool()
    @mutating
    async def start_task(task_id: int) -> Task:
        """Start a planned task (PRZYDZIELONE → REALIZOWANE).

        Tasks created with add_my_task start immediately in REALIZOWANE.
        This tool is for planned tasks (created with czy_planowane=Tak)
        that are in PRZYDZIELONE (assigned/planned) status.

        Args:
            task_id: ID of the task to start.

        Returns:
            Updated Task in REALIZOWANE status.
        """
        from mcp_emp.domains.rejestr.status import Status  # noqa: PLC0415

        task = await fetch_task(task_id)
        if task.status != Status.PRZYDZIELONE:
            from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415
            raise InvalidTransition(
                task_id=task_id, current=task.status, attempted="realizuj"
            )
        return await start_my_task(task_id)

    @server.tool()
    @mutating
    async def reject_task(
        task_id: int,
        reason: str = "",
        dry_run: bool = False,
    ) -> Task:
        """Reject a REALIZOWANE task back to OCZEKUJĄCE (waiting queue).

        Manager operation. Clears the assigned user so the task returns
        to the team queue. Optionally provide a rejection reason.

        Args:
            task_id: ID of the task to reject.
            reason:  Rejection reason (uzasadnienie_odrzucenia). Optional.
            dry_run: Preview without calling EMP.

        Returns:
            Updated Task in OCZEKUJĄCE status.
        """
        from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415
        from mcp_emp.domains.rejestr.status import Status  # noqa: PLC0415

        task = await fetch_task(task_id)
        if task.status != Status.REALIZOWANE:
            raise InvalidTransition(
                task_id=task_id, current=task.status, attempted="odrzuc"
            )
        if dry_run:
            return task
        return await reject_my_task(task_id, reason or None)

    @server.tool()
    @mutating
    async def withdraw_task(
        task_id: int,
        dry_run: bool = False,
    ) -> Task:
        """Withdraw an OCZEKUJĄCE task back to W_EDYCJI (draft).

        Used after a task has been rejected by a manager (put in OCZEKUJĄCE)
        and the employee wants to re-edit and resubmit it.

        Args:
            task_id: ID of the task to withdraw.
            dry_run: Preview without calling EMP.

        Returns:
            Updated Task in W_EDYCJI status.
        """
        from mcp_emp.core.errors import InvalidTransition  # noqa: PLC0415
        from mcp_emp.domains.rejestr.status import Status  # noqa: PLC0415

        task = await fetch_task(task_id)
        if task.status != Status.OCZEKUJACE:
            raise InvalidTransition(
                task_id=task_id, current=task.status, attempted="wycofaj"
            )
        if dry_run:
            return task
        return await withdraw_my_task(task_id)

    @server.tool()
    @readable
    async def list_team_tasks(
        scope: str = "active",
        status: str = "",
        search: str = "",
        assigned_to_id: int | None = None,
        limit: int = 50,
    ) -> list[Task]:
        """List tasks visible to me as kierownik (team manager view).

        Requires kierownik_podglad permission. Returns an empty list if
        the current user lacks the required role.

        Args:
            scope:          "active" — currently open tasks (default).
                            "all"    — full team history.
            status:         Filter by status (Polish or English alias).
            search:         Substring filter on task subject.
            assigned_to_id: Filter by assigned user ID.
            limit:          Max results (default 50, max 500).

        Returns:
            List of Task objects newest first.
        """
        try:
            emp_scope = "" if scope == "active" else "moje-wszystkie"
            tasks = await fetch_team_tasks(scope=emp_scope)
        except Exception:  # noqa: BLE001
            return []

        if status:
            resolved = resolve_status(status)
            filter_status = resolved.value if resolved else status
            tasks = [t for t in tasks if t.status == filter_status]

        if search:
            q = search.casefold()
            tasks = [t for t in tasks if t.subject and q in t.subject.casefold()]

        if assigned_to_id is not None:
            tasks = [t for t in tasks if t.assigned_to is not None]

        tasks = sorted(tasks, key=lambda t: t.ordered_at or t.id, reverse=True)
        return tasks[:min(limit, 500)]

    # ── P3: Bulk operations ──────────────────────────────────────────────────

    @server.tool()
    @mutating
    async def bulk_create_tasks(
        tasks: list[dict[str, object]],
        confirmation_token: str = "",
        dry_run: bool = False,
    ) -> dict[str, object]:
        """Create multiple tasks at once with a two-step confirmation.

        Each task dict needs: task_type_id (required), plus optional subject,
        deadline, notes, url, sod_number, tag_ids.

        Step 1 (no token): validates, returns preview + confirmation_token.
        Step 2 (with token): creates all tasks.

        Args:
            tasks:              List of task dicts.
            confirmation_token: Token from step 1.
            dry_run:            Validate and preview without issuing token.
        """
        import hashlib  # noqa: PLC0415
        import json as _json  # noqa: PLC0415

        from mcp_emp.core import confirmations  # noqa: PLC0415
        from mcp_emp.core.config import get_settings  # noqa: PLC0415
        from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415
        from mcp_emp.domains.slowniki.cache import get_or_load  # noqa: PLC0415
        from mcp_emp.domains.slowniki.client import fetch_task_types  # noqa: PLC0415

        if not tasks:
            raise ValidationFailed("tasks list must not be empty.", {})

        s = get_settings()
        task_types = await get_or_load("task_types", fetch_task_types, s.task_type_ttl)
        tt_map = {t.id: t for t in task_types}

        for i, t in enumerate(tasks):
            tid = t.get("task_type_id")
            if not tid or not isinstance(tid, (int, float)):
                raise ValidationFailed(
                    f"tasks[{i}]: task_type_id={tid} not found.",
                    {"index": i, "task_type_id": tid},
                )

        raw = _json.dumps(tasks, sort_keys=True, ensure_ascii=False).encode()
        bulk_resource_id = int(hashlib.sha256(raw).hexdigest()[:8], 16) % (2**31)

        preview = [
            {"index": i,
             "task_type": tt_map.get(int(t["task_type_id"])) and tt_map[int(t["task_type_id"])].name,  # type: ignore[call-overload]  # type: ignore[index]
             "subject": t.get("subject")}
            for i, t in enumerate(tasks)
        ]

        if dry_run:
            return {"dry_run": True, "count": len(tasks), "preview": preview}

        if confirmation_token:
            canonical: dict[str, object] = {"tasks": tasks}
            await confirmations.consume(
                token=confirmation_token, op="bulk_create",
                resource_id=bulk_resource_id, payload=canonical,
            )
            created = await bulk_create_my_tasks(tasks)
            return {"created": len(created), "task_ids": [t.id for t in created]}

        canonical2: dict[str, object] = {"tasks": tasks}
        tok = await confirmations.issue("bulk_create", bulk_resource_id, canonical2)
        return {"preview": preview, "confirmation_token": tok,
                "expires_in_seconds": confirmations.TOKEN_TTL,
                "note": f"Call again with confirmation_token='{tok}' to create."}

    @server.tool()
    @mutating
    async def bulk_delete_tasks(
        task_ids: list[int],
        confirmation_token: str = "",
        dry_run: bool = False,
    ) -> dict[str, object]:
        """Delete multiple W_EDYCJI (draft) tasks at once.

        Step 1 (no token): previews + issues confirmation token.
        Step 2 (with token): executes the deletes.
        Tasks not in W_EDYCJI are silently skipped.

        Args:
            task_ids:           Task IDs to delete.
            confirmation_token: Token from step 1.
            dry_run:            Preview without issuing token.
        """
        import asyncio as _asyncio  # noqa: PLC0415
        import hashlib  # noqa: PLC0415
        import json as _json  # noqa: PLC0415

        from mcp_emp.core import confirmations  # noqa: PLC0415
        from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415
        from mcp_emp.domains.rejestr.status import Status  # noqa: PLC0415

        if not task_ids:
            raise ValidationFailed("task_ids must not be empty.", {})

        fetched = await _asyncio.gather(
            *[fetch_task(tid) for tid in task_ids], return_exceptions=True
        )
        deletable, skipped = [], []
        for tid, result in zip(task_ids, fetched, strict=False):
            if isinstance(result, BaseException):
                skipped.append({"task_id": tid, "reason": str(result)})
            elif isinstance(result, Task) and result.status != Status.W_EDYCJI:
                skipped.append({"task_id": tid, "reason": f"status={result.status}"})
            elif isinstance(result, Task):
                deletable.append(result)

        preview = [{"task_id": t.id, "subject": t.subject} for t in deletable]

        if dry_run:
            return {"dry_run": True, "would_delete": len(deletable),
                    "preview": preview, "skipped": skipped}

        sorted_ids = sorted(t.id for t in deletable)
        raw = _json.dumps(sorted_ids).encode()
        bulk_resource_id = int(hashlib.sha256(raw).hexdigest()[:8], 16) % (2**31)

        if confirmation_token:
            canonical: dict[str, object] = {"task_ids": sorted_ids}
            await confirmations.consume(
                token=confirmation_token, op="bulk_del",
                resource_id=bulk_resource_id, payload=canonical,
            )
            results = await bulk_delete_my_tasks([t.id for t in deletable])
            return {"deleted": sum(1 for v in results.values() if v == "deleted"),
                    "results": results, "skipped": skipped}

        canonical2: dict[str, object] = {"task_ids": sorted_ids}
        tok = await confirmations.issue("bulk_del", bulk_resource_id, canonical2)
        return {"would_delete": len(deletable), "preview": preview, "skipped": skipped,
                "confirmation_token": tok, "expires_in_seconds": confirmations.TOKEN_TTL,
                "note": f"Call again with confirmation_token='{tok}' to delete."}

    # ── P3: Templates ─────────────────────────────────────────────────────────

    @server.tool()
    @readable
    async def list_templates(search: str = "") -> list[dict[str, object]]:
        """List saved task templates (created via: mcp-emp template add <name> ...).

        Args:
            search: Substring filter on template name.
        """
        from pathlib import Path  # noqa: PLC0415

        from mcp_emp.core.config import get_settings  # noqa: PLC0415
        from mcp_emp.core.templates.db import list_templates as _lt  # noqa: PLC0415
        from mcp_emp.core.templates.db import open_templates_db  # noqa: PLC0415

        s = get_settings()
        conn = open_templates_db(Path(s.templates_db_path).expanduser())
        return [{"name": t.name, "task_type_id": t.task_type_id,
                 "subject_template": t.subject_template,
                 "notes_template": t.notes_template,
                 "deadline_offset_days": t.deadline_offset_days,
                 "tag_ids": t.tag_ids}
                for t in _lt(conn, search=search)]

    @server.tool()
    @mutating
    async def apply_template(
        name: str,
        subject: str = "",
        deadline: str = "",
        dry_run: bool = False,
    ) -> dict[str, object]:
        """Create a task from a saved template.

        Supports {today}/{date} and {cycle} in subject/notes templates.
        Manage: mcp-emp template add|list|delete

        Args:
            name:     Template name (from list_templates).
            subject:  Override the template subject.
            deadline: Override the template deadline (ISO 8601).
            dry_run:  Preview without creating.
        """
        from pathlib import Path  # noqa: PLC0415

        from mcp_emp.core.config import get_settings  # noqa: PLC0415
        from mcp_emp.core.errors import ValidationFailed  # noqa: PLC0415
        from mcp_emp.core.templates.db import get_template, open_templates_db  # noqa: PLC0415

        s = get_settings()
        conn = open_templates_db(Path(s.templates_db_path).expanduser())
        tmpl = get_template(conn, name)
        if not tmpl:
            raise ValidationFailed(
                f"Template not found: {name}. Use list_templates().",
                {"name": name},
            )
        rendered = tmpl.render(subject_override=subject or None,
                               deadline_override=deadline or None)
        if dry_run:
            return {"dry_run": True, "template": name, "would_create": rendered}

        task = await create_my_task(
            task_type_id=int(rendered["task_type_id"]),  # type: ignore[call-overload]
            subject=rendered.get("subject") or None,  # type: ignore[arg-type]
            deadline=rendered.get("deadline") or None,  # type: ignore[arg-type]
            notes=rendered.get("notes") or None,  # type: ignore[arg-type]
            tag_ids=rendered.get("tag_ids") or None,  # type: ignore[arg-type]
        )
        return {"created": True, "template": name, "task_id": task.id,
                "subject": task.subject, "status": task.status}


    # ── Direct DB: backdate ──────────────────────────────────────────────────

    @server.tool()
    @mutating
    async def backdate_task(
        task_id: int,
        target_date: str,
        set_completion_date: bool = False,
    ) -> dict[str, object]:
        """Set historical dates on a task directly in the EMP PostgreSQL database.

        Used for retroactively logging tasks from previous months.
        The API cannot change data_zlecenia retroactively after completion
        (Zakoncz overwrites it), so this tool goes directly to the DB.

        Requires MCP_EMP_DB_HOST / DB_USER / DB_PASS / DB_DATABASE in .env.

        Sets:
          data_zlecenia, data_rozpoczecia, data_gotowe, data_przydzielenia
          data_zakonczenia (only when set_completion_date=True)

        Note: nr_cyklu is NOT changed — EMP assigned the current cycle at
        creation/completion time. Cycle-based stats will show the task in the
        current cycle regardless of date.

        Args:
            task_id:              EMP task ID to backdate.
            target_date:          Target date — ISO 8601 or YYYY-MM-DD
                                  (e.g. '2026-01-15' or '2026-01-15T09:00:00').
            set_completion_date:  When True, also sets data_zakonczenia to
                                  target_date (useful for completed tasks).

        Returns:
            Confirmation with updated date fields from the database.
        """
        from mcp_emp.core.emp_db import backdate_rejestr  # noqa: PLC0415
        result = await backdate_rejestr(
            task_id, target_date, set_zakonczenia=set_completion_date
        )
        return dict(result)

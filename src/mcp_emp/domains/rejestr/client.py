"""Rejestr async HTTP client — read + write operations."""

from __future__ import annotations

from mcp_emp.core.auth import get_auth
from mcp_emp.core.errors import EmpRejected, InvalidTransition, TaskNotFound
from mcp_emp.core.http import get_client
from mcp_emp.domains.rejestr.contract import (
    RejestrDetailWrapperPayload,
    RejestrListPayload,
    Task,
)
from mcp_emp.domains.rejestr.mapper import map_task_from_detail, map_task_from_list


async def _bearer() -> dict[str, str]:
    token = await get_auth().get_token()
    return {"Authorization": f"Bearer {token}"}


# ── Read ──────────────────────────────────────────────────────────────────────

async def fetch_my_tasks(scope: str = "moje") -> list[Task]:
    """Fetch tasks from EMP.

    scope: "moje" (active only) | "moje-wszystkie" (all history)
    """
    path = f"/rejestr/lista/{scope}"
    r = await get_client().get(path, headers=await _bearer())
    if r.status_code == 404:
        raise TaskNotFound(0)
    if r.status_code != 200:
        raise EmpRejected(
            f"EMP returned {r.status_code} for {path}",
            {"status_code": r.status_code, "body": r.text[:200]},
        )
    payload = RejestrListPayload.model_validate(r.json())
    return [map_task_from_list(p) for p in payload.list]


async def fetch_task(task_id: int) -> Task:
    """Fetch a single task by ID."""
    r = await get_client().get(
        f"/rejestr/{task_id}", headers=await _bearer()
    )
    if r.status_code == 404:
        raise TaskNotFound(task_id)
    if r.status_code != 200:
        raise EmpRejected(
            f"EMP returned {r.status_code} for /rejestr/{task_id}",
            {"task_id": task_id, "status_code": r.status_code},
        )
    wrapper = RejestrDetailWrapperPayload.model_validate(r.json())
    return map_task_from_detail(wrapper.item)


# ── Write ─────────────────────────────────────────────────────────────────────

async def create_my_task(
    task_type_id: int,
    subject: str | None = None,
    deadline: str | None = None,
    notes: str | None = None,
    url: str | None = None,
    sod_number: str | None = None,
    sod_letter: str | None = None,
    quantity: float | None = None,
    time: str | None = None,
    tag_ids: list[int] | None = None,
    parent_id: int | None = None,
) -> Task:
    """POST /rejestr/moje — create and immediately start a task.

    EMP auto-sets: status=REALIZOWANE, points/weight from task type,
    created_user_id=assigned_user_id=current user, timestamps.
    Returns the full Task fetched after creation.
    """
    body: dict[str, object] = {"slownik_typ_zadania_id": task_type_id}
    if subject is not None:
        body["dotyczy"] = subject
    if deadline is not None:
        body["data_termin"] = deadline
    if notes is not None:
        body["uwagi"] = notes
    if url is not None:
        body["url"] = url
    if sod_number is not None:
        body["nr_sprawy_sod"] = sod_number
    if sod_letter is not None:
        body["nr_pisma_sod"] = sod_letter
    if quantity is not None:
        body["ilosc"] = quantity
    if time is not None:
        body["czas"] = time
    if tag_ids is not None:
        body["tags"] = tag_ids
    if parent_id is not None:
        body["rejestr_id"] = parent_id

    r = await get_client().post(
        "/rejestr/moje",
        json=body,
        headers=await _bearer(),
    )
    if r.status_code != 200:
        raise EmpRejected(
            f"EMP rejected create: {r.status_code}",
            {"status_code": r.status_code, "body": r.text[:300]},
        )
    resp = r.json()
    task_id = resp.get("id")
    if not task_id:
        raise EmpRejected(
            "EMP create response missing id",
            {"body": str(resp)[:200]},
        )
    return await fetch_task(int(task_id))


async def complete_my_task(
    task_id: int,
    time: str | None = None,
    quantity: float | None = None,
) -> Task:
    """PUT /rejestr/zakoncz — complete a task.

    EMP transitions:
      REALIZOWANE + requires_evaluation → DO_OCENY
      REALIZOWANE (no evaluation)       → ZAKOŃCZONE
      DO_OCENY                          → ZAKOŃCZONE
    Returns the updated Task fetched after completion.
    """
    body: dict[str, object] = {"id": task_id}
    if time is not None:
        body["czas"] = time
    if quantity is not None:
        body["ilosc"] = quantity

    r = await get_client().put(
        "/rejestr/zakoncz",
        json=body,
        headers=await _bearer(),
    )
    if r.status_code == 404:
        raise TaskNotFound(task_id)
    if r.status_code != 200:
        try:
            msg = r.json().get("message", r.text[:200])
        except Exception:  # noqa: BLE001
            msg = r.text[:200]
        raise EmpRejected(
            f"EMP rejected complete: {msg}",
            {"task_id": task_id, "status_code": r.status_code, "message": msg},
        )
    return await fetch_task(task_id)


async def edit_my_task(
    task_id: int,
    subject: str | None = None,
    deadline: str | None = None,
    notes: str | None = None,
    url: str | None = None,
    sod_number: str | None = None,
    sod_letter: str | None = None,
    quantity: float | None = None,
    time: str | None = None,
    tag_ids: list[int] | None = None,
) -> Task:
    """PUT /rejestr — update task fields (any non-ZAKOŃCZONE task).

    Returns the updated task fetched after the edit.
    """
    body: dict[str, object] = {"id": task_id}
    if subject is not None:
        body["dotyczy"] = subject
    if deadline is not None:
        body["data_termin"] = deadline
    if notes is not None:
        body["uwagi"] = notes
    if url is not None:
        body["url"] = url
    if sod_number is not None:
        body["nr_sprawy_sod"] = sod_number
    if sod_letter is not None:
        body["nr_pisma_sod"] = sod_letter
    if quantity is not None:
        body["ilosc"] = quantity
    if time is not None:
        body["czas"] = time
    if tag_ids is not None:
        body["tags"] = tag_ids

    r = await get_client().put("/rejestr", json=body, headers=await _bearer())
    if r.status_code == 404:
        raise TaskNotFound(task_id)
    if r.status_code != 200:
        try:
            msg = r.json().get("message", r.text[:200])
        except Exception:  # noqa: BLE001
            msg = r.text[:200]
        raise EmpRejected(
            f"EMP rejected edit: {msg}",
            {"task_id": task_id, "status_code": r.status_code, "message": msg},
        )
    return await fetch_task(task_id)


async def start_my_task(task_id: int) -> Task:
    """PUT /rejestr/realizuj — start a planned (PRZYDZIELONE) task.

    Transitions PRZYDZIELONE → REALIZOWANE.
    Returns the updated task.
    """
    r = await get_client().put(
        "/rejestr/realizuj", json={"id": task_id}, headers=await _bearer()
    )
    if r.status_code == 404:
        raise TaskNotFound(task_id)
    if r.status_code != 200:
        raise InvalidTransition(
            task_id=task_id, current="not PRZYDZIELONE", attempted="realizuj"
        )
    return await fetch_task(task_id)


async def delete_my_task(task_id: int) -> None:
    """DELETE /rejestr/{id} — permanently delete a W_EDYCJI task.

    Raises InvalidTransition when task is not W_EDYCJI or not found
    (EMP returns 422 for both cases without distinction).
    """
    r = await get_client().delete(
        f"/rejestr/{task_id}",
        headers=await _bearer(),
    )
    if r.status_code == 200:
        return
    if r.status_code in (404, 422):
        raise InvalidTransition(
            task_id=task_id,
            current="not W_EDYCJI or not found",
            attempted="usun",
        )
    raise EmpRejected(
        f"EMP rejected delete: {r.status_code}",
        {"task_id": task_id, "status_code": r.status_code},
    )


async def reject_my_task(task_id: int, reason: str | None = None) -> Task:
    """PUT /rejestr/odrzuc — reject a REALIZOWANE task back to OCZEKUJĄCE.

    Clears assigned_user_id so the task sits in queue.
    Returns the updated task.
    """
    body: dict[str, object] = {"id": task_id}
    if reason:
        body["uzasadnienie_odrzucenia"] = reason
    r = await get_client().put("/rejestr/odrzuc", json=body, headers=await _bearer())
    if r.status_code == 404:
        raise TaskNotFound(task_id)
    if r.status_code != 200:
        try:
            msg = r.json().get("message", r.text[:200])
        except Exception:  # noqa: BLE001
            msg = r.text[:200]
        raise EmpRejected(
            f"EMP rejected odrzuc: {msg}",
            {"task_id": task_id, "status_code": r.status_code, "message": msg},
        )
    return await fetch_task(task_id)


async def withdraw_my_task(task_id: int) -> Task:
    """PUT /rejestr/wycofaj — withdraw OCZEKUJĄCE task back to W_EDYCJI.

    Returns the updated task.
    """
    r = await get_client().put(
        "/rejestr/wycofaj", json={"id": task_id}, headers=await _bearer()
    )
    if r.status_code == 404:
        raise TaskNotFound(task_id)
    if r.status_code != 200:
        raise EmpRejected(
            f"EMP rejected wycofaj: {r.status_code}",
            {"task_id": task_id, "status_code": r.status_code},
        )
    return await fetch_task(task_id)


async def fetch_team_tasks(scope: str = "") -> list[Task]:
    """Fetch team tasks visible to kierownik.

    scope: "" (active only) | "moje-wszystkie" (full history)
    """
    path = f"/rejestr/kierownik/lista/{scope}" if scope else "/rejestr/kierownik/lista"
    r = await get_client().get(path, headers=await _bearer())
    if r.status_code != 200:
        raise EmpRejected(
            f"EMP {r.status_code} on {path}",
            {"status_code": r.status_code, "body": r.text[:200]},
        )
    payload = RejestrListPayload.model_validate(r.json())
    return [map_task_from_list(p) for p in payload.list]

# Tools Reference

All 13 tools exposed by mcp-emp.  Every mutating tool supports `dry_run=true`
to preview the operation without calling EMP.

---

## health_check

Check EMP API reachability and Keycloak auth status.

**Parameters:** none

**Returns:** `HealthStatus`

```json
{
  "emp_api": "reachable",
  "auth": "valid",
  "user": {
    "username": "stect",
    "display_name": "Tomasz Steć",
    "unit": "CI",
    "team": "CI-PRS",
    "roles": ["rejestr_modyfikacja", "kierownik_podglad", "..."]
  }
}
```

---

## list_task_types

List available task types from the EMP dictionary.  Results cached 10 minutes.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `search` | string | `""` | Case-insensitive substring filter on name. |
| `team_id` | string | `""` | Filter by team (e.g. `CI-PRS`). |

**Returns:** `list[TaskType]` sorted by name.

Each item:
```json
{
  "id": 28,
  "name": "Drobna poprawka/zmiana",
  "team_id": "CI-PRS",
  "subteam_id": null,
  "requires_quantity": false,
  "requires_time": false,
  "requires_evaluation": false,
  "is_container": false,
  "points": 2,
  "description": "Usprawnienie/zmiana działania..."
}
```

---

## list_tags

List available tags.  Results cached 5 minutes.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `search` | string | `""` | Substring filter on tag name. |
| `full` | bool | `false` | Include inactive/archived tags. |

**Returns:** `list[Tag]` sorted by name.

```json
{ "id": 5, "name": "AI" }
```

---

## list_my_tasks

List tasks assigned to me.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `scope` | string | `"active"` | `"active"` — open tasks only; `"all"` — full history. |
| `status` | string | `""` | Filter by status. Accepts Polish (`ZAKOŃCZONE`) or English aliases (`completed`, `draft`, `in_progress`, `pending_review`, `rejected`, `withdrawn`). |
| `search` | string | `""` | Substring filter on subject. |
| `sod_number` | string | `""` | Substring filter on SOD case number. |
| `limit` | int | `50` | Max results (hard cap: 500). |

**Returns:** `list[Task]` newest first.

Each `Task`:
```json
{
  "id": 134343,
  "subject": "eDrogi - poprawka eksportu raportów do PDF",
  "status": "ZAKOŃCZONE",
  "status_explained": "completed",
  "cycle": 2568,
  "task_type": {
    "id": 28, "name": "Drobna poprawka/zmiana",
    "requires_quantity": false, "requires_time": false, "requires_evaluation": false
  },
  "assigned_to": "Tomasz Steć",
  "created_by": "Tomasz Steć",
  "ordered_at": "2026-04-08T10:15:33",
  "deadline": null,
  "started_at": "2026-04-08T10:15:33",
  "completed_at": "2026-04-08T10:38:18",
  "quantity": 1,
  "time": null,
  "points": 2,
  "sod_number": null,
  "url": "https://mantis.slaskie.pl/view.php?id=8185",
  "notes": null,
  "parent_id": null,
  "tags": ["AI"],
  "open_children": 0,
  "permissions": null
}
```

> `permissions` is `null` in list results. Use `get_task` to get the permissions block.

---

## get_task

Fetch full detail of a single task including permissions.

| Parameter | Type | Description |
|---|---|---|
| `task_id` | int | EMP task ID. |

**Returns:** `Task` with `permissions` populated:

```json
{
  "...same as list_my_tasks...",
  "permissions": {
    "can_complete": false,
    "can_delete": false,
    "can_edit": false,
    "can_start": false
  },
  "rejection_reason": null,
  "correction_reason": null
}
```

**Permissions matrix:**

| Status | can_start | can_edit | can_delete | can_complete |
|---|---|---|---|---|
| `W_EDYCJI` | ✅ | ✅ | ✅ | ❌ |
| `REALIZOWANE` | ❌ | ❌ | ❌ | ✅ |
| `DO_OCENY` | ❌ | ❌ | ❌ | ✅ |
| `ZAKOŃCZONE` | ❌ | ❌ | ❌ | ❌ |
| `ODRZUCONE` | ❌ | ❌ | ❌ | ❌ |

---

## add_my_task

Create a new task in EMP.  EMP immediately sets status to `REALIZOWANE`
(in progress) and auto-assigns points/weight from the task type.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task_type_id` | int | **required** | From `list_task_types()`. |
| `subject` | string | `""` | Task subject / description. |
| `deadline` | string | `""` | ISO 8601 date or datetime (`2026-06-30`). |
| `notes` | string | `""` | Internal notes (uwagi). |
| `url` | string | `""` | Related URL (e.g. Mantis ticket). |
| `sod_number` | string | `""` | SOD case number. |
| `sod_letter` | string | `""` | SOD letter number. |
| `quantity` | float\|null | `null` | Required when task type `requires_quantity`. |
| `time` | string | `""` | Time spent in `HH:MM` format. Required when task type `requires_time`. |
| `tag_ids` | list[int]\|null | `null` | Tag IDs from `list_tags()`. |
| `parent_id` | int\|null | `null` | Parent task ID for sub-tasks. |
| `dry_run` | bool | `false` | Validate + preview without creating. |

**Returns:** `TaskCreateResult`

```json
{
  "dry_run": false,
  "validated": {
    "task_type_id": 28,
    "task_type_name": "Drobna poprawka/zmiana",
    "requires_quantity": false,
    "requires_time": false,
    "quantity_provided": false,
    "time_provided": false,
    "tag_ids_valid": [5],
    "tag_ids_unknown": []
  },
  "task": { "...full Task object..." },
  "note": "Task created and set to REALIZOWANE (in progress)."
}
```

**Errors:**
- `VALIDATION_FAILED` — unknown `task_type_id`, unknown tag IDs, missing required quantity/time.
- `EMP_REJECTED` — EMP refused the write.
- `READ_ONLY` — server is in read-only mode.

---

## complete_task

Complete a task (transition to `DO_OCENY` or `ZAKOŃCZONE`).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task_id` | int | **required** | Task to complete. |
| `time` | string | `""` | Time in `HH:MM`. Required when task type needs it. |
| `quantity` | float\|null | `null` | Required when task type needs it. |
| `dry_run` | bool | `false` | Preview the transition without executing. |

**Transition logic:**

| Current status | Task type `requires_evaluation` | → New status |
|---|---|---|
| `REALIZOWANE` | No | `ZAKOŃCZONE` |
| `REALIZOWANE` | Yes | `DO_OCENY` |
| `DO_OCENY` | (any) | `ZAKOŃCZONE` |
| Anything else | — | `INVALID_TRANSITION` error |

**Returns:** `TaskCompleteResult`

```json
{
  "dry_run": false,
  "task_id": 134343,
  "from_status": "REALIZOWANE",
  "would_transition_to": "ZAKOŃCZONE",
  "task": { "...updated Task..." },
  "note": "Will transition: REALIZOWANE → ZAKOŃCZONE (completed)"
}
```

---

## delete_task

Delete a draft (`W_EDYCJI`) task permanently.  **Two-step operation.**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task_id` | int | **required** | Task to delete. Must be `W_EDYCJI`. |
| `confirmation_token` | string | `""` | Token from step 1. Empty = step 1 (preview). |
| `dry_run` | bool | `false` | Preview without issuing a token. |

### Step 1 — Preview (no token)

```json
{
  "deleted": false,
  "task_id": 99999,
  "preview": {
    "task_id": 99999,
    "subject": "Test task",
    "status": "W_EDYCJI",
    "task_type_name": "Spotkanie",
    "ordered_at": "2026-05-30T10:00:00"
  },
  "confirmation_token": "del_99999_a3f9c2b1",
  "expires_in_seconds": 300,
  "note": "Review the preview above, then call delete_task again with confirmation_token='del_99999_a3f9c2b1' to permanently delete. Token expires in 5 minutes."
}
```

### Step 2 — Execute (with token)

```json
{
  "deleted": true,
  "task_id": 99999,
  "note": "Task 99999 permanently deleted."
}
```

**Token properties:** 5-minute TTL · single-use · scoped to `(operation, task_id)` · payload-hash bound (prevents bait-and-switch).

---

## get_my_profile

Get the current user's EMP profile.

**Parameters:** none

```json
{
  "id": 3,
  "username": "stect",
  "email": "tomasz.stec@slaskie.pl",
  "first_name": "Tomasz",
  "last_name": "Steć",
  "phone": null,
  "unit": "CI",
  "team": "CI-PRS",
  "subteam": null
}
```

---

## get_my_permissions

Get the current user's EMP permission list.

**Parameters:** none

```json
{
  "user_id": 3,
  "has_subteams": false,
  "permissions": [
    "rejestr_modyfikacja",
    "rejestr_podglad",
    "kierownik_podglad",
    "slowniki_modyfikacja",
    "..."
  ]
}
```

---

## list_users

List EMP users visible to the current user.  Requires `uzytkownicy_podglad`
permission; returns an empty list if the user lacks it.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `search` | string | `""` | Substring filter on username, first or last name. |
| `team_id` | string | `""` | Filter by team ID (e.g. `CI-PRS`). |

```json
[
  {
    "id": 1,
    "username": "bochynskid",
    "email": "dariusz.bochynski@slaskie.pl",
    "first_name": "Dariusz",
    "last_name": "Bochyński",
    "unit": "CI",
    "team": "CI-PRS",
    "subteam": null,
    "is_manager": false,
    "symbol": 5096,
    "permissions": ["rejestr_modyfikacja", "..."]
  }
]
```

---

## get_cycle_stats

Get point totals per EMP cycle (billing period).

**Parameters:** none

```json
{
  "cycles": [
    { "cycle": 2622, "points_default": 82, "points_manager": 82, "points_employee": 82 },
    { "cycle": 2621, "points_default": 100, "points_manager": 100, "points_employee": 100 }
  ]
}
```

---

## get_daily_stats

Get today's completed tasks and point summary.  Useful for standup notes.

**Parameters:** none

```json
{
  "date": "2026-05-30",
  "total_tasks": 3,
  "total_points": 7.0,
  "tasks": [
    {
      "id": 151558,
      "task_type": "Spotkanie",
      "subject": "emp mcp",
      "started_at": "2026-05-30 16:21:48",
      "completed_at": "2026-05-30 16:22:09",
      "points": 1,
      "points_weighted": 1,
      "quantity": 1,
      "time": null,
      "sod_number": null,
      "tags": []
    }
  ]
}
```

---

## Error codes

All errors carry a machine-readable `code` in `error.data.code`:

| Code | Meaning |
|---|---|
| `AUTH_MISCONFIGURED` | KC credentials wrong or realm unreachable. Startup fatal. |
| `AUTH_EXPIRED` | KC token could not be refreshed. |
| `EMP_UNREACHABLE` | EMP API is not responding. |
| `EMP_PARSE_ERROR` | EMP returned an unexpected shape. |
| `EMP_REJECTED` | EMP rejected the request (non-auth 4xx). |
| `TASK_NOT_FOUND` | Task does not exist or is not accessible. |
| `INVALID_TRANSITION` | Status transition not allowed. |
| `VALIDATION_FAILED` | Pre-flight validation failed; EMP was not called. |
| `CONFIRMATION_REQUIRED` | Destructive operation needs a confirmation token. |
| `CONFIRMATION_INVALID` | Token expired, already used, or payload-hash mismatch. |
| `READ_ONLY` | Server is in read-only mode. |

---

## bulk_create_tasks

Create multiple tasks at once with a two-step confirmation.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tasks` | list[dict] | **required** | Each dict: `task_type_id` (required), `subject`, `deadline`, `notes`, `url`, `sod_number`, `tag_ids`. |
| `confirmation_token` | string | `""` | Token from step 1. Empty = step 1. |
| `dry_run` | bool | `false` | Validate and preview without issuing a token. |

**Step 1 response:**
```json
{
  "preview": [{"index": 0, "task_type": "Spotkanie", "subject": "Daily standup"}],
  "confirmation_token": "bulk_create_...",
  "expires_in_seconds": 300,
  "note": "Call again with confirmation_token='...' to create."
}
```

**Step 2 response:**
```json
{ "created": 3, "task_ids": [151600, 151601, 151602] }
```

---

## bulk_delete_tasks

Delete multiple W_EDYCJI (draft) tasks with two-step confirmation.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task_ids` | list[int] | **required** | Task IDs to delete. Non-W_EDYCJI tasks are silently skipped. |
| `confirmation_token` | string | `""` | Token from step 1. |
| `dry_run` | bool | `false` | Preview without issuing a token. |

---

## list_templates

List saved task templates. Templates are managed via `mcp-emp template` CLI.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `search` | string | `""` | Substring filter on template name. |

```json
[
  {
    "name": "daily_standup",
    "task_type_id": 28,
    "subject_template": "Standup {today}",
    "deadline_offset_days": null,
    "tag_ids": [1]
  }
]
```

---

## apply_template

Create a task from a saved template.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | **required** | Template name from `list_templates`. |
| `subject` | string | `""` | Override the template subject. |
| `deadline` | string | `""` | Override the deadline (ISO 8601). |
| `dry_run` | bool | `false` | Preview without creating. |

**Template variables** (in subject/notes):
- `{today}` or `{date}` — today's date (`2026-05-30`)
- `{cycle}` — current EMP cycle number

---

## detect_recurring_tasks

Find task types that appear repeatedly in history.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `min_count` | int | `3` | Minimum occurrences to be considered recurring. |

```json
[
  {
    "task_type_id": 28,
    "task_type_name": "Drobna poprawka/zmiana",
    "count": 47,
    "avg_points": 2.0,
    "example_subject": "eDrogi - poprawka...",
    "suggested_subject": "Edrogid Poprawka"
  }
]
```

---

## suggest_task_completions

Rank REALIZOWANE tasks by completion urgency.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | `10` | Max suggestions to return. |

**Scoring:** overdue > near-deadline (≤3 days) > high points (≥5) > long-running (≥7 days, no deadline).

```json
[
  {
    "task_id": 134500,
    "subject": "eDrogi bug fix",
    "score": 115.0,
    "reason": "overdue by 3 day(s)",
    "deadline": "2026-05-27",
    "days_running": 10
  }
]
```

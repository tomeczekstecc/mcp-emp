# 06 — Tool Surface Design

The contract the LLM sees. Drives everything else: docs 07 (data shapes),
08 (errors), 10 (modules), 11 (tests).

---

## Global conventions

Applied uniformly to every tool.

- **Naming:** `snake_case`, verb-first (`add_my_task`, `list_my_tasks`).
- **Parameter naming:** `snake_case` English. IDs end in `_id`. Dates are
  ISO 8601 strings.
- **Return envelope:** always a JSON object, never bare lists or strings.
  Top-level shape:
  ```json
  { "ok": true,  "data":  { ... } }
  { "ok": false, "error": { "code": "...", "message": "...", "details": {...} } }
  ```
- **Errors never raise** out of the tool — they're returned as `ok: false`.
  Full model in doc 08.
- **Read vs mutate:**
  - Read tools are pure, no extra params.
  - Mutating tools accept optional `dry_run: bool = false`.
  - Destructive tools (delete, bulk ops, reject) return a
    `confirmation_token` the LLM must echo back on a follow-up call.
- **Role gating:** if the authenticated user lacks the role required for a
  tool, that tool is **not registered** at MCP startup — the LLM never
  sees it. Avoids confusing "permission denied" mid-conversation.
- **Polish data values preserved.** `status: "W_EDYCJI"` stays Polish (it's
  an identifier). Where useful, an `_explained` sibling adds an English
  gloss: `status_explained: "in editing"`. Tool descriptions document the
  full enum.

---

## P0 tools (MVP)

Build order (each links to its section below):

1. [`health_check`](#tool-1--health_check) — connectivity + identity
2. `list_task_types` — dictionary (B12)
3. `list_tags` — dictionary (B12)
4. `list_my_tasks` — core list (B10)
5. `get_task` — detail (B9)
6. `add_my_task` — create (B1)
7. `complete_task` — mark done (B5)
8. `delete_task` — destructive (B8)

> Tools are added below as they are approved one-by-one.

---

## Tool 1 — `health_check`

**Area:** A5
**Status:** ✅ approved

**Purpose for LLM:**
> Verify the EMP backend is reachable and the current session is
> authenticated. Use this if other tools start failing or before a long
> batch operation.

**Parameters:** none.

**Returns (success):**
```json
{
  "ok": true,
  "data": {
    "emp_api": "reachable",
    "emp_version": "1.4.2",
    "auth": "valid",
    "token_expires_in_seconds": 287,
    "user": {
      "id": 42,
      "username": "tkowalski",
      "display_name": "Tomek Kowalski",
      "roles": ["pracownik", "kierownik"]
    }
  }
}
```

**Returns (failure):**
```json
{
  "ok": false,
  "error": {
    "code": "EMP_UNREACHABLE",
    "message": "EMP API did not respond within 5s at http://localhost:480/api"
  }
}
```

**Side effects:** none. May trigger a transparent token refresh internally.
**Safety:** no `dry_run`, no confirmation, no role gate (available to all).

**Backing endpoint:** `GET /api/health-check` (per `routes/App/HealthCheck.php`)
combined with the cached identity context (A3).

**Design notes:**
- Combines connectivity + identity so a single call gives the LLM
  everything it needs to recover from an unknown failure.
- `token_expires_in_seconds` lets the LLM decide whether a multi-step
  workflow is likely to span a token refresh.
- **No separate `whoami` tool** — identity is included here. If we later
  find the LLM calling `health_check` only for identity, we'll revisit.

---

## Tool 2 — `list_task_types`

**Area:** B12
**Status:** ✅ approved

**Purpose for LLM:**
> List all available task types (`słownik typów zadań`). Use this to find
> the `task_type_id` you need when creating a task, or to translate a
> task type id from another response into a human-readable name. Results
> are cached, so it's cheap to call repeatedly.

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | string | no | — | Substring filter on the Polish `name` (case-insensitive). |
| `include_inactive` | bool | no | `false` | Include deactivated types (`czy_aktywny = false`). |

**Returns (success):**
```json
{
  "ok": true,
  "data": {
    "count": 27,
    "task_types": [
      {
        "id": 1,
        "name": "Obsługa zgłoszenia zmiany właściciela projektu",
        "team_id": 3,
        "team_name": "Projekty",
        "default_points": 1,
        "default_weight": 1,
        "requires_quantity": false,
        "requires_time": true,
        "requires_evaluation": false,
        "active": true
      }
    ],
    "cached": true,
    "cache_age_seconds": 42
  }
}
```

**Side effects:** none. Read-only; served from in-memory cache when warm.
**Safety:** no `dry_run`, no confirmation, no role gate.

**Backing endpoint:** `GET /api/rejestr/slowniki/typ_zadania`.

**Field translation (EMP → tool output):**

| EMP field | Tool field | Notes |
|---|---|---|
| `nazwa` | `name` | preserved in Polish (data value) |
| `slownik_team_id` | `team_id` | + enriched `team_name` |
| `punkty_domyslne` | `default_points` | |
| `waga` | `default_weight` | |
| `czy_ilosciowy` | `requires_quantity` | bool from `"Tak"/"Nie"` |
| `czy_czasowy` | `requires_time` | bool from `"Tak"/"Nie"` |
| `czy_ocena_wykonania` | `requires_evaluation` | bool from `"Tak"/"Nie"` |
| `czy_aktywny` | `active` | bool |

**Design notes:**
- **Cache TTL:** 10 minutes, in-memory, per-process (consistent with Q3).
- `search` is **client-side** post-fetch filter on the cached list — keeps
  it simple and avoids round-trips for every variation.
- `team_name` enriched here (saves a second tool call); the dedicated
  `list_teams` tool stays the source of truth.
- `requires_evaluation: true` means `complete_task` will transition the
  task to `DO_OCENY` instead of `ZAKOŃCZONE` — cross-referenced from
  `complete_task`'s description.
- No explicit `refresh_cache` parameter for P0; cache is managed
  implicitly. Revisit if the LLM ends up wanting to force-refresh.

---

## Tool 3 — `list_tags`

**Area:** B12
**Status:** ✅ approved

**Purpose for LLM:**
> List all tags available in the task register. Use this to (a) find
> existing `tag_id`s to attach when creating a task, or (b) translate tag
> ids/names in task responses. Tags are user-created labels, so the set
> grows over time — results are cached briefly. To create a new tag, use
> `create_tag` (not yet available in P0).

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | string | no | — | Substring filter on tag `name` (case-insensitive). |
| `include_deleted` | bool | no | `false` | Include soft-deleted tags. |

**Returns (success):**
```json
{
  "ok": true,
  "data": {
    "count": 14,
    "tags": [
      { "id": 7,  "name": "pilne",       "color": "#cc3333", "deleted": false },
      { "id": 12, "name": "projekt-XYZ", "color": null,      "deleted": false }
    ],
    "cached": true,
    "cache_age_seconds": 18
  }
}
```

**Side effects:** none.
**Safety:** no `dry_run`, no confirmation, no role gate.

**Backing endpoint:**
- `GET /api/rejestr/tag` when `include_deleted=false`
- `GET /api/rejestr/tag/pelna-lista` when `include_deleted=true`

**Field translation:**

| EMP field | Tool field | Notes |
|---|---|---|
| `id` | `id` | |
| `nazwa` | `name` | Polish content preserved |
| `kolor` (if present) | `color` | hex string or `null` |
| `deleted_at` | `deleted` | bool: `true` if non-null |

**Design notes:**
- **Cache TTL:** 5 minutes (shorter than `list_task_types` since tags are
  user-created and change more often).
- Same pattern as `list_task_types`: client-side `search`, no explicit
  `refresh_cache`.
- `color` is best-effort — if EMP doesn't expose it, the field is always
  `null` and we may drop it later.
- Tag *create/edit/delete* tools (`tagUtworz`, `tagZapisz`, `tagUsun`) are
  **deferred to P1+**. P0 stance: "use existing tags, don't invent new
  ones" — avoids tag pollution from LLM experimentation.
- No `attached_to_task_id` filter — redundant with the inline `tags`
  field already present in `get_task` and `list_my_tasks`.

---

## Tool 4 — `list_my_tasks`

**Area:** B10 / B11
**Status:** ✅ approved

**Purpose for LLM:**
> List tasks assigned to me. By default returns only active tasks (those
> not yet completed). Use `scope: "all"` to include
> completed/rejected/withdrawn tasks for historical or analytical
> queries. Supports filtering and sorting client-side. Use this to find
> a specific task before acting on it (e.g. before `complete_task` or
> `delete_task`).

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `scope` | enum | no | `"active"` | `"active"` = exclude `ZAKOŃCZONE` (B10). `"all"` = include everything (B11). |
| `status` | string | no | — | Filter to one status. Accepts Polish identifier (`W_EDYCJI`, `REALIZOWANE`, `DO_OCENY`, `ZAKOŃCZONE`, `ODRZUCONE`, `WYCOFANE`) **or** English alias (`in_editing`, `in_progress`, `pending_evaluation`, `completed`, `rejected`, `withdrawn`). If set, implies `scope="all"`. |
| `task_type_id` | int | no | — | Filter to one task type. |
| `tag` | string | no | — | Filter to tasks bearing this tag name (case-insensitive). |
| `subject_contains` | string | no | — | Substring filter on `subject` (case-insensitive). |
| `sod_number` | string | no | — | Exact match on `sod_case_number` or `sod_letter_number`. |
| `created_after` | string (ISO date) | no | — | `ordered_at >= created_after`. |
| `created_before` | string (ISO date) | no | — | `ordered_at <= created_before`. |
| `deadline_before` | string (ISO date) | no | — | `deadline <= deadline_before`. Useful for "overdue" / "due this week". |
| `sort_by` | enum | no | `"id_desc"` | One of `"id_desc"`, `"id_asc"`, `"deadline_asc"`, `"ordered_at_desc"`. |
| `limit` | int | no | `100` | Max rows returned (client-side, after filtering). Hard cap: 500. |

**Returns (success):**
```json
{
  "ok": true,
  "data": {
    "count": 12,
    "truncated": false,
    "tasks": [
      {
        "id": 1234,
        "subject": "Obsługa zgłoszenia SOD-2024/123",
        "status": "REALIZOWANE",
        "status_explained": "in progress",
        "task_type_id": 1,
        "task_type_name": "Obsługa korespondencji",
        "assigned_user_id": 42,
        "created_user_id": 7,
        "cycle_number": 2520,
        "ordered_at": "2025-01-31T08:00:00",
        "deadline": "2025-02-07T17:00:00",
        "started_at": "2025-02-01T09:15:00",
        "ready_at": null,
        "finished_at": null,
        "default_points": 1,
        "manager_points": 2,
        "employee_points": 2,
        "weight": 1,
        "weighted_points": 2,
        "quantity": null,
        "time": "01:30",
        "sod_case_number": "SOD-2024/123",
        "sod_letter_number": null,
        "url": null,
        "notes": null,
        "tags": ["pilne", "projekt-XYZ"],
        "is_correction": false,
        "is_planned": true,
        "overdue": false
      }
    ]
  }
}
```

**Side effects:** none.
**Safety:** no `dry_run`, no confirmation, no role gate.

**Backing endpoint:**
- `GET /api/rejestr/lista/moje` when `scope="active"`
- `GET /api/rejestr/lista/moje-wszystkie` when `scope="all"`

**Field translation (EMP → tool output):**

| EMP field | Tool field |
|---|---|
| `dotyczy` | `subject` |
| `slownik_typ_zadania_id` | `task_type_id` |
| `slownik_typ_zadania_nazwa` | `task_type_name` |
| `nr_cyklu` | `cycle_number` |
| `data_zlecenia` | `ordered_at` |
| `data_termin` | `deadline` |
| `data_rozpoczecia` | `started_at` |
| `data_gotowe` | `ready_at` |
| `data_zakonczenia` | `finished_at` |
| `punkty_domyslne` | `default_points` |
| `punkty_przelozony` | `manager_points` |
| `punkty_pracownik` | `employee_points` |
| `waga` | `weight` |
| `punkty_wagi` | `weighted_points` |
| `ilosc` | `quantity` |
| `czas` | `time` (string `HH:MM` preserved) |
| `nr_sprawy_sod` | `sod_case_number` |
| `nr_pisma_sod` | `sod_letter_number` |
| `uwagi` | `notes` |
| `czy_poprawka` | `is_correction` (bool) |
| `czy_planowane` | `is_planned` (bool) |
| `status` | `status` (Polish identifier preserved) + `status_explained` |

**Computed / enriched fields:**
- `status_explained` — English gloss of the status enum.
- `overdue` — `deadline` is in the past **and** status not in
  {`ZAKOŃCZONE`, `ODRZUCONE`, `WYCOFANE`}.
- `truncated` — `true` if more rows existed than `limit` after filtering.

**Status alias map (input only):**

| English alias | Polish identifier |
|---|---|
| `in_editing` | `W_EDYCJI` |
| `in_progress` | `REALIZOWANE` |
| `pending_evaluation` | `DO_OCENY` |
| `completed` | `ZAKOŃCZONE` |
| `rejected` | `ODRZUCONE` |
| `withdrawn` | `WYCOFANE` |

Output always uses the Polish identifier in `status` + English gloss in
`status_explained`. This bi-directional rule applies to **every** tool
that accepts/returns a task status.

**Design notes:**
- **Filtering is client-side** (after fetch) because `GET /lista/moje`
  doesn't accept filter params (per the route definitions). If perf
  becomes an issue with large histories, push filters into EMP via the
  DataTable endpoint (`lista-dt/moje`) which does support params.
- `limit` default 100, hard cap 500 — keeps us under the "small payload"
  assumption from Q6.
- `task_type_name` denormalised onto every row to save the LLM a
  cross-reference to `list_task_types`.
- Assignee name/id is `me` here — omitted to reduce noise. Re-added in
  the future `list_team_tasks` tool (P1).

---

## Tool 5 — `get_task`

**Area:** B9
**Status:** ✅ approved

**Purpose for LLM:**
> Fetch full details of a single task by ID. Returns the same shape as
> one row from `list_my_tasks`, plus authorship/assignee names and a
> `permissions` block telling you which actions are currently legal on
> this task. Use this when you have an ID (from a previous list, a user
> reference, or `add_my_task`'s response) and need to inspect or confirm
> state before/after an operation.

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `task_id` | int | yes | — | The task's `id`. |

**Returns (success):**
```json
{
  "ok": true,
  "data": {
    "task": {
      "id": 1234,
      "subject": "Obsługa zgłoszenia SOD-2024/123",
      "status": "REALIZOWANE",
      "status_explained": "in progress",
      "task_type_id": 1,
      "task_type_name": "Obsługa korespondencji",
      "assigned_user": {
        "id": 42,
        "username": "tkowalski",
        "display_name": "Tomek Kowalski"
      },
      "created_user": {
        "id": 7,
        "username": "manager",
        "display_name": "Anna Nowak"
      },
      "cycle_number": 2520,
      "ordered_at": "2025-01-31T08:00:00",
      "deadline": "2025-02-07T17:00:00",
      "started_at": "2025-02-01T09:15:00",
      "ready_at": null,
      "finished_at": null,
      "default_points": 1,
      "manager_points": 2,
      "employee_points": 2,
      "weight": 1,
      "weighted_points": 2,
      "quantity": null,
      "time": "01:30",
      "sod_case_number": "SOD-2024/123",
      "sod_letter_number": null,
      "url": null,
      "notes": null,
      "tags": ["pilne", "projekt-XYZ"],
      "is_correction": false,
      "is_planned": true,
      "rejection_reason": null,
      "correction_reason": null,
      "parent_task_id": null,
      "overdue": false,
      "permissions": {
        "can_edit": false,
        "can_start": false,
        "can_complete": true,
        "can_delete": false,
        "can_reject": true,
        "can_withdraw": true
      }
    }
  }
}
```

**Notable failure codes:**
- `TASK_NOT_FOUND` — no task with that id, **or** it exists but the user
  can't see it. EMP doesn't distinguish; we don't either (don't leak
  existence of other users' tasks).
- `AUTH_EXPIRED` — token refresh failed.

**Side effects:** none.
**Safety:** no `dry_run`, no confirmation, no role gate.

**Backing endpoint:** `GET /api/rejestr/{rejestr_id}`.

**Field translation:** same map as Tool 4 (`list_my_tasks`), plus:

| EMP field | Tool field |
|---|---|
| `uzasadnienie_odrzucenia` | `rejection_reason` |
| `uzasadnienie_poprawy` | `correction_reason` |
| `rejestr_id` (parent on corrections) | `parent_task_id` |
| `created_user_id` + joined user | `created_user.{id, username, display_name}` |
| `assigned_user_id` + joined user | `assigned_user.{id, username, display_name}` |

**Computed / enriched fields:**
- `overdue` — same rule as Tool 4.
- `permissions` — derived from current user's role, task `status`, and
  task type's `requires_evaluation`:
  - `can_edit` — `status == W_EDYCJI` and user is creator
  - `can_start` — `status == W_EDYCJI` (or after `przydziel`) and user is assignee
  - `can_complete` — `status in {REALIZOWANE, DO_OCENY}` and user is assignee (or manager for `DO_OCENY`)
  - `can_delete` — `status == W_EDYCJI` (EMP enforces this in `Usun.php`)
  - `can_reject` — `status in {W_EDYCJI, REALIZOWANE}` and user is assignee
  - `can_withdraw` — mirrors EMP's rule (TBD by reading `Wycofaj.php` at build time)

**Design notes:**
- **`permissions` inlined** so the LLM can avoid suggesting illegal
  transitions in one read. Tiny payload, big UX win.
- **Composite `assigned_user` / `created_user` objects** instead of
  parallel `*_id` + `*_name` flat fields — cleaner shape for LLM
  reasoning, ~3 extra tokens per task.
- **`TASK_NOT_FOUND` indistinguishable from "hidden"** by design.
- **No `include_history` flag** — history goes through dedicated
  `get_task_history` (P1, feature B13). Keeps `get_task` cheap and
  predictable.
- **Always re-fetches** (no `if_modified_since`) — caching mutable data
  is a foot-gun; can revisit if it becomes a perf issue.

---

## Tool 6 — `add_my_task`

**Area:** B1 — **first write tool**; sets the pattern for every later mutation.
**Status:** ✅ approved

**Purpose for LLM:**
> Create a new task in your own register (`utworzMoje`). The task is
> created in `W_EDYCJI` status and is owned by you. Use `dry_run: true`
> to preview what would be created without committing. Required:
> `subject`, `task_type_id`. Other fields are optional but recommended
> if known (especially `time` when the task type requires it — check
> `list_task_types`'s `requires_time` flag).

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `subject` | string | yes | — | What the task is about (`dotyczy`). Free text. |
| `task_type_id` | int | yes | — | From `list_task_types`. Drives scoring and required fields at completion. |
| `deadline` | string (ISO) | no | — | When the task is due. |
| `notes` | string | no | — | Free-text notes / context (`uwagi`). |
| `time` | string `HH:MM` | no | — | Time spent. Required at completion if `task_type.requires_time`. |
| `quantity` | int | no | — | Item count. Required at completion if `task_type.requires_quantity`. |
| `weight` | int | no | task type default | Weight multiplier (`waga`). |
| `employee_points` | int | no | task type default | Self-assessed points. |
| `sod_case_number` | string | no | — | Linked SOD case number. |
| `sod_letter_number` | string | no | — | Linked SOD letter number. |
| `url` | string | no | — | External link. |
| `tag_ids` | int[] | no | `[]` | Tag ids from `list_tags`. |
| `is_planned` | bool | no | `true` | Whether this was planned vs. ad-hoc. |
| `dry_run` | bool | no | `false` | Validate + preview; don't commit. |

**Returns (success, `dry_run=false`):**
```json
{
  "ok": true,
  "data": {
    "created": true,
    "task_id": 1287,
    "task": { "/* same shape as get_task */": null }
  }
}
```

**Returns (success, `dry_run=true`):**
```json
{
  "ok": true,
  "data": {
    "created": false,
    "dry_run": true,
    "would_create": {
      "subject": "Spotkanie projektowe nt. migracji DB",
      "task_type_id": 5,
      "task_type_name": "Spotkanie / narada",
      "deadline": null,
      "time": "01:30",
      "quantity": null,
      "weight": 1,
      "manager_points": 1,
      "employee_points": 1,
      "weighted_points": 1,
      "tags": ["projekt-XYZ"],
      "status_after_create": "W_EDYCJI",
      "owner": {
        "id": 42,
        "username": "tkowalski",
        "display_name": "Tomek Kowalski"
      }
    },
    "warnings": []
  }
}
```

**Notable failure codes:**
- `VALIDATION_FAILED` — local pre-check (missing required field for this
  task type, malformed date, unknown `tag_ids`, etc.).
- `TASK_TYPE_NOT_FOUND` — `task_type_id` unknown or inactive.
- `TAG_NOT_FOUND` — one or more `tag_ids` don't exist.
- `EMP_REJECTED` — EMP returned 4xx; raw message in `details`.
- `AUTH_EXPIRED`.

**Side effects:** creates one task in EMP when `dry_run=false`.
**Idempotency:** none — calling twice creates two tasks. (See notes.)
**Safety:** `dry_run` supported; no confirmation token (create, not destructive); no role gate.

**Backing endpoint:** `POST /api/rejestr/moje`.

**Field translation (tool input → EMP body):**

| Tool field | EMP field |
|---|---|
| `subject` | `dotyczy` |
| `task_type_id` | `slownik_typ_zadania_id` |
| `deadline` | `data_termin` |
| `notes` | `uwagi` |
| `time` | `czas` (passed through `correctTime()`) |
| `quantity` | `ilosc` |
| `weight` | `waga` |
| `employee_points` | `punkty_pracownik` |
| `sod_case_number` | `nr_sprawy_sod` |
| `sod_letter_number` | `nr_pisma_sod` |
| `url` | `url` |
| `tag_ids` | `tags` |
| `is_planned` | `czy_planowane` |

EMP fills automatically: `nr_cyklu`, `data_zlecenia`, `created_user_id`,
`status = W_EDYCJI`, `punkty_wagi`, `punkty_przelozony` fallback.

**Design notes:**
- **Pre-validation against cache** — the tool checks `task_type_id` vs.
  cached `list_task_types`, validates `requires_time` /
  `requires_quantity`, validates `tag_ids` vs. cached `list_tags`.
  Failures return `VALIDATION_FAILED` *without* hitting EMP — faster
  feedback, cheaper tokens, no half-broken state.
- **Dry-run is local-only** — doesn't call EMP. Runs the same validation
  + enrichment pipeline and returns what *would* be sent. Zero EMP cost.
- **No idempotency key for P0.** If the LLM is unsure a previous call
  landed, it should `list_my_tasks` and check. Idempotency keys are
  deferred.
- **`created: true|false`** in the response disambiguates real vs. dry-run
  for the LLM without relying on the `dry_run` echo.
- **Full task object returned on real create** — saves the LLM a
  follow-up `get_task` call. Internally we may have to do one extra read
  if the EMP POST response is sparse.
- **`warnings` array in dry-run** — reserved for soft issues ("no
  deadline set", "task type usually expects a SOD number"). Empty in P0.
- **One-tool-one-action** — no `start_immediately` shortcut; the LLM
  chains explicitly. Future convenience tools (`add_and_complete_task`)
  can compose if friction emerges.
- **No `task_type_name` lookup** for P0 — too easy to silently pick the
  wrong type. LLM must call `list_task_types` and pass an id.

---

## Tool 7 — `complete_task`

**Area:** B5
**Status:** ✅ approved

**Purpose for LLM:**
> Mark a task as done (`zakoncz`). Requires the task to be in
> `REALIZOWANE` or `DO_OCENY` status. If the task type requires
> evaluation (`requires_evaluation: true`), this transitions the task
> to `DO_OCENY` (awaiting manager scoring); otherwise straight to
> `ZAKOŃCZONE`. Optionally update `time`, `quantity`, and
> `employee_points` before completion. Use `dry_run: true` to preview.

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `task_id` | int | yes | — | The task to complete. |
| `time` | string `HH:MM` | conditional | unchanged | **Required** if task type has `requires_time=true` and task lacks a value. |
| `quantity` | int | conditional | unchanged | **Required** if `requires_quantity=true` and task lacks a value. |
| `employee_points` | int | no | unchanged | Self-assessed points (`punkty_pracownik`). |
| `manager_points` | int | no | unchanged | Manager score (`punkty_przelozony`). Honoured only when current user is the evaluating manager. |
| `notes` | string | no | unchanged | **Overwrites** `uwagi` if provided. |
| `dry_run` | bool | no | `false` | Preview without committing. |

**Returns (success, real run):**
```json
{
  "ok": true,
  "data": {
    "completed": true,
    "task_id": 1234,
    "previous_status": "REALIZOWANE",
    "new_status": "DO_OCENY",
    "new_status_explained": "pending evaluation",
    "next_step": "Awaiting manager scoring; no further action needed from you.",
    "task": { "/* full task object, post-update */": null }
  }
}
```

**Returns (success, dry-run):**
```json
{
  "ok": true,
  "data": {
    "completed": false,
    "dry_run": true,
    "task_id": 1234,
    "current_status": "REALIZOWANE",
    "would_transition_to": "DO_OCENY",
    "would_apply": {
      "time": "02:15",
      "quantity": null,
      "employee_points": 2,
      "manager_points": null,
      "notes": null
    },
    "warnings": []
  }
}
```

**Notable failure codes:**
- `INVALID_TRANSITION` — task not in `REALIZOWANE` or `DO_OCENY`.
  `details` includes `current_status` + allowed source statuses.
- `VALIDATION_FAILED` — missing `time` / `quantity` for this task type.
- `TASK_NOT_FOUND` — unknown or hidden.
- `EMP_REJECTED` — EMP-side rejection passed through.
- `AUTH_EXPIRED`.

**Side effects:** transitions one task on real run. Triggers EMP domain
event `Zakonczone` (may notify others, recompute stats).
**Safety:** `dry_run` supported. **No confirmation token** — reversible
by re-opening / withdrawing; reserved tokens for destructive ops only.
No role gate.

**Backing endpoint:** `PUT /api/rejestr/zakoncz`.

**Field translation (tool input → EMP body):**

| Tool field | EMP field |
|---|---|
| `task_id` | `id` (or `rejestr_id` — confirm vs. `Zakoncz.php` at build) |
| `time` | `czas` |
| `quantity` | `ilosc` |
| `employee_points` | `punkty_pracownik` |
| `manager_points` | `punkty_przelozony` |
| `notes` | `uwagi` |

**Computed / enriched fields:**
- `next_step` — short English hint about what happens after:
  - to `ZAKOŃCZONE` → `"Task fully closed."`
  - to `DO_OCENY`   → `"Awaiting manager scoring; no further action needed from you."`
- `previous_status`, `new_status` — both echoed so the LLM doesn't need
  to re-read.

**Design notes:**
- **Pre-flight checks (no EMP write) before the PUT:**
  1. `get_task` — verify `permissions.can_complete`.
  2. Cache-lookup task type — enforce `requires_time` / `requires_quantity`.
  3. If anything missing → `VALIDATION_FAILED` (no EMP call).
- **Local target prediction** — `would_transition_to` derived from the
  task type's `requires_evaluation` flag. On real run we still trust
  EMP's actual response.
- **`manager_points` is conditionally honoured** — set freely; if the
  caller isn't the evaluating manager, EMP rejects and we surface
  `EMP_REJECTED`. Proper role-gated visibility is P1.
- **No confirmation token** — completion is a forward step in a normal
  workflow. `dry_run` is the safety net.
- **`notes` overwrites** (matches EMP PUT semantics). A future
  `append_notes` tool can append safely.
- **No auto-`start_task`** — two transitions in one tool would hide
  intent. LLM chains explicitly, or uses a future
  `add_and_complete_task` convenience tool.

---

## Tool 8 — `delete_task`

**Area:** B8 — **first destructive tool**; defines the
confirmation-token contract (E2) reused by all later destructive ops.
**Status:** ✅ approved

**Purpose for LLM:**
> Permanently delete a task (`usun`). Only allowed when the task is in
> `W_EDYCJI` status — EMP rejects deletion of started/completed tasks.
> This is a **two-step destructive operation**: first call with
> `dry_run: true` (or no `confirmation_token`) to receive a confirmation
> token; then call again with the same `task_id` and the
> `confirmation_token` to actually delete. Tokens are single-use and
> expire after 5 minutes.

**Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `task_id` | int | yes | — | Task to delete. |
| `confirmation_token` | string | no | — | Token from a prior preview call. Omit to receive one; provide to actually delete. |
| `dry_run` | bool | no | `false` | Force preview-only mode. Mostly redundant with the token flow; kept for symmetry. |

### Two-step flow

```
Call 1: delete_task(task_id=1234)
  → { ok: true, data: { deleted: false, requires_confirmation: true,
                         confirmation_token: "del_1234_a3f9...",
                         expires_at: "...", preview: {...} } }

Call 2: delete_task(task_id=1234, confirmation_token="del_1234_a3f9...")
  → { ok: true, data: { deleted: true, task_id: 1234,
                         previous_status: "W_EDYCJI" } }
```

**Returns (call 1 — preview / token issuance):**
```json
{
  "ok": true,
  "data": {
    "deleted": false,
    "requires_confirmation": true,
    "confirmation_token": "del_1234_a3f9c10e",
    "expires_at": "2026-05-30T12:34:56Z",
    "preview": {
      "task_id": 1234,
      "subject": "Spotkanie projektowe (draft)",
      "status": "W_EDYCJI",
      "task_type_name": "Spotkanie / narada",
      "ordered_at": "2025-05-20T08:00:00",
      "tags": ["projekt-XYZ"]
    },
    "warning": "Deletion is permanent and cannot be undone. Re-call with this confirmation_token within 5 minutes to commit."
  }
}
```

**Returns (call 2 — real delete):**
```json
{
  "ok": true,
  "data": {
    "deleted": true,
    "task_id": 1234,
    "previous_status": "W_EDYCJI"
  }
}
```

**Notable failure codes:**
- `INVALID_TRANSITION` — task not in `W_EDYCJI`. `details.current_status`
  included. Mirrors EMP `Usun.php`.
- `CONFIRMATION_INVALID` — token doesn't match `task_id`, was already
  used, or expired. `details.reason ∈ {"unknown", "used", "expired",
  "wrong_task"}`.
- `TASK_NOT_FOUND` — unknown or hidden.
- `EMP_REJECTED` — EMP-side rejection passed through.
- `AUTH_EXPIRED`.

**Side effects (call 2 only):** permanent task deletion. Triggers EMP
domain event `Usuniete`. **No recovery.**
**Safety:** confirmation token mandatory. No role gate (EMP enforces
ownership).

**Backing endpoint:** `DELETE /api/rejestr/{rejestr_id}`.

### Confirmation-token contract (E2 — used by **all** destructive tools)

| Field | Spec |
|---|---|
| Format | `<op>_<resource_id>_<random_hex>` (e.g. `del_1234_a3f9c10e`) |
| Storage | in-memory only (consistent with Q3); process-local dict |
| TTL | 5 minutes from issuance |
| Single-use | yes — committed tokens are immediately invalidated |
| Scope | bound to `(op, resource_id)` — `del_1234_...` cannot delete task `1235` |
| Generation | `secrets.token_hex(8)` |

This pattern is reused verbatim by future destructive tools (`reject_task`,
`bulk_delete_tasks`, etc.) and is the canonical instance of feature E2.

**Design notes:**
- **Pre-flight `get_task`** before issuing the token — populates
  `preview` and short-circuits with `INVALID_TRANSITION` if status isn't
  `W_EDYCJI` (no point handing out a token that can't be used).
- **Why a token instead of `confirm=true`?** A token forces the LLM to
  have *seen and reasoned about* the preview. A flag would let it just
  retry blindly. Token + preview = deliberate two-step.
- **5-minute TTL** — enough time to ask the user; short enough that
  stale plans don't execute later in a long session.
- **Single tool with optional token** (not two separate
  `preview_delete_task` + `confirm_delete_task` tools) — cleaner LLM
  surface, fewer tool descriptions to load.
- **Errors precede confirmation** — `TASK_NOT_FOUND` /
  `INVALID_TRANSITION` return errors on call 1, before any token issues.
- **No `force: true` escape hatch** — defeats the point of E2.
- **Expired tokens do not auto-renew** — re-preview is the safer default
  for P0.

---

## P0 — Tool surface complete

All 8 P0 tools are designed:

| # | Tool | Mutating? | Confirmation? |
|---|---|---|---|
| 1 | `health_check` | no | — |
| 2 | `list_task_types` | no | — |
| 3 | `list_tags` | no | — |
| 4 | `list_my_tasks` | no | — |
| 5 | `get_task` | no | — |
| 6 | `add_my_task` | yes | `dry_run` only |
| 7 | `complete_task` | yes | `dry_run` only |
| 8 | `delete_task` | yes (destructive) | **confirmation token** + `dry_run` |

What this surface delivers:
- **UC-1** *(Add what I just did)* — add + optional complete
- **UC-2** *(Mark X as done)* — list → find → complete
- **UC-3** *(Clean up obsolete drafts)* — list → filter → delete with confirmation

P1+ tools will be appended to this document as they are designed.

# 07 — Data Shapes

The internal data layer. Single source of truth for:
- EMP response shapes we depend on
- Field-translation table (EMP ↔ tool surface)
- Python types we'll use internally
- Date/time, null, encoding, and enum rules

> **Doc 06 is the *external* contract (LLM-facing). Doc 07 is the *internal*
> contract (Python ↔ EMP).** Any change here cascades into 06.

---

## 1. Layering

```
┌─────────────────────────────┐
│  MCP tool functions         │  ← Doc 06: external contract
│  (return dict envelopes)    │
└──────────────┬──────────────┘
               │ Python types (this doc)
┌──────────────▼──────────────┐
│  Domain layer               │  ← typed dataclasses
│  Task, TaskType, Tag, User  │
└──────────────┬──────────────┘
               │ translate(emp_dict) → Task
┌──────────────▼──────────────┐
│  EMP client (httpx)         │  ← raw EMP JSON dicts
└─────────────────────────────┘
```

Three layers, two boundaries:
- **EMP → domain:** parse + rename + enrich (single function per resource).
- **Domain → tool envelope:** serialise dataclasses to dicts; tool layer wraps in `{ok, data}`.

This isolation means: if EMP renames `dotyczy` to `temat` tomorrow, we change **one** translate function and **zero** tools.

---

## 2. Canonical EMP response shapes

What we currently believe EMP sends, based on reading the controllers and
DTOs. To be confirmed against live responses during P0 build.

### 2.1 `Rejestr` (task) — from `app/Domain/Rejestr/DTO/Rejestr.php`

```jsonc
{
  "id": 1234,
  "dotyczy": "Obsługa zgłoszenia SOD-2024/123",
  "status": "REALIZOWANE",
  "slownik_typ_zadania_id": 1,
  "slownik_typ_zadania_nazwa": "Obsługa korespondencji",   // joined
  "created_user_id": 7,
  "assigned_user_id": 42,
  "nr_cyklu": 2520,
  "data_zlecenia": "2025-01-31 08:00:00",
  "data_termin": "2025-02-07 17:00:00",
  "data_rozpoczecia": "2025-02-01 09:15:00",
  "data_gotowe": null,
  "data_zakonczenia": null,
  "punkty_domyslne": 1,
  "punkty_przelozony": 2,
  "punkty_pracownik": 2,
  "waga": 1,
  "punkty_wagi": 2,
  "ilosc": null,
  "czas": "01:30",
  "nr_sprawy_sod": "SOD-2024/123",
  "nr_pisma_sod": null,
  "url": null,
  "uwagi": null,
  "tags": [{"id": 7, "nazwa": "pilne"}, {"id": 12, "nazwa": "projekt-XYZ"}],
  "czy_poprawka": false,
  "czy_planowane": true,
  "uzasadnienie_odrzucenia": null,
  "uzasadnienie_poprawy": null,
  "rejestr_id": null,                                       // parent on corrections
  "rodzaj_zadania": "ZWYKLE"
}
```

**Open uncertainties** (resolve at first real call):
- Are `tags` returned as objects (`[{id, nazwa}]`) or just id arrays? We assume objects; degrade gracefully.
- Are joined fields like `slownik_typ_zadania_nazwa` always present, or only on detail endpoints?
- Date format — `"YYYY-MM-DD HH:MM:SS"` (Laravel default) vs ISO 8601? See §5.

### 2.2 `Słownik typu zadania` — from `routes/.../slowniki/typ_zadania`

```jsonc
{
  "id": 1,
  "nazwa": "Obsługa korespondencji",
  "slownik_team_id": 3,
  "punkty_domyslne": 1,
  "waga": 1,
  "czy_ilosciowy": "Nie",         // string "Tak"/"Nie"
  "czy_czasowy": "Tak",
  "czy_ocena_wykonania": "Nie",
  "czy_aktywny": true
}
```

### 2.3 `Tag` — from `routes/.../rejestr/tag`

```jsonc
{
  "id": 7,
  "nazwa": "pilne",
  "kolor": "#cc3333",       // may be absent
  "deleted_at": null
}
```

### 2.4 `User` — extracted from Keycloak token + EMP user join

EMP joins on `assigned_user_id` typically returning at least `id`,
`username` (= `name` claim from KC), and optionally a `display_name`.
We treat anything we can't get from EMP as `null`.

### 2.5 Error responses

EMP returns Laravel-style JSON on failure. Two observed shapes:

```jsonc
// Validation
{ "message": "The given data was invalid.", "errors": { "dotyczy": ["..."] } }

// Domain exception (InvalidDataException, AccessDeniedException)
{ "message": "Status nie pozwala na usunięcie zadania." }
```

Translation to our error envelope handled in doc 08.

---

## 3. Field-translation table — single source of truth

This table is **canonical**. Every translate function and every tool in
doc 06 derives from this. If a row changes, search the codebase for the
EMP name and update.

### 3.1 Task (`Rejestr`)

| EMP field | Python attr | Tool field | Type | Notes |
|---|---|---|---|---|
| `id` | `id` | `id` | `int` | |
| `dotyczy` | `subject` | `subject` | `str` | Polish content preserved |
| `status` | `status` | `status` | `Status` (enum) | + `status_explained` (computed) |
| `slownik_typ_zadania_id` | `task_type_id` | `task_type_id` | `int` | |
| `slownik_typ_zadania_nazwa` | `task_type_name` | `task_type_name` | `str \| None` | enriched from cache if EMP omits |
| `created_user_id` | `created_user_id` | `created_user.id` | `int` | |
| `assigned_user_id` | `assigned_user_id` | `assigned_user.id` | `int` | |
| `nr_cyklu` | `cycle_number` | `cycle_number` | `int` | |
| `data_zlecenia` | `ordered_at` | `ordered_at` | `datetime` | see §5 |
| `data_termin` | `deadline` | `deadline` | `datetime \| None` | |
| `data_rozpoczecia` | `started_at` | `started_at` | `datetime \| None` | |
| `data_gotowe` | `ready_at` | `ready_at` | `datetime \| None` | |
| `data_zakonczenia` | `finished_at` | `finished_at` | `datetime \| None` | |
| `punkty_domyslne` | `default_points` | `default_points` | `int` | |
| `punkty_przelozony` | `manager_points` | `manager_points` | `int \| None` | |
| `punkty_pracownik` | `employee_points` | `employee_points` | `int \| None` | |
| `waga` | `weight` | `weight` | `int` | |
| `punkty_wagi` | `weighted_points` | `weighted_points` | `int` | |
| `ilosc` | `quantity` | `quantity` | `int \| None` | |
| `czas` | `time` | `time` | `str \| None` | `"HH:MM"` preserved |
| `nr_sprawy_sod` | `sod_case_number` | `sod_case_number` | `str \| None` | |
| `nr_pisma_sod` | `sod_letter_number` | `sod_letter_number` | `str \| None` | |
| `url` | `url` | `url` | `str \| None` | |
| `uwagi` | `notes` | `notes` | `str \| None` | |
| `tags` | `tags` | `tags` | `list[str]` | names only in output |
| `czy_poprawka` | `is_correction` | `is_correction` | `bool` | |
| `czy_planowane` | `is_planned` | `is_planned` | `bool` | |
| `uzasadnienie_odrzucenia` | `rejection_reason` | `rejection_reason` | `str \| None` | |
| `uzasadnienie_poprawy` | `correction_reason` | `correction_reason` | `str \| None` | |
| `rejestr_id` | `parent_task_id` | `parent_task_id` | `int \| None` | |
| `rodzaj_zadania` | `kind` | (omitted from tool output) | `str` | internal use |
| — | `overdue` | `overdue` | `bool` | **computed** (§6) |
| — | — | `permissions` | `Permissions` | **computed**, only on `get_task` |

### 3.2 TaskType (`Słownik typu zadania`)

| EMP field | Python attr | Tool field | Type | Notes |
|---|---|---|---|---|
| `id` | `id` | `id` | `int` | |
| `nazwa` | `name` | `name` | `str` | |
| `slownik_team_id` | `team_id` | `team_id` | `int` | |
| — | `team_name` | `team_name` | `str \| None` | enriched from teams cache |
| `punkty_domyslne` | `default_points` | `default_points` | `int` | |
| `waga` | `default_weight` | `default_weight` | `int` | |
| `czy_ilosciowy` | `requires_quantity` | `requires_quantity` | `bool` | `"Tak"`→`True`, `"Nie"`→`False` |
| `czy_czasowy` | `requires_time` | `requires_time` | `bool` | same |
| `czy_ocena_wykonania` | `requires_evaluation` | `requires_evaluation` | `bool` | same |
| `czy_aktywny` | `active` | `active` | `bool` | may already be bool |

### 3.3 Tag

| EMP field | Python attr | Tool field | Type | Notes |
|---|---|---|---|---|
| `id` | `id` | `id` | `int` | |
| `nazwa` | `name` | `name` | `str` | |
| `kolor` | `color` | `color` | `str \| None` | best-effort |
| `deleted_at` | `deleted_at` | `deleted` | `bool` | `True` if non-null |

### 3.4 User

| Source | Python attr | Tool field | Type |
|---|---|---|---|
| KC `sub` / EMP `id` | `id` | `id` | `int` |
| KC `preferred_username` or `name` | `username` | `username` | `str` |
| EMP user join / KC `name` | `display_name` | `display_name` | `str \| None` |
| KC `realm_access.roles` ∩ known roles | `roles` | `roles` | `list[Role]` |

---

## 4. Python types

We use **`pydantic v2` BaseModels** (already implied by MCP SDK use of
pydantic for tool param validation). Two model flavours:

- **Domain models** — internal, full fidelity, typed.
- **Input models** — per tool, define accepted parameters.

Output is plain `dict` (via `.model_dump(mode="json", by_alias=False)`)
so the MCP envelope stays a simple JSON object.

### 4.1 Sketch

```python
# domain/types.py

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class Status(str, Enum):
    W_EDYCJI    = "W_EDYCJI"
    REALIZOWANE = "REALIZOWANE"
    DO_OCENY    = "DO_OCENY"
    ZAKONCZONE  = "ZAKOŃCZONE"      # value retains the Polish identifier
    ODRZUCONE   = "ODRZUCONE"
    WYCOFANE    = "WYCOFANE"

class Role(str, Enum):
    PRACOWNIK = "pracownik"
    KIEROWNIK = "kierownik"
    DYREKTOR  = "dyrektor"
    ZARZAD    = "zarzad"

class User(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    roles: list[Role] = []

class Tag(BaseModel):
    id: int
    name: str
    color: str | None = None
    deleted: bool = False

class TaskType(BaseModel):
    id: int
    name: str
    team_id: int
    team_name: str | None = None
    default_points: int
    default_weight: int
    requires_quantity: bool
    requires_time: bool
    requires_evaluation: bool
    active: bool

class Permissions(BaseModel):
    can_edit: bool
    can_start: bool
    can_complete: bool
    can_delete: bool
    can_reject: bool
    can_withdraw: bool

class Task(BaseModel):
    id: int
    subject: str
    status: Status
    task_type_id: int
    task_type_name: str | None = None
    assigned_user_id: int
    created_user_id: int
    assigned_user: User | None = None       # populated on get_task only
    created_user:  User | None = None
    cycle_number: int
    ordered_at:  datetime
    deadline:    datetime | None = None
    started_at:  datetime | None = None
    ready_at:    datetime | None = None
    finished_at: datetime | None = None
    default_points: int
    manager_points:  int | None = None
    employee_points: int | None = None
    weight: int
    weighted_points: int
    quantity: int | None = None
    time: str | None = None                 # "HH:MM"
    sod_case_number: str | None = None
    sod_letter_number: str | None = None
    url: str | None = None
    notes: str | None = None
    tags: list[str] = []
    is_correction: bool = False
    is_planned: bool = True
    rejection_reason: str | None = None
    correction_reason: str | None = None
    parent_task_id: int | None = None
    overdue: bool = False
    permissions: Permissions | None = None  # only on get_task

class ErrorEnvelope(BaseModel):
    code: str
    message: str
    details: dict | None = None

class ConfirmationToken(BaseModel):
    token: str
    op: str
    resource_id: int
    expires_at: datetime
```

### 4.2 Output envelope helpers

```python
def ok(data: dict | BaseModel) -> dict:
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    return {"ok": True, "data": data}

def err(code: str, message: str, details: dict | None = None) -> dict:
    payload = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return {"ok": False, "error": payload}
```

Used by every tool. Final shape is **always** one of these two.

---

## 5. Date & time handling

| Question | Rule |
|---|---|
| Incoming format from EMP | Laravel default: `"YYYY-MM-DD HH:MM:SS"` (space, no tz). |
| Tz interpretation | Assume **Europe/Warsaw local time**, naive. (EMP runs in PL.) |
| Internal type | `datetime` (naive, treated as Warsaw local). |
| Tool output format | ISO 8601 without tz: `"2025-02-07T17:00:00"` — matches what we showed in doc 06. |
| Date-only fields | None in P0 — every "date" field is actually a timestamp. |
| Outgoing format to EMP | Same as incoming: `"YYYY-MM-DD HH:MM:SS"`. |
| Accepted from LLM | Either `"YYYY-MM-DD"` or `"YYYY-MM-DDTHH:MM:SS"` or `"YYYY-MM-DD HH:MM:SS"`. Bare date → time defaults to `00:00:00`. |
| Time-of-day field (`czas`) | String `"HH:MM"`, **never** a datetime. Validated by regex. |

**Rationale for naive Warsaw-local:**
- EMP doesn't send timezone info; pretending otherwise risks off-by-an-hour bugs around DST.
- Single deployment context (one org, one timezone) — no benefit to UTC normalisation.
- We can revisit if EMP ever returns timezone info.

**Edge case:** during DST transitions, ambiguous wall-clock times exist
(02:30 happens twice in autumn). We accept whatever EMP sends; we do not
attempt to disambiguate. Logged as a known limitation.

---

## 6. Null & missing-field rules

| Scenario | Rule |
|---|---|
| EMP sends `null` | Map to `None` in the model. |
| EMP **omits** a key entirely | Map to `None` (model default). |
| Model field is `None` on output | **Included** in JSON as `null` (predictable shape for the LLM). |
| List field is empty | Included as `[]` (never `null`). |
| Bool field unknown | **Never** `None` — every bool has a default (usually `False`). |

**Why include nulls in output?** LLMs reason better with stable schemas.
A field that sometimes appears and sometimes doesn't makes the model
less reliable at filling it in on subsequent writes.

**Exception:** the `permissions` block is *only* present on `get_task`
output. It's expensive to compute and not useful in list contexts.

### Computed fields

| Field | Rule |
|---|---|
| `overdue` | `deadline is not None and deadline < now() and status not in {ZAKOŃCZONE, ODRZUCONE, WYCOFANE}` |
| `status_explained` | static map (§8) |
| `permissions.*` | from `status` + current user role + `task_type.requires_evaluation` |
| `truncated` (lists) | `count_returned == limit and there were more rows` |

---

## 7. Encoding & Polish characters

- **All HTTP traffic UTF-8.** httpx defaults are fine; we set
  `Accept: application/json; charset=utf-8` and `Content-Type:
  application/json; charset=utf-8` explicitly.
- **JSON dumping:** `json.dumps(..., ensure_ascii=False)` so Polish
  characters render natively (`"ZAKOŃCZONE"`, not `"ZAKO\u0143CZONE"`).
- **Identifiers (status values, role names) keep their Polish
  characters.** They are matched by exact string; no normalisation.
- **Search filters** (e.g. `subject_contains`) use `.casefold()` for
  case-insensitive matching — correctly handles Polish casing
  (`Ł`/`ł`, `Ż`/`ż`, etc.).
- **Logging:** redact tokens; emit Polish content as-is (not escaped).

---

## 8. Enum reference

### 8.1 Status

| Value (Polish identifier) | `status_explained` (English gloss) | Meaning |
|---|---|---|
| `W_EDYCJI` | `in editing` | Draft, not yet started. Only state in which delete is allowed. |
| `REALIZOWANE` | `in progress` | Active work. |
| `DO_OCENY` | `pending evaluation` | Awaiting manager scoring (task types with `requires_evaluation`). |
| `ZAKOŃCZONE` | `completed` | Closed. |
| `ODRZUCONE` | `rejected` | Rejected with reason. |
| `WYCOFANE` | `withdrawn` | Withdrawn by creator. |

**Input alias map** (LLM may send either form, tools normalise):

| English alias | Polish identifier |
|---|---|
| `in_editing` | `W_EDYCJI` |
| `in_progress` | `REALIZOWANE` |
| `pending_evaluation` | `DO_OCENY` |
| `completed` | `ZAKOŃCZONE` |
| `rejected` | `ODRZUCONE` |
| `withdrawn` | `WYCOFANE` |

Output **always** uses the Polish identifier in `status` + the English
gloss in `status_explained`.

### 8.2 Role

| Value | Meaning |
|---|---|
| `pracownik` | Employee — own tasks only |
| `kierownik` | Manager — team operations + stats |
| `dyrektor` | Director — broader scope |
| `zarzad` | Board — read-only aggregated stats |

A user may have multiple roles; the **highest** role drives tool gating.

### 8.3 `rodzaj_zadania` (internal, not exposed to LLM)

Observed values: `ZWYKLE`, possibly others (TBD on first contact with
live data). Mapped to `Task.kind` internally; not surfaced in tool
output for P0.

---

## 9. Translation function pattern

Every resource has **exactly one** translate function. Pattern:

```python
def task_from_emp(raw: dict, *, ctx: TranslationContext) -> Task:
    """EMP dict → Task domain model."""
    return Task(
        id=raw["id"],
        subject=raw["dotyczy"],
        status=Status(raw["status"]),
        task_type_id=raw["slownik_typ_zadania_id"],
        task_type_name=raw.get("slownik_typ_zadania_nazwa")
                       or ctx.task_type_name(raw["slownik_typ_zadania_id"]),
        # ...
        tags=[t["nazwa"] for t in raw.get("tags", [])],
        ordered_at=parse_emp_datetime(raw["data_zlecenia"]),
        deadline=parse_emp_datetime(raw.get("data_termin")),
        # ...
        overdue=compute_overdue(raw),
    )
```

- `TranslationContext` carries the dictionaries cache + current user
  identity — required for enrichment without re-fetching.
- All `parse_emp_datetime`, `tak_nie_to_bool`, etc. live in
  `domain/coerce.py` and are unit-tested standalone.
- Translation **never** fails silently — unknown enum values raise
  `EmpParseError`, surfaced to the user as `EMP_REJECTED` with details.

---

## 10. What this doc fixes

| Question | Answer |
|---|---|
| How do we type internal data? | pydantic v2 BaseModels (§4) |
| How do we name things in Python? | Python attr column in §3 (English snake_case) |
| What's the tz / date format story? | Naive Warsaw local; ISO 8601 in/out, Laravel format on the wire (§5) |
| Do we preserve nulls in output? | Yes (§6) — predictable shape for the LLM |
| Polish characters? | UTF-8 everywhere; identifiers preserved (§7) |
| Where does enrichment happen? | Translation layer, with cached context (§9) |
| Where does validation happen? | Pydantic at tool entry; enum/coerce at translation; business rules in tool body |

---

## 11. Cascades into later docs

- **Doc 08 (errors)** — `ErrorEnvelope` shape locked here; `EmpParseError`
  and `EMP_REJECTED` codes referenced.
- **Doc 10 (modules)** — implies a `domain/` package with `types.py`,
  `coerce.py`, and `translate.py`.
- **Doc 11 (tests)** — every translate function is unit-tested with
  recorded EMP fixtures; pydantic models give us free schema tests.

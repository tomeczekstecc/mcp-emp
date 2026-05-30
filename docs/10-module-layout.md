# 10 — Module Layout

The Python package structure. Where every concept from docs 05–09
actually lives, what's allowed to depend on what, and how the process
boots.

---

## 1. Top-level layout

```
mcp_emp/                            ← repo root
├── pyproject.toml
├── README.md
├── .env.example                    ← committed (doc 09 §8)
├── .env                            ← gitignored
├── docs/                           ← this folder
├── tests/                          ← see doc 11
└── src/
    └── mcp_emp/                    ← the importable package
        ├── __init__.py             ← version + minimal public exports
        ├── __main__.py             ← `python -m mcp_emp` entry point
        ├── server.py               ← MCP server bootstrap + tool registration
        ├── config.py               ← Settings (doc 09)
        ├── identity.py             ← IdentityContext (doc 09 §5 step 6)
        ├── errors.py               ← error codes + ok()/err() helpers (doc 08)
        ├── logging_setup.py        ← log config + redaction filter (doc 08 §9)
        │
        ├── auth/                   ← Keycloak auth (doc 08 §5)
        │   ├── __init__.py
        │   ├── keycloak.py         ← KC client (login, refresh, well-known)
        │   └── token_holder.py     ← in-memory TokenHolder + asyncio lock
        │
        ├── emp/                    ← EMP HTTP client (doc 08 §3)
        │   ├── __init__.py
        │   ├── client.py           ← httpx wrapper, bearer injection, error mapping
        │   └── endpoints.py        ← typed endpoint URLs (one constant per route)
        │
        ├── domain/                 ← typed domain layer (doc 07)
        │   ├── __init__.py
        │   ├── types.py            ← Task, TaskType, Tag, User, Permissions, enums
        │   ├── coerce.py           ← parse_emp_datetime, tak_nie_to_bool, etc.
        │   └── translate.py        ← task_from_emp, task_type_from_emp, ...
        │
        ├── cache/                  ← in-process caches (doc 06 tools 2–3)
        │   ├── __init__.py
        │   └── ttl_cache.py        ← simple TTL dict with async-safe get-or-load
        │
        ├── confirmations.py        ← TokenStore + payload hashing (doc 08 §7)
        │
        ├── permissions.py          ← compute Permissions block (doc 07 §6, doc 06 tool 5)
        │
        ├── tools/                  ← one module per MCP tool (doc 06)
        │   ├── __init__.py         ← register_p0_tools(server, ctx)
        │   ├── _base.py            ← shared input models, tool decorators
        │   ├── health_check.py
        │   ├── list_task_types.py
        │   ├── list_tags.py
        │   ├── list_my_tasks.py
        │   ├── get_task.py
        │   ├── add_my_task.py
        │   ├── complete_task.py
        │   └── delete_task.py
        │
        └── resources/              ← MCP resources (read-only, LLM-loadable)
            ├── __init__.py
            └── error_codes.py      ← exposes the doc 08 §2 table as a resource
```

**Why `src/`-layout?** Standard modern Python convention; prevents
importing the package by accident from CWD before it's installed; plays
well with `uv` / `pip install -e .`.

---

## 2. Dependency direction (allowed imports)

A module may import only from its own layer or layers **below** it.

```
        tools/*          resources/*         ← layer 5 (LLM-facing)
            │                  │
            ▼                  ▼
     permissions.py     confirmations.py     ← layer 4 (orchestration)
            │                  │
            ▼                  ▼
        emp/client.py    cache/ttl_cache.py  ← layer 3 (I/O + state)
            │
            ▼
   domain/translate.py  ◀── domain/types.py  ← layer 2 (pure data)
            │                  ▲
            ▼                  │
   domain/coerce.py            │
                               │
   auth/* ──▶ emp/client.py    │             ← layer 3 (auth feeds I/O)
            ▲                  │
            │                  │
        config.py ── identity.py             ← layer 1 (bootstrap)
            ▲
            │
        errors.py  logging_setup.py          ← layer 0 (cross-cutting)
```

**Hard rules:**
- `domain/` is **pure** — no I/O, no httpx, no asyncio. Easy to unit-test.
- `tools/` is the **only** layer that returns the `{ok, data|error}`
  envelope. Lower layers raise typed exceptions; `_base.py` translates
  them at the boundary.
- `emp/client.py` is the **only** caller of httpx. Everything else asks
  it for typed results.
- `auth/` is the **only** holder of credentials. Tools never see
  passwords or raw tokens.
- `config.py` is imported by everything but imports nothing project-local
  except `errors.py`.
- Circular imports forbidden; enforced by an import-lint test (doc 11).

---

## 3. Key modules — one-line purposes

| Module | Purpose |
|---|---|
| `config.py` | `Settings` (pydantic-settings), loaded once at startup |
| `identity.py` | `IdentityContext` — current user id, username, roles; immutable after startup |
| `errors.py` | `ErrorCode` enum, `EmpError` exception hierarchy, `ok()` / `err()` helpers |
| `logging_setup.py` | `configure_logging(settings)`, redaction filter for secrets |
| `auth/keycloak.py` | `KeycloakClient` — `login(username, password)`, `refresh(token)`, `discover()` |
| `auth/token_holder.py` | `TokenHolder.ensure_valid()` — refresh-or-relogin with asyncio lock |
| `emp/client.py` | `EmpClient` — `get_json(path, params)`, `post_json(path, body)`, etc.; injects bearer; maps HTTP → `EmpError` |
| `emp/endpoints.py` | URL constants: `REJESTR_LISTA_MOJE`, `REJESTR_USUN(id)`, … |
| `domain/types.py` | Pydantic models from doc 07 §4 |
| `domain/coerce.py` | `parse_emp_datetime`, `tak_nie_to_bool`, `parse_time_hhmm`, alias maps |
| `domain/translate.py` | `task_from_emp(raw, ctx)`, `task_type_from_emp(raw)`, `tag_from_emp(raw)` |
| `cache/ttl_cache.py` | `TtlCache[T]` with `get_or_load(key, loader, ttl)` and `invalidate(key)` |
| `confirmations.py` | `TokenStore.issue(op, resource_id, payload)`, `.validate_and_use(token, op, resource_id, payload)` |
| `permissions.py` | `compute(task, identity, task_type) -> Permissions` |
| `tools/_base.py` | `@mcp_tool` decorator: wraps in envelope, catches `EmpError`, enforces `READ_ONLY` flag for mutating tools |
| `tools/<name>.py` | One module per tool; defines input model + handler function |
| `resources/error_codes.py` | Static MCP resource serving the doc 08 §2 table as a markdown blob |
| `server.py` | `async def run()` — builds Settings, KC, EMP client, IdentityContext, caches, ToolContext; registers tools/resources; starts transport |
| `__main__.py` | `asyncio.run(server.run())` |

---

## 4. The `ToolContext` object

A single immutable dataclass passed to every tool handler. Built once
at startup; never mutated. Avoids global state.

```python
# server.py (sketch)

@dataclass(frozen=True)
class ToolContext:
    settings: Settings
    identity: IdentityContext
    emp: EmpClient
    task_types_cache: TtlCache[list[TaskType]]
    tags_cache:       TtlCache[list[Tag]]
    confirmations:    TokenStore
    now: Callable[[], datetime]    # injectable for tests
```

Every tool handler receives `ctx: ToolContext` plus its typed input
model. Translation functions receive a `TranslationContext` derived
from `ToolContext` (caches + identity only).

---

## 5. Tool module shape (canonical)

Every `tools/<name>.py` follows the same structure. Example:

```python
# tools/delete_task.py

from pydantic import BaseModel
from ..tools._base import mcp_tool, ToolContext
from ..errors import EmpError, ErrorCode
from ..permissions import compute as compute_perms
from ..domain.translate import task_from_emp

class DeleteTaskInput(BaseModel):
    task_id: int
    confirmation_token: str | None = None
    dry_run: bool = False

@mcp_tool(
    name="delete_task",
    description="Permanently delete a task ... (full description from doc 06 tool 8)",
    mutating=True,
    destructive=True,
)
async def delete_task(ctx: ToolContext, inp: DeleteTaskInput) -> dict:
    # 1. pre-flight: fetch + validate state
    raw  = await ctx.emp.get_json(f"/rejestr/{inp.task_id}")
    task = task_from_emp(raw, ctx=ctx.translation_ctx())
    perms = compute_perms(task, ctx.identity, ctx.task_type_for(task))
    if not perms.can_delete:
        raise EmpError(ErrorCode.INVALID_TRANSITION,
                       "Task is not in W_EDYCJI; deletion not allowed.",
                       details={"current_status": task.status.value,
                                "allowed_source_statuses": ["W_EDYCJI"]})

    # 2. preview / token issuance
    if inp.confirmation_token is None or inp.dry_run:
        token = ctx.confirmations.issue("del", inp.task_id, {"task_id": inp.task_id})
        return _preview_response(task, token, dry_run=inp.dry_run)

    # 3. commit
    ctx.confirmations.validate_and_use(inp.confirmation_token, "del",
                                       inp.task_id, {"task_id": inp.task_id})
    await ctx.emp.delete(f"/rejestr/{inp.task_id}")
    return {"deleted": True, "task_id": inp.task_id,
            "previous_status": task.status.value}
```

Convention details:
- Handler is **async**.
- Returns a **plain dict** for the `data` payload; `@mcp_tool` wraps in
  `{ok: true, data: ...}`.
- Raises `EmpError` for failures; `@mcp_tool` converts to `{ok: false,
  error: ...}`.
- Mutating handler with `mutating=True`: decorator checks `settings.read_only`
  before the handler body runs (doc 08 §8).
- Input model is module-local; not re-exported.

---

## 6. Async vs sync

| Layer | Async? |
|---|---|
| `tools/*` | **async** (MCP handlers are async) |
| `emp/client.py` | **async** (httpx AsyncClient) |
| `auth/*` | **async** (KC token endpoints) |
| `confirmations.py` | **sync** (in-memory; nanoseconds) |
| `cache/ttl_cache.py` | **async** `get_or_load` (loader is async) |
| `domain/*` | **sync** (pure CPU) |
| `config.py`, `errors.py`, `permissions.py`, `identity.py` | **sync** |

Single event loop; no threading. No sync wrappers around async — if you
need async, your caller must be async.

---

## 7. Entry point

```python
# __main__.py
import asyncio
from .server import run

if __name__ == "__main__":
    asyncio.run(run())
```

```python
# server.py (skeleton)
async def run() -> None:
    settings = Settings()                      # raises if missing required
    configure_logging(settings)
    kc       = KeycloakClient(settings)
    holder   = await TokenHolder.bootstrap(kc, settings)   # full login at startup
    identity = await IdentityContext.from_token(holder.current)
    emp      = EmpClient(settings, holder)
    await _startup_health_check(emp)           # WARN on fail, do not exit
    ctx = build_tool_context(settings, identity, emp)
    server = build_mcp_server()
    register_p0_tools(server, ctx)
    register_resources(server, ctx)
    await start_transport(server, settings)    # stdio or sse
```

Replacement for the current `main.py` stub. The stub stays only as a
historical artefact and is removed at build time.

---

## 8. `__init__.py` exports — public vs internal

```python
# src/mcp_emp/__init__.py

__version__ = "0.1.0"

# Public API: only the things a host (or test) might reasonably import.
from .server import run                # for embedding
from .config import Settings           # for tests / programmatic config

__all__ = ["run", "Settings", "__version__"]
```

Everything else is **internal**. Submodules' `__init__.py` files are
empty (or just re-export inside the package).

---

## 9. External dependencies

Locked at this layer; no surprises later.

| Package | Used by | Why |
|---|---|---|
| `mcp >= 1.27` | `server.py`, `tools/_base.py` | The protocol |
| `httpx >= 0.28` | `emp/client.py`, `auth/keycloak.py` | Async HTTP |
| `pydantic >= 2.x` | `domain/types.py`, `tools/*` input models | Validation |
| `pydantic-settings` | `config.py` | Env parsing |
| `starlette` + `sse-starlette` + `uvicorn` | `server.py` (when transport=sse) | SSE transport |
| `python-dateutil` *(optional)* | `domain/coerce.py` | Lenient date parsing of LLM input |

No: orm, queue client, redis, db driver — we go through the EMP REST
API for everything.

---

## 10. What this doc fixes

| Question | Answer |
|---|---|
| Where does each concept live? | §3 |
| Who's allowed to import what? | §2 |
| How are tools structured? | §5 |
| Async or sync? | §6 |
| How does the process boot? | §7 |
| What's public API? | §8 |
| What third-party packages? | §9 |

---

## 11. Cascades

- **Doc 11 (tests):** mirrors §1 — one test module per source module,
  with import-direction lint enforcing §2.
- **Doc 12 (runtime):** uses `start_transport` from §7; finalises SSE
  vs stdio dispatch.
- **Doc 13 (roadmap):** P0 file list is everything in §1 except
  `tools/` past index 8.

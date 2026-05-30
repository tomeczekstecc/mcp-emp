# PRD — mcp-emp: MCP Server for Elektroniczna Miara Pracy (EMP)

_Generated from planning docs 01–14 and grilling session (ADRs 0001–0004)._
_Status: ready for implementation — P0 scope._

---

## Problem Statement

As a `pracownik` (employee) using an LLM assistant (Claude Desktop, pi, Cursor), I have no way to read, create, or update my work records in EMP without switching to a browser. The EMP backend (a Laravel/CQRS/PostgreSQL app) exposes a REST API, but it is inaccessible to LLM agents — there is no MCP server wrapping it. Every interaction (logging time, completing a task, reviewing my cycle, bulk-deleting drafts) requires a manual context switch that breaks the flow of AI-assisted work.

---

## Solution

`mcp-emp` is a Python MCP server that bridges LLM clients to the EMP backend. It authenticates as a single user via Keycloak (Resource Owner Password grant), exposes a small set of well-typed MCP tools covering task CRUD and lifecycle, and runs as a local process that any MCP-compatible host (Claude Desktop, pi, Cursor, Cline, etc.) can spawn over stdio.

The server is intentionally single-user and single-process. It wraps EMP's endpoints with domain-typed models, validates mutations against in-process cached reference data before calling EMP, and requires explicit confirmation for destructive operations.

---

## User Stories

### Auth & identity

1. As a pracownik, I want the server to authenticate me via Keycloak at startup using environment variables, so that I never type credentials into the LLM chat.
2. As a pracownik, I want the server to refresh my Keycloak token transparently mid-session, so that long-running conversations don't suddenly fail with auth errors.
3. As a pracownik, I want a clear error message at startup when my credentials are wrong or the KC realm is misconfigured, so that I can fix the problem without reading logs.
4. As a pracownik, I want the server to report my identity (username, display name, roles) via the `health_check` tool, so that I can confirm which account is active.

### Health & observability

5. As a pracownik, I want to call `health_check` to verify EMP and Keycloak are reachable, so that I know whether tool failures are my data or infrastructure.
6. As a sysadmin, I want a `/healthz` HTTP endpoint (when HTTP transport is on) to probe the process, so that I can integrate it with a service monitor.

### Reference data (słowniki)

7. As a pracownik, I want to list all active task types with a search filter, so that I can pick the right `task_type_id` when logging work.
8. As a pracownik, I want to list all tags with a search filter, so that I can tag new tasks correctly.
9. As a pracownik, I want słowniki results to be cached in-process with a TTL, so that repeated calls don't slow down a multi-step conversation.
10. As a pracownik, I want `list_task_types` to flag which types require a time entry and which require a quantity, so that the LLM prompts me for the right fields.

### Reading tasks

11. As a pracownik, I want to list my active tasks (scope: `mine_active`) filtered by status, date range, or SOD number, so that I can find a specific task quickly.
12. As a pracownik, I want to list all my tasks including historical ones (scope: `mine_all`), so that I can audit past work.
13. As a pracownik, I want to retrieve the full detail of a single task by ID, so that the LLM has all the context it needs to complete or edit it.
14. As a pracownik, I want `get_task` to return a `permissions` block indicating what operations are currently allowed, so that the LLM doesn't attempt transitions EMP will reject.
15. As a pracownik, I want status values returned with an English gloss (`status_explained`), so that I understand the Polish identifier without a lookup.

### Creating tasks

16. As a pracownik, I want to create a new task (`add_my_task`) with all required fields validated before the EMP call, so that I get a precise error message instead of an EMP rejection.
17. As a pracownik, I want `add_my_task` to support a `dry_run` mode that validates and previews the task without creating it, so that I can confirm the details before committing.
18. As a pracownik, I want `add_my_task` to return the full created task immediately, so that I don't need a separate `get_task` call.
19. As a pracownik, I want pre-flight validation to check my `task_type_id` and `tag_ids` against cached słowniki, so that I get an immediate error for unknown values rather than waiting for EMP.

### Completing tasks

20. As a pracownik, I want to mark a task as done (`complete_task`) with the time I spent, so that I can close out work without leaving the LLM context.
21. As a pracownik, I want `complete_task` to tell me whether the task will move to `ZAKOŃCZONE` or `DO_OCENY`, so that I know whether a manager review is pending.
22. As a pracownik, I want `complete_task` to refuse when the task is not in `REALIZOWANE` or `DO_OCENY`, so that I don't waste a round trip on an invalid transition.

### Deleting tasks

23. As a pracownik, I want to delete a draft task (`W_EDYCJI`) via a two-step confirmation flow, so that the LLM cannot silently delete tasks I care about.
24. As a pracownik, I want the first `delete_task` call to show a preview of the task to be deleted, so that I can verify the right task is targeted.
25. As a pracownik, I want the confirmation token to expire after 5 minutes, so that an abandoned conversation doesn't leave a live delete token.
26. As a pracownik, I want the confirmation token to be bound to the task payload, so that the LLM cannot bait-and-switch (preview task A, delete task B).
27. As a pracownik, I want `delete_task` to refuse with a clear error on non-draft tasks, so that I never accidentally try to delete a task already in progress.

### Safety & control

28. As a sysadmin, I want to set `MCP_EMP_READ_ONLY=true` to prevent any writes, so that I can let an agent read EMP data in a demo or audit without risk.
29. As a sysadmin, I want `READ_ONLY` mode to block `dry_run` calls too, so that there is a single simple rule about what the agent can do.
30. As a pracownik, I want all error responses to carry a stable machine-readable `code` (e.g. `TASK_NOT_FOUND`, `INVALID_TRANSITION`), so that the LLM can branch on them reliably.

### Transport & deployment

31. As a pracownik, I want to run `mcp-emp` via stdio so that any desktop MCP host (Claude Desktop, pi, Cursor) can spawn it without extra setup.
32. As a developer, I want to run `mcp-emp` in HTTP mode (`MCP_EMP_TRANSPORT=http`) so that web-based MCP hosts (ChatGPT MCP, n8n) can reach it.
33. As a developer, I want the HTTP server to expose both Streamable HTTP (`/mcp`) and legacy SSE (`/sse` + `/messages`) endpoints, so that any HTTP-capable MCP client works regardless of which sub-protocol it uses.
34. As a developer, I want to install `mcp-emp` via `uv tool install` or `pipx`, so that it lands on my PATH with a single command.
35. As a developer, I want `MCP_EMP_LOG_LEVEL=DEBUG` to produce detailed logs without ever leaking credentials or tokens, so that I can diagnose issues safely.

---

## Implementation Decisions

### Architecture

- **Domain-first layout** under `src/mcp_emp/`: `domains/rejestr/`, `domains/slowniki/`, `core/`. A future `domains/stat/` will hold statistics (P1). Tools are never in a flat `tools/` folder.
- Each domain package has: `contract.py` (Payload + Model + Input types), `mapper.py` (Payload → Model), `client.py` (async `fetch_*` / `create_*` functions), `tools.py` (`register(server)` function), and optionally `errors.py`.
- Cross-cutting infrastructure (`httpx.AsyncClient`, Keycloak auth, identity, config, logging, error codes, confirmation tokens, read-only/dry-run gates) lives entirely in `core/`.
- **Allowed cross-domain import**: `rejestr → slowniki` (pre-flight reads the słowniki cache). Never the reverse. Never `core ← domains`.

### Tool result shape (ADR-0001)

- Tools return domain model instances directly on success (`-> Task`, `-> list[TaskType]`).
- Failures raise typed `EmpError` subclasses carrying a stable `code` string (closed enum of 17 codes) and a `details` dict.
- Decorators convert `EmpError` to `McpError` with `data={"code": ..., "details": ...}` so the LLM sees `error.data.code`.
- Dry-run and confirmation metadata are expressed as **dedicated typed wrappers** on mutating tools only (e.g. `TaskCreateResult { task, dry_run, validated }`), not on every tool.

### Exception serialisation (ADR-0004)

- Every `@server.tool()` function is wrapped by exactly one of `@mutating` (writes) or `@readable` (reads) from `core/modes.py`.
- Both decorators catch `EmpError` and convert it to `McpError` via a shared `_to_mcp_error()` helper.
- `@mutating` additionally raises `ReadOnlyMode` before the body runs when `MCP_EMP_READ_ONLY=true`.
- Lint rule: every tool function has exactly one of these decorators directly below `@server.tool()`.

### Mutating-tool conventions (ADR-0003)

- `dry_run: bool = False` is always the last keyword argument on mutating tools.
- `READ_ONLY` blocks `dry_run=true` as well — one simple rule.
- `confirmation_token: str | None = None` is present on destructive tools; absence triggers the preview/token flow.

### Shared state

- `httpx.AsyncClient`, `KeycloakAuth`, `SlownikCache`, `ConfirmationStore`, and `Settings` are module-level singletons initialised in `server.py`'s `lifespan()` and accessed via `get_client()`, `get_auth()`, etc.
- No FastMCP `Context` injection for state (adds parameters that must be hidden from MCP schema). `Context` is reserved for future multi-session needs.

### Domain split (ADR-0002)

- **`rejestr/`**: task CRUD, lifecycle (`W_EDYCJI → REALIZOWANE → DO_OCENY/ZAKOŃCZONE`), permission matrix, status alias map.
- **`slowniki/`**: task types, tags; in-process TTL cache (10m for task types, 5m for tags); no writes from mcp-emp.
- **`stat/`** (P1): aggregate reports; own client, own models, role-gated tool registration.
- `health_check` is registered directly from `server.py` — it is not a domain.

### Confirmation token contract

- Format: `<op>_<resource_id>_<hex8>` (e.g. `del_1234_a3f9c2b1`).
- TTL: 5 minutes, fixed.
- Single-use; `(operation, resource_id)` scoped; sha256[:16] payload-hash bound to prevent bait-and-switch.
- `ConfirmationStore` in `core/confirmations.py` is the in-memory registry, protected by an asyncio lock.

### Auth

- Keycloak Resource Owner Password grant. Username + password from env vars.
- `KeycloakAuth` in `core/auth.py` holds the current token and refreshes it under an asyncio lock (single refresh for N concurrent calls).
- Token stored in memory only; lost on restart (re-login is transparent and fast).
- Startup fails with exit code 77 (`AUTH_MISCONFIGURED`) if initial login fails.

### Transport

- `MCP_EMP_TRANSPORT=stdio` (default) for desktop hosts.
- `MCP_EMP_TRANSPORT=http` for web/hosted hosts; binds `127.0.0.1:8765`; exposes `/mcp` (Streamable HTTP) + `/sse` + `/messages` (legacy SSE) + `/healthz`.
- No stdio + HTTP in a single process.

---

## Testing Decisions

- **Good tests** assert on external behaviour: the tool's return value (a model instance) or the exception raised (typed, with `code`). Never assert on internal state (cache size, httpx call count beyond what respx verifies, singleton identity).
- **Test layout** mirrors `src/`: `tests/rejestr/`, `tests/slowniki/`, `tests/core/`, `tests/lint/`.
- **Fixtures**: EMP JSON responses captured from the live dev backend and committed under `tests/<domain>/fixtures/emp/`. Translate/mapper functions are tested against these captures only — never hand-written JSON.
- **What to mock**: httpx transport via `respx`; time via `time-machine`; `secrets.token_hex` for deterministic confirmation tokens. Never mock pydantic models, mapper functions, or pure domain logic.
- **Per-tool integration test scenarios** (applied to every tool): (1) happy path, (2) validation error, (3) EMP error response, (4) auth failure, (5) `READ_ONLY` mode (mutating tools only), (6) `dry_run` (mutating tools only), (7) confirmation flow (destructive tools only).
- **Lint tests** (in `tests/lint/`): import direction, no secrets in logs, every tool has `@readable` or `@mutating`, tool description compliance, schema snapshot stability.
- **Coverage targets**: ≥95% domain + mapper code; ≥80% tools + core auth/IO. Gating in CI; not a target to game.
- **e2e suite** (`tests/e2e/`): opt-in via `MCP_EMP_E2E=1`; 5 smoke tests against real dev EMP. Not in the fast CI gate.

---

## Out of Scope

- Multi-user / multi-tenant operation. One process = one Keycloak identity.
- Manager tools (`list_team_tasks`, `assign_task`, etc.) — P1 at earliest.
- Statistics and reporting tools — P1.
- Bulk create / bulk delete — P3.
- Task templates and recurring tasks — P3.
- HTTP shared-secret authentication — P2.
- Persistent token storage (tokens are in-memory only).
- Idempotency keys on writes.
- Background token refresh / keep-alive.
- Structured logging / metrics / tracing.
- Public PyPI release (local install only for P0).

---

## Further Notes

- Polish-language identifiers (`ZAKOŃCZONE`, `W_EDYCJI`, `pracownik`, etc.) are **data values**, not translated — the LLM receives them as-is alongside English glosses (`status_explained`). This is intentional: the server must not lie about EMP's actual identifiers.
- The planning docs (`docs/01–14`) and ADRs (`docs/adr/0001–0004`) are the authoritative source for every decision above. When in doubt, read the doc; don't infer from code.
- The grilling session surfaced **six conflicts between the original planning docs (06, 07, 08, 10, 11, 13) and the pre-existing project conventions** (`CONTEXT.md`, `ddd-patterns.md`). Those docs need rewriting before or during M0–M2. The conflicts and their resolutions are recorded in ADRs 0001–0004.
- The first demoable milestone is **M7** (~6–7 working days): UC-1 (create task), UC-2 (find + complete), UC-3 (confirm + delete) all working against real EMP via Claude Desktop or pi.

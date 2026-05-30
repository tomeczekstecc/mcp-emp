# CONTEXT

Domain glossary for the `mcp-emp` Python MCP server.

---

## MCP

Model Context Protocol. The transport + schema that lets LLM clients (Claude Desktop, IDE agents, pi) discover and call **tools**, read **resources**, and use **prompts** exposed by this server.

## MCP server

The running Python process started from `main.py` (eventually `mcp_emp/server.py`). It registers tools/resources/prompts and speaks the MCP protocol over a transport (stdio by default).

## Tool

A single callable function exposed to MCP clients. Named `verb_noun` (e.g. `get_employee`). Inputs are typed parameters; output is a JSON-serializable Pydantic model or primitive structure. Tool docstrings are the LLM-facing spec.

## Resource

A read-only addressable piece of context (e.g. a document, a record) the LLM can pull in by URI. Not used yet in this project; add under a domain when needed.

## Prompt

A reusable, parameterised prompt template the client can invoke. Not used yet; reserve `mcp_emp/domains/<domain>/prompts.py` for these when they arrive.

## Upstream API

Any external HTTP service this server wraps via `httpx`. Each upstream gets its own **domain** package.

## EMP

*Elektroniczna Miara Pracy* — the Laravel/PostgreSQL backend this server wraps. CQRS-shaped: `app/Domain/Rejestr/{Commands,Queries}`. Auth via Keycloak (realm `eMP`, client `eMP-REST-API`) using the Resource Owner Password grant. Polish-language data values (status identifiers like `ZAKOŃCZONE`, role names like `kierownik`) are preserved as-is in payloads and models.

## Rejestr

A single unit of work recorded in EMP (a "task"). Has a lifecycle (`W_EDYCJI` → `REALIZOWANE` → optional `DO_OCENY` → `ZAKOŃCZONE`, plus `ODRZUCONE` / `WYCOFANE`) and a `rodzaj_zadania` (task kind). The MCP-facing model name is `Task`. The `rejestr/` domain package owns task CRUD, lifecycle, permission matrix, and history.

## Słowniki

Reference data ("dictionaries") in EMP: task types, tags, teams, users. Read-mostly; cached in-process with a TTL. Owned by the `slowniki/` domain package. The status alias map is *not* a słownik — it is task-lifecycle vocabulary and lives in `rejestr/`.

## Stat

Aggregate reporting over rejestr (cycle stats, daily reports, team comparisons). Read-only, often role-gated. Its own domain (`stat/`) rather than a sub-module of rejestr because the consumer mental model and shape differ. P1+ scope.

## Role

A permission level carried in the Keycloak token: `pracownik` (employee), `kierownik` (manager), `dyrektor` (director), `zarzad` (board). Some tools are only registered when the user has the required role.

## Tool error

A failure outcome of a tool call. Signalled as a typed Python exception carrying a stable `code` (drawn from a closed enum) and a `details` mapping. The MCP SDK serialises it into the JSON-RPC `error.data` slot. See ADR-0001.

## Confirmation token

A short-lived, single-use, payload-bound string a destructive tool requires on its second call. Issued by the first call (which previews the change) and consumed by the second call (which executes it). Scoped to `(operation, resource_id)` and bound to a sha256 prefix of the payload to defeat bait-and-switch.

## Pre-flight

Validation performed before any EMP write: the tool checks the cached słowniki, the user's role, and the target task's current status, and raises a `Tool error` with a precise `code` if the EMP call would be rejected. Pre-flight is *advisory*: EMP remains the source of truth, and an `EMP_REJECTED` is still possible.

## Dry-run

A mutating-tool mode (`dry_run=true`) that runs pre-flight and returns the would-be result wrapped in a typed wrapper (e.g. `TaskCreateResult`) without calling EMP. Disabled when `READ_ONLY` is on.

## Read-only mode

A boot-time toggle (`MCP_EMP_READ_ONLY=true`) that refuses every mutating tool call — including `dry_run=true` — with a `READ_ONLY` tool error. Reads are unaffected.

## Domain

A bounded context corresponding to one upstream capability (e.g. `employees`, `timesheets`). Lives under `mcp_emp/domains/<domain>/` with the standard layout: `contract.py`, `mapper.py`, `client.py`, `tools.py`.

## Payload vs Model

- **Payload** (`*Payload`) — the raw upstream API shape. Snake_case, possibly inconsistent.
- **Model** — the clean, MCP-facing shape returned by tools. Properly typed, normalized.

The boundary between them is `mapper.py`.

## Client (domain client)

The async functions in `mcp_emp/domains/<domain>/client.py` that call the upstream API via the shared `httpx.AsyncClient` and return mapped models. Not to be confused with the **MCP client** (the LLM/agent calling this server).

## Core

Cross-cutting infrastructure under `mcp_emp/core/` — HTTP client lifespan, configuration, logging, base exceptions. Never domain-specific.

## Lifespan

The MCP server startup/shutdown lifecycle where shared resources (the `httpx.AsyncClient`, logging, config) are initialised and torn down.

---

For deeper conventions, see `context/coding-standards.md`, `context/ddd-patterns.md`, and `context/project-overview.md`.

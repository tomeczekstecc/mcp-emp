# Changelog

All notable changes to `mcp-emp` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-05-30

First public release.  Covers the P0 scope: full task CRUD, reference data,
statistics, user profile, and MCP API-key auth for the HTTP transport.

### Added

#### Tools (13)

| Tool | Description |
|---|---|
| `health_check` | EMP reachability + KC auth status |
| `list_task_types` | EMP task-type dictionary (cached 10 min) |
| `list_tags` | EMP tag dictionary (cached 5 min) |
| `list_my_tasks` | My tasks with scope/status/search/SOD filters |
| `get_task` | Single task detail + permissions block |
| `add_my_task` | Create a task (dry_run, pre-flight, tag validation) |
| `complete_task` | Complete a task (dry_run, transition prediction) |
| `delete_task` | Delete a draft task (two-step confirmation token) |
| `get_my_profile` | Current user's EMP profile |
| `get_my_permissions` | Current user's EMP permission list |
| `list_users` | All EMP users (role-gated) |
| `get_cycle_stats` | Points per billing cycle |
| `get_daily_stats` | Today's completed tasks |

#### Core features

- **Keycloak ROPC auth** — Resource Owner Password grant with asyncio-locked
  concurrent refresh (KC hit exactly once for N parallel calls).
- **Confirmation tokens** — 5-minute TTL, single-use, scoped to
  `(operation, resource_id)`, SHA-256 payload-hash bound (prevents
  bait-and-switch attacks).
- **Pre-flight validation** — task type and tag IDs validated against cached
  słowniki before every EMP write.
- **Structured error codes** — 11 error codes with machine-readable `code`
  and `details`; LLMs can branch reliably.
- **Read-only mode** — `MCP_EMP_READ_ONLY=true` blocks all mutations.
- **Dry-run on all mutating tools** — preview without calling EMP.
- **Credential redaction** — passwords and tokens automatically stripped from
  all log output, including `DEBUG` level.

#### Transports

- **stdio** (default) — works with Claude Desktop, pi, Cursor, Cline,
  Continue, Ollama-based hosts.
- **Streamable HTTP** + **legacy SSE** — works with ChatGPT MCP, Claude.ai
  web, n8n, and custom HTTP agents
  (`MCP_EMP_TRANSPORT=http`).

#### MCP API-key auth (HTTP transport)

- SQLite-backed user/key store (`~/.mcp_emp/auth.db`).
- Key format: `emp_<username>_<32hex>` — SHA-256 hash stored, plaintext
  never persisted.
- Superuser model: only superusers can add users.
- CLI: `mcp-emp auth init | add-user | delete-user | revoke-key | list-users`.
- `/healthz` endpoint always open; auth required on all MCP paths.

#### Documentation

- `README.md` — overview, quick start, feature table.
- `docs/guides/quick-start.md` — install → configure → Inspector → hosts.
- `docs/guides/configuration.md` — all 15 env vars with defaults.
- `docs/guides/tools-reference.md` — all 13 tools with parameters, shapes,
  error codes, permissions matrix.
- `docs/guides/auth-management.md` — full auth guide: setup, CLI reference,
  client recipes, security notes.
- `docs/guides/troubleshooting.md` — 9 failure scenarios with root-cause
  and fix.

#### Architecture

- Domain-first layout: `domains/{rejestr,slowniki,stat,uzytkownik}/`,
  `core/` for cross-cutting infrastructure.
- pydantic v2 models throughout; `SecretStr` for credentials.
- `@readable` / `@mutating` decorators convert `EmpError → McpError` with
  structured `error.data.code` (ADR-0001, ADR-0004).
- Module-level singletons (`get_client()`, `get_auth()`, etc.) initialised
  in FastMCP `lifespan()`.
- Import-direction rule enforced by lint test: `core ← domains` never;
  `slowniki → rejestr` never.

#### Testing

- 90 tests across unit, integration, and lint tiers.
- Mapper tests run against **live-captured EMP fixtures**
  (not hand-written JSON).
- All 7 confirmation-token scenarios covered.
- Concurrent KC-refresh test asserts KC is hit exactly once for 8 parallel
  calls.
- Import-direction lint + schema snapshot lint.

### Known limitations

- Single-user, single-process only (Q2 decision).
- No idempotency keys on writes — duplicate creates possible on client retry
  (accepted risk A1).
- `start_task`, `edit_task`, `reject_task`, `withdraw_task` not yet exposed
  (P1 roadmap).
- Stats endpoints for `kierownik`/`dyrektor` scope not yet exposed (P1).
- HTTP shared-secret auth is now full API-key auth (supersedes doc 12 §2
  "deferred to P2").

---

## [Unreleased]

Nothing yet.

[0.1.0]: https://github.com/tomeczekstecc/mcp-emp/releases/tag/v0.1.0

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

---

## [1.1.0] — 2026-05-30

### Added

#### EMP task automation skills (3 new pi/Claude Code skills)

| Skill | Trigger | What it does |
|---|---|---|
| `emp-log-task` | "dodaj zadanie do EMP", "zaloguj pracę" | Interactive: pick type, tag by repo, dry-run, create + complete + backdate |
| `emp-complete-task` | "zakończ zadanie", "complete EMP task" | Find open task by ID/description, check permissions, complete it |
| `emp-commit-and-log` | "commit i zaloguj", "push and log" | Git commit + push AND create matching EMP task in one flow; auto-maps commit type → EMP type, detects repo → tag |

#### Direct DB access control

-  config flag (default )
- When :  is **not registered** — absent from tools/list
- When :  available with full DB access
-  raises clear error when disabled

#### Host integration documentation

New guide:  — copy-paste configs for:
- Claude Desktop (Windows/macOS)
- Claude Code
- Cursor
- pi (auto-import from Cursor + project-local)
- OpenAI Codex CLI (TOML format)
- Cline / Continue (VS Code)
- HTTP hosts: n8n, ChatGPT MCP, Claude.ai
- MCP Inspector (testing)
- macOS/Linux path equivalents
- Troubleshooting quick-reference

### Changed

- All host configs updated with 
-  links to new host-integrations guide
- README updated with host-integrations reference

---

## [1.0.0] — 2026-05-30 (P3 — Bulk, Templates, Automation)

### Added

#### Bulk operations (2 tools)

| Tool | Description |
|---|---|
| `bulk_create_tasks` | Create multiple tasks at once. Step 1: validates + preview + token. Step 2: creates all. |
| `bulk_delete_tasks` | Delete multiple W_EDYCJI tasks at once. Same two-step confirmation pattern. |

Both use confirmation tokens (5-min TTL, payload-hash bound) identical to `delete_task`.

#### Task templates (3 new capabilities)

**CLI:** `mcp-emp template add|list|show|delete`
- SQLite store at `~/.mcp_emp/templates.db` (configurable via `MCP_EMP_TEMPLATES_DB_PATH`)
- Supports `{today}`, `{date}`, `{cycle}` variable substitution in subject/notes
- `deadline_offset_days` — auto-set deadline N days from today

**MCP tools:**
| Tool | Description |
|---|---|
| `list_templates` | List saved templates (with optional search filter). |
| `apply_template` | Create a task from a template; subject/deadline overrides supported; dry_run. |

#### Automation analysis (2 tools)

| Tool | Description |
|---|---|
| `detect_recurring_tasks` | Find task types appearing ≥ N times; suggests representative subjects. Identifies candidates for templates. |
| `suggest_task_completions` | Rank REALIZOWANE tasks by completion urgency: overdue > near-deadline > high-points > long-running. |

### Total: 29 tools

### CLI additions

| Command | Description |
|---|---|
| `mcp-emp template init` | Initialise template DB (auto-created on first use) |
| `mcp-emp template add <name> --task-type-id <id> ...` | Create a template |
| `mcp-emp template list [--search <q>]` | List templates |
| `mcp-emp template show <name>` | Show full template JSON |
| `mcp-emp template delete <name>` | Remove a template |

### SemVer contract locked

From 1.0.0, breaking changes require a MAJOR bump:
- Tool names
- Tool input parameter names and types
- Error code strings
- Envelope shape (error.data.code, error.data.details)

---

## [0.3.0] — 2026-05-30 (P2 — Smart Assistance)

### Added

#### New tools (4) — 

| Tool | Description |
|---|---|
|  | Full snapshot: in-progress, today's completions, upcoming deadlines, overdue tasks, waiting queue. Returns a human-readable  paragraph — ideal for standup notes. |
|  | Scan all tasks for overdue (deadline passed), stalled (REALIZOWANE > N days), and awaiting (OCZEKUJĄCE). Returns a  sorted by severity. |
|  | Suggest tag IDs for a new task based on keyword similarity to past task subjects. Returns  list with  and human-readable reason. |
|  | Distribution of work across task types over a configurable time window (default 30 days): count, total points, avg points, completed/in-progress breakdown. |

All four tools are **pure local computation** — no new EMP HTTP endpoints. They aggregate and analyse data from the existing task, stats, and dictionary endpoints.

### Total: 23 tools

---

## [0.2.0] — 2026-05-30

### Added

#### New tools (5)

| Tool | Description |
|---|---|
| `edit_task` | Update subject, deadline, notes, url, SOD, tags on any non-terminal task. Dry-run supported. |
| `start_task` | Transition planned (`PRZYDZIELONE`) tasks to in-progress (`REALIZOWANE`). |
| `reject_task` | Manager: reject `REALIZOWANE` → `OCZEKUJĄCE` with optional reason. Dry-run supported. |
| `withdraw_task` | Withdraw `OCZEKUJĄCE` → `W_EDYCJI` to re-edit and resubmit. Dry-run supported. |
| `list_team_tasks` | Kierownik view: list team tasks with scope/status/search filters. |
| `get_team_cycle_stats` | Richer cycle stats with per-employee breakdown (kierownik scope). |

#### Status enum

Added two previously undocumented EMP statuses:
- `PRZYDZIELONE` — planned task, assigned but not yet started.
- `OCZEKUJĄCE` — waiting queue after manager rejection.

All 8 statuses now covered: `W_EDYCJI` · `PRZYDZIELONE` · `REALIZOWANE` · `OCZEKUJĄCE` · `DO_OCENY` · `ZAKOŃCZONE` · `ODRZUCONE` · `WYCOFANE`.

New English aliases: `planned`, `waiting`.

#### Permissions matrix

- `can_edit` corrected: `true` for all non-terminal statuses (was: `W_EDYCJI` only).
- `can_start` corrected: `true` only for `PRZYDZIELONE` (was: `W_EDYCJI`).

### Total: 19 tools

---

[0.1.0]: https://github.com/tomeczekstecc/mcp-emp/releases/tag/v0.1.0

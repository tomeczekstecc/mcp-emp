# Domain split: rejestr, słowniki, stat

The MCP-facing tool surface is divided into three domain packages under `src/mcp_emp/domains/`:

- **`rejestr/`** — task CRUD, lifecycle, status, permission matrix, history. Owns the `Task` model.
- **`słowniki/`** (English-named package `slowniki/`) — read-mostly reference data: task types, tags, teams, users. Owns the `TaskType` and `Tag` models. In-process TTL cache lives here.
- **`stat/`** — statistics and reports (P1+). Read-only, role-gated. Owns aggregate models.

Cross-cutting infrastructure (HTTP client, Keycloak auth, identity, config, logging, errors, confirmation tokens, read-only / dry-run gates) lives under `src/mcp_emp/core/`.

The `health_check` MCP tool is registered directly from `server.py`; it is not a domain.

## Why three, not two

- Folding `stat/` into `rejestr/` would mix CRUD entities with aggregate reporting and bloat what is already the largest domain. The consumer mental model differs ("show me numbers" vs "manage tasks") and stat tools are often role-gated, while rejestr tools mostly aren't.
- Splitting `słowniki/` per table (one package for tags, one for task types, …) was rejected: every słownik follows the same shape (cached list + search, no writes from mcp-emp), and one package keeps the pattern in one place.

## Consequences

- Cross-domain import is allowed only `rejestr → słowniki` (pre-flight reads cached słowniki). Never the reverse, and never `core ← domains`.
- Pre-flight permission logic stays in `rejestr/permissions.py` (rejestr-shaped, not reusable).
- Status alias map stays in `rejestr/status.py` (it is task-lifecycle vocabulary, not external reference data).
- Adding a future upstream beyond EMP would mean a parallel `domains/<new-context>/` tree, not a fork of `rejestr/`.

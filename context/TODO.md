# TODO

Project-level follow-ups captured by agents.

## Open

- [ ] Promote `main.py` into a proper `mcp_emp/` package with `server.py` + `core/` + `domains/` layout.
  - Priority: high
  - Date: 2026-05-30
  - Branch: `master`
  - Domain: scaffolding

- [ ] Add `mcp_emp/core/http.py` with a lifespan-managed shared `httpx.AsyncClient`.
  - Priority: high
  - Date: 2026-05-30
  - Branch: `master`
  - Domain: core

- [ ] Add `mcp_emp/core/config.py` (Pydantic `BaseSettings`) and wire it into startup.
  - Priority: high
  - Date: 2026-05-30
  - Branch: `master`
  - Domain: core

- [ ] Set up `ruff` + `pytest` + `pytest-asyncio` and add a minimal CI workflow.
  - Priority: medium
  - Date: 2026-05-30
  - Branch: `master`
  - Domain: tooling

- [ ] Define the first real domain (e.g. `employees`) following `context/ddd-patterns.md`.
  - Priority: medium
  - Date: 2026-05-30
  - Branch: `master`
  - Domain: employees

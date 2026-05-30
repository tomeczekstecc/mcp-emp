<!-- SPECKIT START -->
For additional context about product goals, technologies, project structure,
workflow expectations, and project-specific conventions, read the local
`context/` folder in this repository.

Use these files selectively:
- `project-overview.md` for product goals, target use cases, and MCP server direction
- `project-spec.md` for current scope, MCP tool expectations, and non-goals
- `coding-standards.md` for baseline Python, typing, async, and `httpx` rules
- `ddd-patterns.md` for domain-driven package organization (`mcp_emp/domains/<domain>/`)
- `performance.md` for async I/O hygiene, startup time, and payload-size guidance
- `ai-interaction.md` for collaboration, verification, and commit expectations
- `TODO.md` for open project-level follow-ups

Project-specific adjustments for this repository:
- This is a **Python MCP (Model Context Protocol) server**, not a web app. Defaults: `mcp` + `httpx`, async-first, Python `>=3.12`, packaged with `uv`.
- Real repo layout today: `main.py` at the root, `pyproject.toml`, `uv.lock`, `docs/`, `context/`. The package will grow into `mcp_emp/` with `core/` and `domains/<domain>/` subpackages — see `context/ddd-patterns.md`.
- Use `uv` for everything: `uv sync`, `uv run python main.py`, `uv add <pkg>`, `uv run ruff check`, `uv run pytest`.
- Default to **async** I/O. Reuse a single `httpx.AsyncClient` across calls; never put blocking calls (`time.sleep`, `requests`) inside an async tool handler.
- Follow domain-driven placement: a new upstream API becomes a new package under `mcp_emp/domains/<domain>/` with `contract.py`, `mapper.py`, `client.py`, `tools.py`. Cross-cutting infrastructure (HTTP client lifespan, config, logging) lives under `mcp_emp/core/`.
- Tools must return **mapped models**, not raw upstream payloads. Keep tool docstrings tight — they are the LLM-facing spec.
- Validate everything at boundaries with Pydantic. Avoid `Any` and untyped `dict[str, Any]` across module boundaries.
- Preserve existing patterns in `main.py`, `mcp_emp/core/`, and `mcp_emp/domains/` unless a task explicitly calls for a broader refactor.
- If a local-context rule conflicts with the live codebase, follow the codebase and update local docs when appropriate.
- Never add co-author attribution to commit messages. Do not include `Co-Authored-By` trailers or any similar attribution lines (e.g. `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`), regardless of the AI tool or model involved.
<!-- SPECKIT END -->

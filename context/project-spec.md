# mcp-emp Project Spec

## Current Scope

This repository currently covers:
- a minimal MCP server bootstrap in `main.py`
- a dependency baseline of `mcp` + `httpx` for tool exposure and outbound HTTP
- a place (`docs/`) for upstream API integration notes

## Primary Goals

- Keep the server production-ready even before all integrations are wired.
- Make adding a new upstream API incremental and low-risk (new domain package, not edits across the codebase).
- Keep the MCP tool surface small, well-named, and well-typed.
- Preserve a clear split between transport (`httpx`), mapping (domain mappers), and MCP exposure (tool functions).

## Existing Feature Areas

### MCP Server Bootstrap

The server should:
- start cleanly via `uv run python main.py` (or the configured script)
- register tools/resources/prompts in one well-known place
- expose a `stdio` transport by default; other transports are opt-in
- fail loudly on misconfiguration (missing env vars, unreachable upstream on startup health-check if any)

### Upstream HTTP Integrations (future)

For each upstream API:
- a domain package under `mcp_emp/domains/<domain>/`
- a `client.py` that holds the `httpx.AsyncClient` calls
- a `contract.py` with `*Payload` (upstream) and domain model types
- a `mapper.py` that turns `Payload → Model`
- a `tools.py` that registers MCP tools and returns mapped models

## MCP Tool Expectations

Every exposed tool should:
- have a short, action-oriented name (`get_employee`, not `employee_handler`)
- have a docstring that an LLM can use without reading the code
- declare parameters with explicit Python type hints / Pydantic models
- return JSON-serializable values (mapped domain models, not raw upstream DTOs)
- raise `mcp` errors (or return structured error content) on failure — never swallow exceptions

## Non-Goals

- Direct `httpx` calls scattered across tool functions
- Mixing upstream snake_case / inconsistent payload shapes into the MCP tool return values
- A monolithic `tools.py` containing every tool for every domain
- New abstractions before a second real use case appears
- Stateful in-process caches without explicit invalidation rules

## Quality Bar

- Ship minimal, coherent changes.
- Type everything that crosses a boundary (tool input/output, HTTP response parsing).
- Keep async semantics consistent — don't mix blocking `requests` calls into async tool handlers.
- Run `uv run ruff check` / `uv run pytest` (once configured) before declaring done.
- Smoke-test the server with an MCP client (or the MCP Inspector) for any change that touches tool schemas.

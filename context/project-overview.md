# mcp-emp Project Overview

## What This Repository Is

`mcp-emp` is a Python **MCP (Model Context Protocol) server** that exposes tools, resources, and prompts to MCP-compatible clients (e.g. Claude Desktop, IDE agents, pi).

The current entry point is `main.py`. The project is intentionally small and is meant to grow into a focused MCP server that wraps external APIs (via `httpx`) and exposes them as well-typed MCP tools.

## Product Direction

- Provide a clean, well-typed surface of MCP tools and resources.
- Wrap external HTTP APIs with `httpx` and expose them as ergonomic tools to LLM clients.
- Keep startup fast, dependencies minimal, and behavior predictable.
- Favor a small number of well-named tools over a large surface of thin wrappers.

## Developer Experience Principles

- Lead with clarity, not feature surface.
- Tool names, parameters, and docstrings are the UX — write them for an LLM caller, not a human reader.
- Keep tool inputs strictly typed (Pydantic / type hints) so the MCP schema is precise.
- Prefer explicit errors over silent fallbacks; an LLM client can recover when the error message is clear.

## Technical Snapshot

- Language: Python `>=3.12`
- Runtime / packaging: `uv` + `pyproject.toml`
- MCP framework: `mcp` (the official Python SDK)
- HTTP client: `httpx` (async-first)
- Validation: Pydantic (via the `mcp` SDK)

## Current App Shape

- `main.py` — process entry point (server bootstrap)
- `pyproject.toml` — project metadata and dependencies
- `uv.lock` — pinned dependency graph
- `docs/` — integration notes and external API references
- `context/` — agent-facing context (this folder)

As the server grows, code should be organized under a package (e.g. `src/mcp_emp/`) split by **domain** rather than technical layer. See `ddd-patterns.md`.

## Integration Direction

This project prefers a **domain-first MCP architecture**:
- one `mcp_emp/server.py` registers tools/resources/prompts
- shared HTTP behavior (auth, retries, base URL, error mapping) lives in `mcp_emp/core/http.py`
- domain contracts and mappers isolate upstream API payloads from the MCP-facing models
- tools return mapped models, not raw upstream payloads
- new external APIs are added as new domain packages, not as new files in a flat `tools/` folder

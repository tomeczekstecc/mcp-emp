---
name: ddd-patterns-check
description: Use when deciding where to place new files, when adding a new business domain, when an existing module is growing past its responsibility, or when refactoring code that currently lives in technical-layer folders. Ensures the pragmatic "lite DDD" domain-first layout of this MCP server is preserved.
---

# DDD Patterns Check

**Pattern source:** `context/ddd-patterns.md` — read it before applying this skill. It defines the canonical domain packages and per-domain file structure for this Python MCP server.

## Overview

This repo organizes code by **business domain** (upstream capability), not by technical layer. There is no top-level `mcp_emp/mappers/`, `mcp_emp/clients/`, or `mcp_emp/types/` — those live inside `mcp_emp/domains/<domain>/` next to the domain they describe.

Canonical locations:

| Location | Purpose |
|---|---|
| `mcp_emp/domains/<domain>/` | Domain package: `contract.py`, `mapper.py`, `client.py`, `tools.py`, optional `errors.py` |
| `mcp_emp/core/` | Cross-cutting infrastructure (`http.py`, `config.py`, `logging.py`, base errors) |
| `mcp_emp/server.py` | Server bootstrap + tool registration entry point |
| `tests/<domain>/` | Domain-specific tests mirroring the package layout |

## Workflow

1. Open `context/ddd-patterns.md` and confirm the current domain list and per-domain file structure.
2. Identify the business domain the new code belongs to (typically a single upstream capability). If it does not fit any, propose a new domain name and confirm before creating the package.
3. Place each artifact in the matching canonical location above. Do not create technical-layer siblings (`mappers/`, `clients/`, `utils/`) at the top of `mcp_emp/`.
4. Inside `mcp_emp/domains/<domain>/`, follow the standard files: `contract.py`, `mapper.py`, `client.py`, `tools.py`, optional `errors.py`.
5. Cross-check with `context/coding-standards.md` for the async / typing / Pydantic rules.

## Rules

- Domain name is a noun from the product language (`employees`, `tickets`, `timesheets`), not a technical concept.
- Never re-introduce top-level `mcp_emp/mappers/`, `mcp_emp/types/`, or a flat `mcp_emp/tools.py` containing every tool.
- Cross-cutting infrastructure (HTTP client lifespan, config, logging) lives only under `mcp_emp/core/`.
- One domain per upstream capability — do not split a single domain across multiple sibling packages.
- Tools must return mapped models (from `contract.py`), never raw upstream payloads or `httpx.Response` objects.
- Read/write split inside a domain follows the function-prefix CQRS-lite rule (`fetch_*`/`get_*`/`list_*` vs `create_*`/`update_*`/`delete_*`).

## Validation

- `ls mcp_emp/domains/<new-domain>/` shows the expected files.
- `uv run ruff check` and `uv run pytest` succeed.
- No new files appear directly under `mcp_emp/` outside `core/`, `domains/`, or `server.py` / `__init__.py`.
- The new domain is registered in `mcp_emp/server.py` via its `register(server)` function.

---
name: update-readme
description: Use when creating or updating a README.md file for this Python MCP server, when the user asks what a README should contain, wants to document their project, needs to onboard new developers, or asks to review or improve existing README content. Trigger proactively when a project is newly set up and has no README, or when the user says "add docs", "document this", "write a README", or "update the README". Even vague requests like "help new devs get started" or "describe the project" should trigger this skill.
---

# Update README

A README is often the first thing a developer reads about a project. The goal is to let a new contributor be running locally in under 5 minutes with zero tribal knowledge.

## Workflow

1. Read the existing `README.md` if one exists — preserve accurate sections, update what is stale.
2. Read `pyproject.toml` to get the actual project name, Python version requirement, dependencies, and any defined scripts/entry points.
3. Check for `.env.example` to populate the environment variables table accurately.
4. Inspect the top-level project structure (`main.py`, `mcp_emp/`, `tests/`, `docs/`, `context/`) to describe directories from what actually exists, not from memory.
5. Check the `context/` folder — link to those files instead of duplicating their content inline.
6. Write or update the README, then re-read it as if you have never seen this project before. Ask: can a new developer follow this without asking anyone a question?

## Sections (in order)

### 1. Project Name + One-liner
One sentence: what the project is and what problem it solves. For this repo: an MCP server that exposes [...] tools to MCP-compatible clients. No jargon, no marketing language.

### 2. Prerequisites
What must be installed before starting:
- Python version (from `pyproject.toml` `requires-python`, e.g. `>=3.12`)
- `uv` (the project's package/runtime manager)
- Any upstream service credentials needed (API keys, account access)

### 3. Getting Started
Step-by-step from clone to running locally. Every command must be copy-paste runnable — test them.

```bash
git clone <repo-url>
cd mcp_emp
cp .env.example .env   # fill in required values
uv sync
uv run python main.py
```

Include a one-paragraph note on **how to connect from an MCP client** (Claude Desktop config snippet, MCP Inspector command, or pi config) — that's the actual "does it work?" check for an MCP server.

### 4. Environment Variables
List every variable with a one-line description. Point to `.env.example` as the source of truth. Never include real values.

| Variable | Description |
|----------|-------------|
| `UPSTREAM_API_URL` | Base URL for the upstream API the server wraps |
| `UPSTREAM_API_TOKEN` | Bearer token for upstream authentication |

### 5. Available Commands
Each command with a plain-language description of what it does.

| Command | Description |
|---------|-------------|
| `uv sync` | Install/sync dependencies from `uv.lock` |
| `uv run python main.py` | Start the MCP server over stdio |
| `uv run ruff check` | Lint the codebase |
| `uv run ruff format` | Auto-format the codebase |
| `uv run pytest` | Run the test suite |

### 6. Project Structure
Top-level directories with one line each. Skip obvious ones (`.git`, `.venv`, `__pycache__`).

```
main.py            Process entry point (server bootstrap)
mcp_emp/           Package (created as the project grows past main.py)
  core/            Cross-cutting infrastructure (http, config, logging)
  domains/         One package per upstream capability (employees/, tickets/, ...)
  server.py        FastMCP server + tool registration
tests/             Pytest suite mirroring mcp_emp/
context/           Project documentation for AI and human contributors
docs/              Upstream API integration notes
```

### 7. Architecture Overview
Key patterns a contributor must know before touching code. Examples:

- "Async-first: tools are `async def`, I/O goes through a single shared `httpx.AsyncClient`."
- "Domain-driven layout: each upstream capability is a package under `mcp_emp/domains/<domain>/` with `contract.py`, `mapper.py`, `client.py`, `tools.py`."
- "Tools return mapped models (`Employee`), never raw upstream payloads (`EmployeePayload`)."

Link to `context/ddd-patterns.md` and `context/coding-standards.md` for details.

### 8. Tech Stack
Major dependencies with versions — Python version, `mcp` SDK, `httpx`, Pydantic, `uv`. Versions matter; pull them from `pyproject.toml`.

### 9. Contributing *(for team or open-source projects)*
- Branch naming convention
- Commit message format (Conventional Commits)
- PR process and review expectations

### 10. Deployment
How to ship the server. For an MCP server this usually means: where the binary/script is invoked from, and how MCP clients are configured to spawn it.

## Principles

**Lean over comprehensive.** Link to `context/` instead of duplicating. A short, accurate README beats a long, stale one.

**Commands must work.** Run every command in Getting Started from a clean state before publishing. Broken commands destroy trust faster than missing sections.

**Versions matter.** "Use Python" is unhelpful. "Use Python 3.12+" is actionable. Pull version requirements from `pyproject.toml` (`requires-python`).

**Keep it current.** When a PR changes setup steps, scripts, or env vars, update the README in the same PR.

**Link, don't duplicate.** If architectural detail lives in `context/`, reference it with a path. Don't copy it into the README where it will silently fall out of sync.

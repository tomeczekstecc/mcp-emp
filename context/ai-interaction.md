# mcp-emp AI Interaction Guidelines

## Working Style

- Be concise, direct, and practical.
- Explain non-obvious choices briefly.
- Preserve existing patterns unless the task asks for a broader rethink.
- Do not add speculative features or cleanup unrelated areas.

## Preferred Workflow

1. Read the relevant local context files (`context/`) before substantial work.
2. Inspect the live code (`main.py`, `mcp_emp/` once it exists) before proposing architecture changes.
3. Make the smallest coherent implementation that solves the task.
4. Verify with `uv run ruff check` and, when appropriate, `uv run pytest`.
5. For changes that affect MCP tool schemas, smoke-test with the MCP Inspector or an MCP client.
6. Summarize what changed, what was verified, and any remaining risk.

## Git Expectations

- Do not commit without permission.
- Keep commits focused; use conventional commit messages if a commit is requested.
- Never add co-author attribution (`Co-Authored-By: ...`) to commit messages, regardless of the AI tool involved.

## When To Pause

- Pause before large refactors with broad surface area.
- Pause when requirements are ambiguous and the ambiguity changes the MCP tool surface (names, parameters, return shapes).
- Pause if the live codebase conflicts with written guidance and the right choice is not obvious.
- Pause before adding a new top-level dependency — confirm it's needed and pin it via `uv add`.

## Tracking

- Capture follow-ups in `context/TODO.md` only when they are real and actionable.
- Avoid duplicating issue tracker content in the repo.

## Review Priorities

When reviewing or self-checking changes, prioritize:
- broken behavior and regressions in MCP tools
- type and Pydantic-validation mismatches between upstream payloads and domain models
- async correctness (no blocking calls inside async handlers, shared `httpx.AsyncClient` reused)
- error handling (no swallowed exceptions, clear messages reaching the LLM client)
- accidental drift from the documented domain layout

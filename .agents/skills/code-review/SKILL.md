---
name: code-review
description: Use when the user asks for a review, bug scan, regression check, or implementation critique for code in this Python MCP server. Focus on defects, behavioral regressions, async correctness, typing/Pydantic mismatches, missing edge handling, and maintainability risks before style notes.
---

# Code Review

Use this skill when the user asks for a review or when a change needs a focused quality pass.

## Review Priorities

1. Bugs and behavioral regressions in MCP tools
2. Async correctness (no blocking calls in `async def`, shared `httpx.AsyncClient` reused, no missing `await`)
3. Typing & Pydantic-validation mismatches between upstream payloads and domain models
4. Security or data exposure concerns (secrets in logs, unsafe upstream URL construction, leaked tokens)
5. Performance risks (per-call client creation, missing timeouts, unbounded fan-out)
6. Maintainability and design issues (domain placement, abstraction quality)

## Workflow

1. Read only the files relevant to the change.
2. Compare intent against the implementation.
3. Look for broken states, edge cases, and risky assumptions (None handling, empty lists, upstream 4xx/5xx paths).
4. Verify tool docstrings still accurately describe parameters and return shapes.
5. Prefer concrete findings with file references over broad opinions.
6. Keep summaries short after findings are listed.

## Rules

- Findings come first, ordered by severity.
- Prioritize real breakage (wrong tool return value, swallowed exception, broken async chain) over stylistic commentary.
- Call out missing validation, incorrect state flow, and surprising side effects.
- Flag any `except:` or `except Exception:` that silently continues without logging.
- Flag any sync I/O (`requests`, `open(...).read()` on large files, `time.sleep`) inside `async def`.
- Respect the project constitution: no automated test recommendations unless the user explicitly overrides project rules.
- If no findings exist, say so clearly and note any residual risk.

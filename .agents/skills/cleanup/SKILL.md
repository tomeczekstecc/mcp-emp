---
name: cleanup
description: Clean up project housekeeping tasks for this Python MCP server (add "run" to execute fixes)
argument-hint: run|check
---

Review the codebase for cleanup tasks:

1. Find stray `print(...)` statements in `mcp_emp/` and `main.py` (use logging instead) — skip lines preceded by `# [keep-print]`.
2. Find unused imports (use `ruff check --select F401`); skip imports preceded by `# [keep-commented:*]`.
3. Check for stale TODO/FIXME comments — skip any line or block tagged `# [keep-commented:*]`.
4. Find orphaned/unused Python files (modules not imported anywhere and not referenced in `pyproject.toml` scripts).
5. Check that `context/` files match actual project state (referenced paths still exist, tool names still match).
6. Keep `.env` and `.env.example` in sync — compare variable names (not values); whichever file has more variables wins, add any missing keys to the other.
7. Find `# type: ignore` and `# noqa` comments that may be stale (the underlying issue may already be fixed).
8. Run `/ai-artifacts-sync` to keep `.claude/` and `.agents/` skill directories in sync.
9. Find `Any` type sprawl — locate `Any` annotations beyond known intentional ones (often a sign a Pydantic model is missing).
10. Find unused dependencies — flag packages in `pyproject.toml` that are imported nowhere in `mcp_emp/` or `tests/` (use `uv pip list` cross-referenced with `grep -r "^import\|^from"`).
11. Verify env var consumption — check that every variable declared in `.env.example` is actually read somewhere (via `mcp_emp/core/config.py` or otherwise).
12. Find blocking calls inside `async def` — search for `time.sleep`, `requests.`, `urllib.request` in async functions.
13. Find ad-hoc `httpx.Client()` / `httpx.AsyncClient()` instantiations outside `mcp_emp/core/http.py` (clients should be reused, not created per call).
14. Find tools missing docstrings — every `@server.tool()` (or equivalent) decorated function must have a docstring; the docstring is the LLM-facing spec.
15. Find raw upstream payload shapes leaking into tool return values (functions returning `*Payload` types instead of mapped domain models).

**Mode: $ARGUMENTS**

If no argument or argument is "check":

- Only report findings, don't modify anything.
- List what WOULD be cleaned up.

If the argument is "run" or "fix":

- First, report all findings with numbered items.
- Then ask: "Which items would you like me to fix? (enter numbers like 1,3,5 or 'all' or 'none')"
- Wait for user response before making any changes.
- Only fix the items the user specifies.
- Report what you changed.
- After any code change, run `uv run ruff check` and `uv run ruff format` to verify.

---
name: performance
description: Use when improving runtime performance of this MCP server — async I/O hygiene, shared httpx client reuse, fan-out concurrency, upstream timeouts/retries, startup time, and MCP tool payload size. Triggers on requests to make tools faster, reduce upstream latency, fix blocking-in-async issues, or shrink tool return payloads.
---

# Performance

**Pattern source:** `context/performance.md` — read it before applying this skill. It is the single source of truth for the project's performance practices.

## Overview

Use this skill for performance work on the MCP server. The dominant costs are **upstream I/O latency**, **event-loop hygiene**, and **startup time** (MCP clients spawn the server on demand). Optimize those first, not CPU.

## Workflow

1. Identify whether the cost is upstream I/O, event-loop blocking, startup, payload size, or fan-out.
2. Check whether independent upstream calls can be parallelized with `asyncio.gather`.
3. Confirm a **single shared** `httpx.AsyncClient` is reused across calls (not created per request).
4. Verify explicit timeouts on every upstream call.
5. For list-returning tools, confirm a `limit` parameter and a minimal default return shape.
6. Use `$context7-first` when exact `httpx`, `asyncio`, or `mcp` SDK APIs matter.

## Rules

- No blocking calls inside `async def` tool handlers — no `time.sleep`, no `requests`, no sync SDKs without `anyio.to_thread.run_sync`.
- Reuse one `httpx.AsyncClient` per process, lifespan-managed in `mcp_emp/core/http.py`.
- Always set explicit `httpx.Timeout(...)`; never rely on defaults for production calls.
- Retry only **idempotent** requests (GET, HEAD, PUT) with bounded backoff + jitter.
- Bound fan-out concurrency with `asyncio.Semaphore` — never `asyncio.gather` over unbounded input.
- Avoid heavy module imports at top level; lazy-import inside the function that needs them.
- Cache only stable lookup data with documented invalidation; never cache per-user data without keying on user.
- Return minimal payloads to LLM clients; LLMs pay token cost for every field you return.

## Validation

- Run `uv run ruff check` and `uv run pytest`.
- For latency-sensitive changes, enable `httpx` response event hooks and confirm upstream timings in logs.
- Smoke-test the affected tool through the MCP Inspector and confirm responsive end-to-end behavior.
- For startup changes, measure with `python -X importtime main.py 2> import.log`.

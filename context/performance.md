# Performance Best Practices — Python / MCP

MCP server performance is dominated by **I/O latency** and **startup time**, not CPU. Optimize for those first.

## Async I/O Hygiene

### Reuse a single `httpx.AsyncClient`

```python
# ❌ Bad: new client per call (new TCP/TLS handshake every time)
async def fetch_employee(id: str):
    async with httpx.AsyncClient(base_url=BASE) as c:
        return (await c.get(f"/employees/{id}")).json()

# ✅ Good: one client per process, managed by the server lifespan
_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    assert _client is not None, "HTTP client not initialised"
    return _client

async def startup() -> None:
    global _client
    _client = httpx.AsyncClient(base_url=BASE, timeout=10.0)

async def shutdown() -> None:
    if _client is not None:
        await _client.aclose()
```

### Never block the event loop

```python
# ❌ Bad: blocks the entire server while sleeping
import time
async def slow_tool(): time.sleep(1)

# ❌ Bad: blocking HTTP inside an async tool
import requests
async def fetch_tool(): return requests.get(URL).json()

# ✅ Good: async sleep, async HTTP
import asyncio
async def slow_tool(): await asyncio.sleep(1)

async def fetch_tool():
    return (await get_client().get(URL)).json()
```

If you must call blocking code (e.g. a sync SDK), wrap it:

```python
import anyio
result = await anyio.to_thread.run_sync(blocking_sdk_call, arg1, arg2)
```

---

## Concurrency

### Parallelize independent upstream calls

```python
# ❌ Bad: sequential awaits
emp = await fetch_employee(id)
mgr = await fetch_employee(emp.manager_id)

# ✅ Good: gather what you can
import asyncio
emp, mgr = await asyncio.gather(
    fetch_employee(id),
    fetch_manager(id),
)
```

### Bound fan-out

```python
# ❌ Bad: unbounded — can hammer the upstream API
results = await asyncio.gather(*(fetch_employee(i) for i in ids))

# ✅ Good: cap concurrency
sem = asyncio.Semaphore(8)

async def bounded(i):
    async with sem:
        return await fetch_employee(i)

results = await asyncio.gather(*(bounded(i) for i in ids))
```

---

## Timeouts and Retries

- Always set explicit `httpx` timeouts. A hung upstream call should not freeze a tool indefinitely.
- Prefer short connect timeouts and a slightly longer read timeout:
  `httpx.Timeout(connect=2.0, read=10.0, write=10.0, pool=2.0)`.
- Retry **only idempotent** requests (GET, HEAD, PUT). Use exponential backoff with jitter.
- Cap total retry budget; don't let retries push a tool over its caller's timeout.

---

## Caching

Caching is appropriate for **stable upstream data** that is read often.

```python
from functools import lru_cache

# ✅ Good: cache config/lookups that don't change at runtime
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

For async cached fetches with TTL, use a small in-memory cache (e.g. `aiocache`) — but only after profiling shows a real hot path. **Document invalidation rules** when you add one.

**Do not cache:**
- Per-user data without keying on the user.
- Anything that mutates upstream state.
- Anything where stale data would mislead the LLM client.

---

## Startup Time

MCP clients (Claude Desktop, IDE agents) spawn the server on demand. Slow startup = slow first tool call.

- Import heavy modules **lazily**, inside the function that needs them.
- Don't perform upstream health checks on import — defer until first use, or run them in a background task.
- Read config once, eagerly, with clear error messages — but don't pre-fetch data.

```python
# ❌ Bad: 800ms import cost on every server start
import pandas as pd

# ✅ Good: lazy import — only pay the cost if the relevant tool runs
def _load_pandas():
    import pandas as pd
    return pd
```

---

## Payload Size

LLM clients pay token cost for tool return values.

- Return only the fields the caller asked for. Add an `include`/`fields` parameter for large records.
- Default to **summary** shapes for `list_*` tools; provide a separate `get_*` for the full record.
- Cap list responses (e.g. `limit: int = 50`) and document the cap in the docstring.
- Strip nullable fields that are `None` if the upstream returns them verbosely — Pydantic `model_dump(exclude_none=True)` is your friend.

---

## Profiling

Before optimizing, measure:

- `python -X importtime main.py 2> import.log` — import cost breakdown.
- `cProfile` for CPU hotspots: `python -m cProfile -o out.prof -m mcp_emp`.
- `httpx` event hooks to log upstream latency:

```python
async def log_response(response):
    elapsed = response.elapsed.total_seconds() * 1000
    logger.info("upstream %s %s %.0fms", response.request.method, response.request.url, elapsed)

client = httpx.AsyncClient(event_hooks={"response": [log_response]})
```

---

## Checklist

Before marking a feature complete:

### I/O
- [ ] Single shared `httpx.AsyncClient`, not per-call
- [ ] Explicit timeouts on every upstream call
- [ ] No blocking calls inside `async def` tool handlers
- [ ] Independent calls parallelized with `asyncio.gather`
- [ ] Fan-out bounded with `asyncio.Semaphore`

### Startup
- [ ] No heavy imports at module top-level unless required
- [ ] No upstream calls at import time

### Payload
- [ ] Return shapes are minimal and documented
- [ ] List endpoints have a `limit` and a sane default

### Errors
- [ ] Upstream errors mapped to clear domain errors
- [ ] Retries are bounded and only on idempotent requests

---

## Quick Reference

**Performance hierarchy:**
1. **Don't do the work:** cache, skip, return minimal payloads.
2. **Don't wait:** `asyncio.gather` independent calls.
3. **Don't block:** keep the event loop free, offload sync calls to a thread.
4. **Don't reconnect:** reuse one `httpx.AsyncClient`.
5. **Fail fast:** explicit timeouts beat hung tools.

**Remember:** Premature optimization is the root of all evil. Profile first, then optimize the bottlenecks.

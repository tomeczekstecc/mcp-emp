# Exception serialisation: `@readable` / `@mutating` decorators, not FastMCP exception handler

All tool functions are wrapped by exactly one of two decorators from `core/modes.py`:

- **`@mutating`** — raises `ReadOnlyMode` before the body runs when `MCP_EMP_READ_ONLY=true`; catches any `EmpError` raised inside and converts it to `McpError` with `data={"code": exc.code, "details": exc.details}`.
- **`@readable`** — same `EmpError → McpError` conversion, no READ_ONLY gate.

This gives every tool (read and write alike) structured `error.data.code` in the JSON-RPC response without touching FastMCP's exception handler hook, which would require verifying that the SDK's `data` slot serialisation is stable across versions.

We chose decorators over (a) a central FastMCP exception handler — which relies on an SDK hook whose `data`-slot support we haven't verified at ≥1.27 — and over (b) per-tool `try/except` blocks — which would repeat the same conversion ~15 times.

## Consequences

- Lint rule: every `@server.tool()` function has exactly one of `@readable` / `@mutating` directly below it.
- `_to_mcp_error(exc: EmpError) -> McpError` is a private helper in `core/modes.py`; the JSON-RPC layer code is always `-32603` (INTERNAL_ERROR); our application code is in `data.code`.
- `@mutating` ADR-0003 is extended: the decorator now also performs the error conversion, not just the READ_ONLY gate.
- If FastMCP adds a first-class `data`-aware exception handler in a future release, migrating away from the decorators is mechanical (remove the `try/except` blocks from both decorators).

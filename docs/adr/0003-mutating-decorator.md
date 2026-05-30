# Mutating-tool gate: `@mutating` decorator, not inline checks or FastMCP Context

Mutating tools (those that write to EMP or issue confirmation tokens) are guarded by a `@mutating` decorator from `core/modes.py`, stacked directly below `@server.tool()`. The decorator raises `ReadOnlyMode` before any tool body runs when `MCP_EMP_READ_ONLY=true`. `dry_run` logic stays in each tool body because the dry-run payload shape differs per tool.

We chose this over (a) inline checks — which require every tool author to remember the check and make a lint rule necessary just to compensate — and over (b) FastMCP `Context.require_writable()` — which leaks an extra parameter into the tool signature that must be explicitly excluded from the MCP schema, a subtle footgun.

## Consequences

- `@server.tool()` is always the outermost decorator; `@mutating` is always directly below it (documented rule in module layout).
- Lint test: every tool function with a `dry_run` parameter must be decorated with `@mutating`.
- `dry_run: bool = False` is the conventional last keyword argument on every mutating tool.
- `ReadOnlyMode` is a typed exception (`code=READ_ONLY`) with a hint to unset the flag.
- `Context` injection (via FastMCP lifespan) remains available for other concerns (confirmation store, identity) if needed later.

# Tool result shape: typed model on success, typed exception on failure

MCP tools return their domain model directly (`-> Task`, `-> list[TaskType]`) and signal failure by raising typed exceptions that carry a stable `code` plus structured `details`. The MCP SDK serialises those exceptions into a JSON-RPC error whose `data` slot carries `{code, details}`. No application-level `{ok, data|error}` envelope wraps successes.

We chose this over a uniform envelope because (a) it matches FastMCP idiom — `-> Task` becomes the tool's MCP schema, exactly what the LLM needs; (b) the 17-code error vocabulary survives unchanged, just on a different wire path (`error.data.code` instead of `data.error.code`); (c) tests assert on the model, not on `data["..."]`; (d) it leaves us less exposed to MCP SDK churn.

Dry-run, confirmation, and pre-flight metadata that don't fit the natural model are expressed as **dedicated typed wrappers on mutating tools only** (e.g. `TaskCreateResult { task, dry_run, validated }`) — not retrofitted onto every read tool.

## Consequences

- **Doc 08** rewritten: the envelope spec becomes the exception-class spec; codes and the confirmation-token contract are unchanged.
- **Doc 06** rewritten: every tool's "Returns" section is a model name or wrapper, not `Envelope[T]`.
- **Doc 11** simpler: assertion patterns shrink; envelope-shape lint test is replaced by an "exceptions raise typed errors with `code`" lint test.
- Rejected alternative **A (drop envelope entirely, no code vocabulary)** would have lost the closed enum of error codes the LLM relies on for branching; rejected alternative **B (keep envelope)** would have fought the SDK and obscured tool schemas.

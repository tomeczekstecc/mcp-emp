---
name: design-pattern-check
description: Use when the user wants an architectural or design-pattern review for code in this MCP server repository. Focus on module boundaries, async/sync separation, state ownership, reuse decisions, abstraction quality, accidental coupling, and whether the current pattern is simpler than the alternatives.
---

# Design Pattern Check

Use this skill when a change needs an architectural sanity check.

## What To Evaluate

- module and package boundaries (domain vs core vs server bootstrap)
- async/sync separation — no blocking calls inside async handlers, no sync SDKs leaking into async paths
- where Pydantic models are defined and how they cross boundaries
- reuse versus duplication tradeoffs
- abstraction quality (do helpers earn their existence, or just add indirection?)
- accidental coupling to upstream API shapes leaking into MCP tool return values

## Workflow

1. Identify the main responsibility of the touched module.
2. Check whether HTTP transport, mapping, and MCP exposure are properly separated (`client.py` → `mapper.py` → `tools.py`).
3. Look for premature abstractions or duplication that now deserves extraction.
4. Verify domain placement against `context/ddd-patterns.md`.
5. Judge the pattern against project principles: simple, surgical, typed, and DRY without over-engineering.

## Rules

- Prefer simpler composition over heavier patterns by default.
- Reject abstractions that hide straightforward logic without real leverage.
- Accept duplication briefly when it keeps the domain clearer than early reuse.
- Call out when raw upstream payload shapes (snake_case fields, optional bags) are leaking into tool return values.
- Call out when sync HTTP / blocking I/O is creeping into async tool handlers.

## Pattern References

This skill is cross-cutting. Consult the relevant pattern doc(s) when judging a change:

- Module & package boundaries, abstraction quality, reuse vs duplication — `context/ddd-patterns.md`, `context/coding-standards.md`
- Async correctness & upstream I/O behavior — `context/performance.md`, `context/coding-standards.md`
- Coupling to upstream API shapes — `context/ddd-patterns.md` (Payload vs Model split)
- Project scope & non-goals — `context/project-spec.md`

When a referenced pattern conflicts with the live codebase, follow the codebase and flag the doc for an update.

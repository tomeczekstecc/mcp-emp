---
name: design-pattern-check
description: Use when the user wants an architectural or design-pattern review for frontend code in this repository. Focus on component boundaries, state ownership, reuse decisions, abstraction quality, accidental coupling, and whether the current pattern is simpler than the alternatives.
---

# Design Pattern Check

Use this skill when a change needs an architectural sanity check.

## What To Evaluate

- component and module boundaries
- state ownership and data flow
- reuse versus duplication tradeoffs
- abstraction quality
- accidental coupling to framework or backend details

## Workflow

1. Identify the main responsibility of the touched module or component.
2. Check whether state, rendering, and side effects are mixed too tightly.
3. Look for premature abstractions or duplication that now deserves extraction.
4. Judge the pattern against project principles: simple, surgical, clean, and DRY without over-engineering.

## Rules

- Prefer simpler composition over heavier patterns by default.
- Reject abstractions that hide straightforward logic without real leverage.
- Accept duplication briefly when it keeps the feature clearer than early reuse.
- Call out when Laravel integration concerns are leaking into presentational code too early.

## Pattern References

This skill is cross-cutting. Consult the relevant pattern doc(s) when judging a change:

- Component & module boundaries, abstraction quality, reuse vs duplication — `context/component-patterns.md`, `context/ddd-patterns.md`
- State ownership & data flow — `context/zustand-store.md`, `context/api-mutation-pattern.md`
- Coupling to framework/backend — `context/nextjs-patterns.md`, `context/api-mutation-pattern.md`, `context/ddd-patterns.md`
- Streaming, loading and error boundaries — `context/suspense-pattern.md`
- Wizard-specific architecture — `context/wizard-pattern.md`
- Accessibility, performance, UI hierarchy as design constraints — `context/accessibility.md`, `context/performance.md`, `context/ui-patterns.md`

When a referenced pattern conflicts with the live codebase, follow the codebase and flag the doc for an update.

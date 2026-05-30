---
name: component-patterns-check
description: Use when a React component is growing past ~300-500 lines, has many `useState`/`useEffect`, mixes data fetching with rendering, has long prop lists, or is hard to test. Guides extraction into custom hooks and feature components per this repository's refactoring playbook.
---

# Component Patterns Check

**Pattern source:** `context/component-patterns.md` — read it before applying this skill. It contains the full before/after examples for the custom hook + feature component refactor.

## Overview

When a component crosses the complexity threshold, extract it in two phases:

1. **Custom hooks** — move business logic, data fetching state, and side-effect orchestration out of the JSX.
2. **Feature components** — split the rendered UI into smaller, focused presentational components.

Trigger signs:

- Component >500 lines
- 10+ `useState` or `useEffect`
- Multiple distinct concerns in one file
- Long parameter lists (>5 props)
- Deeply nested conditional logic

Keep as-is when: <300 lines, single responsibility, primarily presentational, simple CRUD.

## Workflow

1. Open `context/component-patterns.md` and confirm the current extraction patterns and examples.
2. List the concerns in the file (e.g. fetching, filtering, selection, submission). One concern → one hook.
3. Extract each concern into a custom hook under `src/hooks/<domain>/` (or feature-local `hooks/`). Hook returns state + actions; no JSX.
4. Once logic is extracted, split the JSX into focused subcomponents under `src/components/<domain>/`.
5. The original component becomes a thin orchestrator: call hooks, render subcomponents, wire callbacks.
6. Cross-check `context/ddd-patterns.md` for file placement and `context/api-mutation-pattern.md` if any extracted hook is a mutation.

## Rules

- Hooks own state and side effects, components own rendering. No `useEffect` for data orchestration left in the leaf component.
- Each subcomponent should be testable with props alone — no hidden context dependencies sneaked in.
- Do not extract prematurely. A 200-line focused component is fine.
- Do not create barrel-only "wrapper" components that add no semantics.
- Keep `"use client"` boundaries at the smallest interactive leaf, not the orchestrator.

## Validation

- The refactored orchestrator file is materially shorter and has no business logic.
- Each new hook has a single clear return shape.
- `pnpm lint` and `pnpm build` succeed; visible behavior unchanged.

---
name: zustand-store-check
description: Use when adding a new Zustand slice, modifying the global store, or deciding whether a piece of state belongs in Zustand vs `useState` vs TanStack Query in this repository. Ensures the single `useStore` + slices layout under `src/lib/store/` is preserved.
---

# Zustand Store Check

**Pattern source:** `context/zustand-store.md` — read it before applying this skill. It defines the slice composition, types layout, decision rules for state placement, and the **Best Practices** section (re-render prevention, atomic selectors, actions/state separation, middleware, scaling) sourced from https://www.youtube.com/watch?v=6tEQ1nJZ51w.

## Overview

The app has a **single app-scoped Zustand store** (`useStore`) composed from **slices** (one file per domain) and wired through a single `create()` call with the `devtools` middleware.

State placement decision:

| State kind | Home |
|---|---|
| Server data | TanStack Query |
| Local-to-subtree UI state | `useState` / `useReducer` |
| Cross-tree, cross-route client state | Zustand slice |

## Workflow

1. Open `context/zustand-store.md` and confirm the current slice list and types.
2. Verify the state truly needs to cross component-tree boundaries. If not, use `useState`. If it's server data, use TanStack Query.
3. Create a new slice file in `src/lib/store/<domain>.slice.ts`. Mirror the existing slice shape.
4. Declare the slice's interface in `src/lib/store/types.ts` and add it to the `StoreState` union.
5. Wire the slice into the single `create()` call in `src/lib/store/index.ts`.
6. Export selectors/hooks colocated with the slice when reuse warrants it; otherwise use inline `useStore(s => s.x)` at the call site.

## Rules

- One store, many slices. **Do not** create a second `create()` call (exception: isolated `persist` stores go in `<domain>.store.ts`).
- Slice files live only under `src/lib/store/`. No ad-hoc stores elsewhere.
- Never put server data in Zustand — it goes in TanStack Query.
- Keep slice interfaces narrow and named per domain in `types.ts`.
- Devtools middleware stays enabled in development; do not strip it.
- **Always select with a selector** — never call `useStore()` naked.
- **`useShallow` for object/array selectors** — any selector returning a new object/array needs `useShallow` to avoid infinite re-renders.
- **Actions-only selectors** — select actions separately from state so action consumers never re-render on state changes.
- **Named selectors** — export a `selectX` function from the slice file when the same selector is used in ≥2 components.
- **Action names are required** — always pass `'slice/actionName'` as the third argument to `set()`.
- **Async work stays outside** — handle async in TanStack mutation hooks; write only resulting UI state into the store.

## Validation

- `ls src/lib/store/` shows `index.ts`, `types.ts`, and one `*.slice.ts` per domain.
- `pnpm lint` and `pnpm build` succeed.
- Redux DevTools shows the slice's actions when the new state mutates.

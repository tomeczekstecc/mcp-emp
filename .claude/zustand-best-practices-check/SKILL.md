---
name: zustand-best-practices-check
description: Use when auditing, reviewing, or writing any Zustand `useStore` call, selector, slice action, or middleware in this repository. Checks for missing `useShallow`, naked store subscriptions, inline derived state, missing action names, async inside set(), and missing named selectors. Source: https://www.youtube.com/watch?v=6tEQ1nJZ51w documented in context/zustand-store.md § Best Practices.
---

# Zustand Best Practices Check

**Pattern source:** `context/zustand-store.md` § Best Practices — read it before applying this skill.

## Checklist

Run every item against the file(s) in scope. Report each finding with file + line, severity, and the fix.

---

### 1. No naked `useStore()` calls
Every call must pass a selector function.

```ts
// ❌
const store = useStore()

// ✅
const count = useStore(s => s.count)
```

**Grep:** `useStore()` (no argument)

---

### 2. `useShallow` on object/array selectors
Any selector that returns a new object literal, array literal, or calls `.map`/`.filter`/`Object.values` must be wrapped with `useShallow`.

```ts
// ❌ — new object reference every render
const { form, validation } = useStore(s => ({ form: s.wizards[name]?.form, validation: s.wizards[name]?.meta.validation }))

// ✅
import { useShallow } from 'zustand/react/shallow'
const { form, validation } = useStore(useShallow(s => ({ form: s.wizards[name]?.form, validation: s.wizards[name]?.meta.validation })))
```

Also flag `useStore(s => s.someObject)` where the selected value is a nested object/record — it returns a reference that may be stable, but confirm before passing.

**Grep:** `useStore(s =>` then check the return shape.

---

### 3. Action selectors separated from state selectors
Actions (functions) must be selected in their own `useStore` call so the component is never re-rendered when unrelated state changes.

```ts
// ❌ — mixed in one object selector, also needs useShallow
const { count, increment } = useStore(s => ({ count: s.count, increment: s.increment }))

// ✅ — separate subscriptions
const count     = useStore(s => s.count)
const increment = useStore(s => s.increment)
```

---

### 4. Action names on every `set()` call
Every `set()` inside a slice must pass `'slice/actionName'` as the third argument and `false` as the second.

```ts
// ❌
set({ count: 0 })
set(s => ({ count: s.count + 1 }), false)

// ✅
set({ count: 0 }, false, 'counter/reset')
set(s => ({ count: s.count + 1 }), false, 'counter/increment')
```

**Grep:** `set(` inside `src/lib/store/` — verify every occurrence has three arguments.

---

### 5. No async work inside `set()` or slice creators
Async logic (fetch, await, timers) must live in TanStack mutation hooks or React callbacks. Slices only receive the result via a synchronous `set()`.

```ts
// ❌
generateReport: async (id) => {
  const result = await api.generate(id)
  set({ generationStates: { [id]: result.state } }, false, 'reports/setGeneration')
}

// ✅ — async stays in the hook; slice only stores the outcome
// hook: await mutateAsync(); setGenerationState(id, 'done')
```

---

### 6. Named selectors exported for ≥2 consumers
When the same selector expression appears in two or more components, extract it to a named export from the slice file.

```ts
// src/lib/store/reports.slice.ts
export const selectGenerationState =
  (reportId: number) => (s: StoreState) =>
    s.generationStates[reportId] ?? 'idle'

// usage
const state = useStore(selectGenerationState(report.id))
```

**Check:** grep for duplicated `useStore(s => s.<slice>` patterns across `src/`.

---

### 7. No server data stored in Zustand
State fetched from the API belongs in TanStack Query (`useQuery` / `useMutation`). Zustand holds only client-only UI state.

**Red flags:** slice fields named `list`, `items`, `data`, `results`, or any field populated directly from an API response without going through a TanStack mutation callback.

---

### 8. Single `create()` call in `index.ts`
There must be exactly one `create()` call in `src/lib/store/index.ts`. Isolated `persist` stores are the only exception and must live in `src/lib/store/<domain>.store.ts` (not `index.ts`).

---

### 9. `resetStore` utility exists
A `resetStore()` function should be exported from `src/lib/store/index.ts` for use in tests and logout flows.

```ts
export function resetStore() {
  useStore.setState(initialState, true) // true = replace, not merge
}
```

---

## Severity guide

| Symbol | Meaning |
|---|---|
| 🔴 | Bug risk — stale renders, infinite loops, or incorrect state |
| 🟡 | Maintainability / performance — correct today but will hurt at scale |
| 🟢 | Nice-to-have — follows best practice, low urgency |

| Check | Default severity |
|---|---|
| Naked `useStore()` | 🔴 |
| Missing `useShallow` on object selector | 🔴 |
| Mixed state + action in one selector | 🟡 |
| Missing action name in `set()` | 🟡 |
| Async inside slice | 🔴 |
| Inline selector duplicated ≥2× | 🟡 |
| Server data in Zustand | 🔴 |
| Multiple `create()` calls | 🔴 |
| Missing `resetStore` | 🟢 |

## Workflow

1. Read `context/zustand-store.md` § Best Practices.
2. Identify scope: single component, a feature folder, or full-codebase scan.
3. Run each checklist item against the scope.
4. Report all findings grouped by severity (🔴 first).
5. Ask the user which findings to fix before making any changes.

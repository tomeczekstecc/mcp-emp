---
name: suspense-pattern-check
description: Use when adding a loading state, error boundary, streamed widget, or React 19 `use()` call in this repository's App Router pages. Ensures file-based (`loading.tsx` / `error.tsx`) and inline `<Suspense>` boundaries follow the documented skeleton conventions.
---

# Suspense Pattern Check

**Pattern source:** `context/suspense-pattern.md` — read it before applying this skill. It documents both file-based and inline Suspense usage and the skeleton conventions.

## Overview

Two complementary Suspense styles are used:

1. **File-based** — `loading.tsx` / `error.tsx` co-located with `page.tsx` in a route segment. Next.js wraps the segment automatically.
2. **Inline `<Suspense fallback={…}>`** — inside a Server Component layout for fine-grained streaming of a single slow widget.

React 19 `use()` is used to pass server-resolved promises into Client Components without blocking the page shell.

## Workflow

1. Open `context/suspense-pattern.md` and confirm the current skeleton conventions and `use()` usage rules.
2. Decide the granularity: whole-segment fallback → `loading.tsx`; partial slow widget → inline `<Suspense>`.
3. For root-level (`src/app/loading.tsx`) use hand-crafted `animate-pulse` shapes that mirror the landing/page shell — no `Skeleton` import.
4. For feature segments (`src/app/(app)/*/loading.tsx`) use shadcn `<Skeleton>` mirroring the feature's table/card/list shape.
5. `error.tsx` must be `"use client"` and provide a reset path.

## Rules

- `loading.tsx` mirrors the real layout — skeleton shape ≈ rendered shape.
- Do not put `loading.tsx` next to a Client Component page; it only works for segments with async server work.
- Inline `<Suspense>` wraps only the slow leaf, not the entire layout.
- Use `use(promise)` only inside Client Components that are descendants of a `<Suspense>` boundary.
- Do not double-wrap: if a segment already has `loading.tsx`, do not add a redundant inline boundary around the whole page.

## Validation

- Force-slow the data source (artificial delay) and confirm the skeleton renders, then is replaced by content.
- Throw inside the server component and confirm `error.tsx` renders with a working reset.
- `pnpm build` succeeds.

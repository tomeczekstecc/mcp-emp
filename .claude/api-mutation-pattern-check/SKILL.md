---
name: api-mutation-pattern-check
description: Use when implementing or reviewing write operations (create/update/delete) against the backend in this repository, especially when introducing a TanStack Query mutation, optimistic update, rollback, toast feedback, or cache invalidation. Ensures the commands.ts (pure transport) + mutation hook (UX orchestration) layering is respected.
---

# API Mutation Pattern Check

**Pattern source:** `context/api-mutation-pattern.md` — read it before applying this skill. It is the single source of truth for layering, naming, and examples.

## Overview

Write operations in this repo are split into two layers:

- **`src/lib/api/domains/<domain>/commands.ts`** — pure async functions, one HTTP call each, framework-agnostic, throw on failure. **Must not import React or `@tanstack/react-query`.**
- **Hook layer** (`src/hooks/<domain>/` or `src/components/<domain>/hooks/`) — `use<Verb><Entity>` hooks that wrap commands with `useMutation`, optimistic updates, rollback, toast, and `queryClient.invalidateQueries` in `onSettled`.

Reads mirror this split: `queries.ts` + `useQuery` consumer hooks.

## Workflow

1. Open `context/api-mutation-pattern.md` and confirm the current rules (naming, optimistic update shape, rollback, invalidation keys).
2. Locate the target domain under `src/lib/api/domains/<domain>/`. Add or update the command in `commands.ts`.
3. Add or update the hook in `src/hooks/<domain>/` (or feature-local `hooks/`) named `use<Verb><Entity>`.
4. In the hook: snapshot in `onMutate`, restore in `onError`, invalidate in `onSettled`, surface toasts.
5. Wire the hook into the UI leaf (button / form submit). Do not call the command directly from a component.

## Rules

- `commands.ts` never imports React, hooks, or `@tanstack/react-query`.
- One command = one HTTP call. Compose multiple commands in the hook if needed.
- Optimistic updates must always have a rollback path captured in `onMutate`.
- Always invalidate the relevant query keys in `onSettled` (not `onSuccess` only).
- Toasts/feedback live in the hook layer, never in `commands.ts`.
- Mirror the read side: queries belong in `queries.ts`, consumed via `useQuery` hooks.

## Validation

- Grep the new command file: `grep -E "react|@tanstack" src/lib/api/domains/<domain>/commands.ts` must return nothing.
- Run `pnpm lint` and `pnpm build`.
- Manually trigger the mutation and confirm optimistic UI, rollback on forced error, and refetch after settle.

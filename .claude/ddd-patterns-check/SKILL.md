---
name: ddd-patterns-check
description: Use when deciding where to place new files, when adding a new business domain, when an existing folder is growing past its responsibility, or when refactoring code that currently lives in technical-layer folders. Ensures the pragmatic "lite DDD" domain-first layout of this repository is preserved.
---

# DDD Patterns Check

**Pattern source:** `context/ddd-patterns.md` — read it before applying this skill. It defines the canonical domain folders and per-domain API structure.

## Overview

This repo organizes code by **business domain**, not by technical layer. There is no `src/lib/mappers/` or `src/lib/types/` at the top level — those live inside `src/lib/api/domains/<domain>/` next to the domain they describe.

Canonical locations:

| Location | Purpose |
|---|---|
| `src/app/<domain>/` | Feature routes |
| `src/components/<domain>/` | Feature UI components |
| `src/lib/api/domains/<domain>/` | API integration: contracts, mappers, queries, commands |
| `src/lib/<domain>/` | Domain helpers shared across routes/components |
| `src/hooks/<domain>/` | Domain-specific hooks |

## Workflow

1. Open `context/ddd-patterns.md` and confirm the current domain list and per-domain file structure.
2. Identify the business domain the new code belongs to. If it does not fit any, propose a new domain name and confirm before creating folders.
3. Place each artifact in the matching canonical location above. Do not create technical-layer siblings (`types/`, `mappers/`, `utils/`) at the top of `src/lib/`.
4. Inside `src/lib/api/domains/<domain>/`, follow the standard files: `contracts.ts`, `mappers.ts`, `queries.ts`, `commands.ts`, `index.ts`.
5. Cross-check with `context/api-mutation-pattern.md` for the read/write split inside the domain.

## Rules

- Domain name is a noun from the product language (`applications`, `dashboard`, `menu`, `wizard`), not a technical concept.
- Never re-introduce top-level `src/lib/mappers/`, `src/lib/types/`, or `src/lib/api/<file>.ts` outside a domain.
- Auth-facing routes live under `src/app/auth/`.
- Feature UI imports from its own domain first; cross-domain imports go through `src/lib/api/domains/<domain>/index.ts` barrels.
- One domain per concept — do not split a single domain across multiple sibling folders.

## Validation

- `ls src/lib/api/domains/<new-domain>/` shows the expected files.
- `pnpm lint` and `pnpm build` succeed.
- No new files appear directly under `src/lib/api/` (only under `src/lib/api/domains/` or `src/lib/api/core/`).

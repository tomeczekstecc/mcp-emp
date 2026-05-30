---
name: web-frontend-best-practices
description: Use when designing, implementing, or refactoring frontend code in this repository, especially for component structure, state boundaries, maintainability, readability, modern React and Next.js practices, and practical code quality decisions for apps/web.
---

# Web Frontend Best Practices

## Overview

Use this skill for general frontend engineering guidance in `apps/web`. Favor simple component boundaries, explicit state flow, maintainable rendering logic, and practical React and Next.js patterns that fit the current codebase.

## Core Principles

- KISS: keep the component tree and state model as simple as the feature allows.
- DRY: share logic only when the abstraction improves clarity.
- SRP: keep components focused on one UI responsibility.
- Explicitness: prefer obvious props, state, and effects over hidden coupling.

## Workflow

1. Read the route, feature components, and shared primitives involved.
2. Keep state as local as possible before lifting it.
3. Split large components when rendering logic, mutation logic, and view composition are fighting each other.
4. Prefer reusable primitives only when they remain easy to understand.
5. Use `$context7-first` for exact React, Next.js, or library API details when they may be version-sensitive.

## Rules

- Keep presentational and data-heavy concerns reasonably separated.
- Avoid giant client components when smaller interactive leaves will do.
- Keep effects purposeful and minimal.
- Prefer typed props and narrow interfaces.
- Preserve repo conventions around aliases, UI primitives, and app structure.

## Validation

- Run `npm run check-types` from `apps/web`.
- Run `npm run build` for larger refactors.

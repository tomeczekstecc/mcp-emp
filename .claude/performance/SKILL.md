---
name: web-performance
description: Use when improving frontend performance in this repository, especially for bundle size, rendering cost, data fetching behavior, client component boundaries, image handling, and perceived responsiveness in Next.js apps/web features.
---

# Web Performance

**Pattern source:** `context/performance.md` — read it before applying this skill. It is the single source of truth for the project's performance budgets and techniques.

## Overview

Use this skill for frontend performance work in `apps/web`. Focus on the biggest sources of cost first: too much client rendering, repeated work, broad invalidation, oversized assets, and poor loading behavior.

## Workflow

1. Identify whether the cost is network, render, hydration, bundle, or interaction related.
2. Check whether a server component boundary can remove client-side work.
3. Minimize unnecessary rerenders, cache churn, and broad mutations.
4. Keep images, uploads, and large UI blocks deliberate.
5. Use `$context7-first` when exact Next.js or React performance APIs matter.

## Rules

- Prefer moving work to the server when it reduces client complexity.
- Keep client components small when they need interactivity.
- Avoid premature micro-optimizations without a clear bottleneck.
- Fix broad cache invalidation and repeated fetch work before adding memoization everywhere.
- Optimize perceived performance, not just raw metrics.

## Validation

- Run `npm run build` from `apps/web`.
- Check the affected flow for loading behavior and interaction responsiveness.

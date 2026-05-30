---
name: context7-first
description: Use when coding against libraries, frameworks, SDKs, or CLIs whose APIs may be version-sensitive, unfamiliar, or easy to misremember. Apply this skill before implementation to resolve the right Context7 library ID, query narrow official docs, and ground code changes in current documentation instead of memory.
---

# Context7 First

## Overview

Use Context7 as the default documentation lookup step before coding against a library with unstable or exact syntax. Keep queries narrow, prefer official documentation surfaced through Context7, then map the result back into local repo conventions.

## Trigger Checklist

Use this skill when one or more of these are true:

- the task depends on exact framework or SDK syntax,
- the library is fast-moving or version-sensitive,
- the code pattern is unfamiliar,
- the change involves setup, configuration, decorators, hooks, middleware, or integration APIs,
- guessing would create churn or subtle bugs.

Skip Context7 only when the task is trivial and the local code already provides a clear, repeated pattern.

## Workflow

1. Identify the exact library or framework involved.
2. Resolve the Context7 library ID first.
3. Query only the narrow topic needed for the current change.
4. Extract the relevant pattern or API shape from the docs.
5. Compare that guidance with the local repo convention.
6. Implement using the documented API while preserving repo-local style.
7. If the docs and local code disagree, prefer the user's requested direction or preserve local conventions unless the task calls for an update.

## Query Rules

- Start with the smallest useful question.
- Prefer one focused query over a broad survey.
- Ask about the exact feature you are changing, such as middleware registration, router decorators, auth hooks, or ORM relations.
- Do not dump large generic documentation into context.
- Re-query only when a new uncertainty appears.

## Output Rules

- Treat Context7 as the source of truth for library behavior and signatures.
- Treat the local repository as the source of truth for naming, layering, and file placement.
- Call out when you are inferring from docs rather than copying an exact local pattern.

## Good Uses

- NestJS module wiring, decorators, guards, interceptors, or lifecycle hooks
- Next.js routing, server actions, caching, or metadata APIs
- Drizzle schema, relations, and query syntax
- tRPC router definitions and procedure patterns
- auth library integration flows
- UI library component APIs that change by version

## Anti-Patterns

- coding from memory when the API is likely to have changed,
- querying Context7 for broad "tell me everything" summaries,
- ignoring strong local conventions after reading the docs,
- using stale snippets from unrelated tutorials instead of focused documentation.

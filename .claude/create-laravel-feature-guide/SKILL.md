---
name: create-laravel-feature-guide
description: Produce a Laravel backend feature guide for a new frontend feature, including an endpoint proposal, request body shape, response DTO shape, and feature description aimed at the Laravel backend developer. Use when the user asks to "draft a backend contract", "write a Laravel feature guide", "propose endpoints for the backend", "spec a DTO", "hand off a feature to backend", or whenever a frontend feature needs a written backend handoff that another agent or developer can implement against.
---

# Create Laravel Feature Guide

## Overview

Generate a single Markdown handoff document that lets a Laravel backend developer (and any agent picking up the work) implement the API needed by a frontend feature. The guide must align with the contracts and domain layout in `src/lib/api/` (see `AGENTS.md`).

## When to use

- A new frontend feature needs backend endpoints that do not yet exist.
- An existing endpoint must change shape, and the frontend wants to formally propose the new contract.
- The user is preparing a backend ticket, PR description, or cross-repo handoff.

## Inputs to gather

Ask only for what is missing; infer the rest from the conversation and codebase.

1. **Feature name and domain** (e.g. `tasks`, `applications`, `menu`). Used for folder placement under `src/lib/api/domains/<domain>/` and the suggested Laravel route prefix.
2. **User-facing goal**: 1–3 sentences describing what the user can do.
3. **Operations needed**: which reads (queries) and writes (commands). Keep CQRS separation.
4. **Auth/visibility**: public, authenticated, role-scoped.
5. **Known constraints**: pagination, filtering, sorting, file upload, rate limits, idempotency.

If the feature already has a Spec Kit folder (`specs/<feature>/`), read `spec.md` and `plan.md` first and reuse their wording.

## Workflow

1. Decide the output path. Default: `docs/backend-handoffs/<feature-slug>.md`. If `specs/<feature>/` exists, also offer `specs/<feature>/backend-guide.md`.
2. Inspect one existing domain under `src/lib/api/domains/` (e.g. `tasks/`) to mirror naming conventions (`contract.ts`, `client.ts`, `query-keys.ts`, `query-options.ts`).
3. Draft the guide using the template below.
4. Show the proposed endpoints, request bodies, and DTOs to the user for confirmation before writing. Iterate until accepted.
5. Write the file. Do not modify backend code (this repo is frontend-only) and do not invent backend internals (DB schema, services) — only describe what the contract must guarantee.

## Document template

```md
# Backend Feature Guide: <Feature Name>

> Audience: Laravel backend developer and any agent implementing the API.
> Source feature: <link to spec.md / PR / ticket if any>
> Frontend domain: `src/lib/api/domains/<domain>/`

## 1. Feature description

<2–5 sentences: what the user does, why it matters, where it appears in the UI.>

**Primary user flows**
- <flow 1>
- <flow 2>

**Out of scope**
- <explicit non-goals>

## 2. Auth & access

- Authentication: <none | session | token>
- Authorization: <roles / policies expected>
- Rate limiting / idempotency: <if relevant>

## 3. Endpoint proposal

Route prefix: `/<domain>` (under the existing API base).

| # | Method | Path | Purpose | Type |
|---|--------|------|---------|------|
| 1 | GET    | `/<domain>/list`        | List items for current user | query   |
| 2 | GET    | `/<domain>/{id}`        | Get single item             | query   |
| 3 | POST   | `/<domain>`             | Create item                 | command |
| 4 | PATCH  | `/<domain>/{id}`        | Update item                 | command |
| 5 | DELETE | `/<domain>/{id}`        | Delete item                 | command |

For each endpoint below, specify: purpose, auth, request, response, errors.

### 3.1 `GET /<domain>/list`

- **Purpose:** <…>
- **Query params:** `page?: number`, `pageSize?: number`, `sort?: 'field:asc'|'field:desc'`, `filter[<field>]?: string`
- **Request body:** none
- **Response 200 (DTO):**
  ```ts
  type <Feature>ListItem = {
    id: number;
    // mirror real fields the UI needs, in camelCase
  };
  type <Feature>ListResponse = {
    data: <Feature>ListItem[];
    meta: { page: number; pageSize: number; total: number };
  };
  ```
- **Errors:** `401` unauthenticated, `422` invalid filters.

### 3.2 `POST /<domain>`

- **Purpose:** <…>
- **Request body:**
  ```ts
  type Create<Feature>Body = {
    // required fields first, camelCase, validated server-side
  };
  ```
- **Response 201 (DTO):** `<Feature>` (full resource).
- **Errors:** `401`, `422` with `{ message, errors: Record<string, string[]> }`.

<Repeat for every endpoint.>

## 4. DTO conventions

- JSON keys: `camelCase` (the frontend consumes them directly; if Laravel emits `snake_case`, the frontend will need a mapper in `src/lib/api/mappers/`).
- Dates: ISO 8601 strings in UTC (`2026-05-21T10:00:00Z`).
- Money/decimals: strings, not floats, when precision matters.
- Enums: lowercase string unions, listed explicitly (e.g. `"low" | "normal" | "high"`).
- IDs: numeric unless the backend already uses ULIDs/UUIDs.
- Nullability: prefer `null` over omitting keys; document each nullable field.

## 5. Validation rules (Laravel-side)

List per endpoint the expected `FormRequest` rules in plain language so the backend dev can translate to Laravel validation:

- `title`: required, string, max 200
- `priority`: required, in: low,normal,high
- …

## 6. Error contract

All errors should follow:

```json
{
  "message": "Human-readable summary",
  "errors": { "field": ["reason"] }
}
```

Status codes used: `400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`.

## 7. Frontend integration notes (for the implementing agent)

- New files to create under `src/lib/api/domains/<domain>/`:
  - `contract.ts` — TypeScript types matching section 3 DTOs.
  - `client.ts` — thin `browserFetch` calls; throw on `!result.ok`.
  - `queries.ts` — TanStack Query options for reads.
  - `commands.ts` — mutation helpers for writes.
  - `query-keys.ts` — stable keys.
- Follow the patterns in `src/lib/api/domains/tasks/` as the reference.
- Pages/components must consume mapped models, not raw DTOs.

## 8. Open questions for backend

- <question 1>
- <question 2>

## 9. Changelog

- <date> — initial draft.
```

## Output rules

- Keep DTO blocks in **TypeScript** so both the frontend agent and backend dev can read them unambiguously.
- Use camelCase in DTOs unless the user explicitly says the Laravel API stays snake_case (then add a mapper note).
- Do not invent fields that were not discussed; mark unknowns as `// TODO: confirm with product`.
- Always include sections 1, 3, 4, 6, 7 — the others are optional only if truly N/A.
- After writing, print the file path and a 5-line summary of the proposed endpoints.

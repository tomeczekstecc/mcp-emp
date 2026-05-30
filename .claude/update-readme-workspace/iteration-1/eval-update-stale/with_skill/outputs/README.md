# CI-PRS Web

A Next.js web application for managing CI pull requests, built on a server-first API layer.

## Prerequisites

- Node.js 20+
- pnpm 9+
- PostgreSQL database
- A running backend API (defaults to `http://127.0.0.1:8000`)

## Getting Started

```bash
git clone <repo-url>
cd web
cp .env.example .env   # fill in required values
pnpm install
pnpm dev
```

The app will be available at `http://localhost:3000`.

## Environment Variables

Copy `.env.example` to `.env` and fill in the required values. Never commit real secrets.

| Variable | Required | Description |
|----------|----------|-------------|
| `API_URL` | Yes | Base URL for the backend API (e.g. `http://127.0.0.1:8000`) |
| `BETTER_AUTH_SECRET` | Yes | Secret key used by Better Auth to sign sessions |
| `BETTER_AUTH_URL` | Yes | Public URL of this app, used by Better Auth (e.g. `http://127.0.0.1:3000`) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `LARAVEL_INTERNAL_AUTH_TOKEN` | Yes | Internal token for Laravel backend auth |
| `LARAVEL_INTERNAL_AUTH_MAIL_TOKEN` | No | Internal token for mail-related backend calls |
| `LARAVEL_INTERNAL_AUTH_REVOKE_TOKEN` | No | Internal token for revoking backend auth |
| `AUTH_SIGNUP_ENABLED` | No | Set to `true` to enable self-service sign-up (default: `true`) |
| `AUTH_SSO_ENABLED` | No | Set to `true` to enable SSO login (default: `false`) |
| `AUTH_SUPPORT_LABEL` | No | Display label for the support link on auth pages |
| `AUTH_SUPPORT_URL` | No | URL for the support link on auth pages |
| `KEYCLOAK_CLIENT_ID` | No | Keycloak client ID (required when SSO is enabled) |
| `KEYCLOAK_CLIENT_SECRET` | No | Keycloak client secret (required when SSO is enabled) |
| `KEYCLOAK_ISSUER` | No | Keycloak issuer URL (required when SSO is enabled) |

## Available Scripts

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start the development server with hot reload |
| `pnpm build` | Compile and type-check a production build |
| `pnpm start` | Serve the production build locally |
| `pnpm lint` | Run ESLint across the project |

## Project Structure

```
src/
  app/            Next.js App Router pages, layouts, and route handlers
  components/     Shared UI components (shadcn/ui + custom)
  hooks/          Reusable React hooks
  lib/            Business logic, API clients, and utilities
    api/          Server-first API layer (see Architecture below)
context/          Project documentation for AI and human contributors
specs/            Spec Kit feature artifacts and implementation plans
```

For product goals, feature scope, coding standards, and collaboration expectations, see the `context/` folder:

- `context/project-overview.md` — product goals, users, and UX direction
- `context/project-spec.md` — feature scope, data model, and roadmap
- `context/coding-standards.md` — TypeScript, React, Next.js, and Tailwind rules
- `context/ai-interaction.md` — collaboration, testing, and commit expectations

## Architecture Overview

- **Server components by default.** Add `'use client'` only at interactive leaves or when browser-only APIs are needed.
- **Auth-facing pages** live under `src/app/auth/`.
- **Feature placement:** routes under `src/app/<domain>/`, UI under `src/components/<domain>/`, helpers under `src/lib/<domain>/` or `src/lib/api/domains/<domain>/`.
- **API layer follows CQRS:** reads in `queries.ts`, writes in `commands.ts`. See the full API pattern below.

## Tech Stack

| Technology | Version |
|------------|---------|
| Next.js | 16.2.2 |
| React | 19 |
| TypeScript | 5.8 |
| Tailwind CSS | 4.x |
| shadcn/ui | 4.x (base-nova style) |
| Better Auth | 1.3 |
| TanStack Table | 8.x |
| Zod | 4.x |
| PostgreSQL (via `pg`) | 8.x |

## API Integration Pattern

This project uses a server-first API layer in `src/lib/api` so page and component code stay small even when backend integration grows.

### Goals

- Keep transport details out of pages and components.
- Keep backend DTOs separate from frontend view models.
- Make each backend area grow inside its own domain folder.
- Allow the UI to handle backend failures consistently.

### Folder structure

```text
src/lib/api/
  core/
    config.ts
    http.ts
  contracts/
    common.ts
  domains/
    landing-page/
      contract.ts
      mapper.ts
      queries.ts
    applications/
      contract.ts
      mapper.ts
      commands.ts
```

### Responsibilities

- `src/lib/api/core/config.ts`
  Reads API configuration such as `API_URL` and builds absolute backend URLs.
- `src/lib/api/core/http.ts`
  Owns the shared `fetch` wrapper, JSON parsing, and normalized API error handling.
- `src/lib/api/contracts/common.ts`
  Defines common request, response, and error types used across domains.
- `src/lib/api/domains/<domain>/contract.ts`
  Defines the raw backend payloads and the frontend-friendly models for that domain.
- `src/lib/api/domains/<domain>/mapper.ts`
  Maps backend DTO fields like `primary_cta_label` into frontend fields like `primaryCtaLabel`.
- `src/lib/api/domains/<domain>/queries.ts`
  Contains read-side operations for that domain and decides how fallback behavior should work.
- `src/lib/api/domains/<domain>/commands.ts`
  Contains write-side operations for that domain such as create, update, submit, and delete flows.

### Request flow

1. A page imports a domain query, for example `getLandingPageContent` from `src/lib/api/domains/landing-page/queries.ts`.
2. The domain query calls the shared `apiRequest()` helper in `src/lib/api/core/http.ts`.
3. The HTTP layer builds the full backend URL from `API_URL`.
4. The backend response is parsed into a raw DTO.
5. The domain mapper converts the DTO into the model used by the UI.
6. The page renders only the mapped model and does not need to know transport details.

### CQRS rule of thumb

- `queries.ts` is the read side. Query functions should fetch data and return mapped read models without causing backend state changes.
- `commands.ts` is the write side. Command functions may create, update, submit, revoke, provision, or otherwise change backend state.
- Pages and server components should import domain queries for route data.
- Server actions, route handlers, and event-style flows should import domain commands for writes.
- Query and command functions should import the shared HTTP client directly instead of calling each other.
- Only mappers should translate backend field naming into frontend naming.
- New endpoints should be added inside a domain folder instead of wiring `fetch` directly in the page.

### TanStack Query v5 guidance

This project should keep the server-first API pattern as the default for route entry, auth-sensitive data, redirects, secure server-only calls, and initial shell data. TanStack Query v5 is the preferred client server-state layer once a domain grows into dynamic CRUD screens with tables, detail panes, filters, sorting, pagination, background refresh, optimistic updates, or multiple components reading the same backend entities.

Use this split:

- Server components and route entry code handle auth checks, initial shell data, redirects, secure server-only calls, and optional prefetch/dehydrate for important first-screen queries.
- TanStack Query handles CRUD tables, detail panes, filters, sorting, pagination, mutations, optimistic updates, invalidation after writes, and background synchronization.

Do not replace `src/lib/api` wholesale. Evolve each domain only when it needs browser-side server-state behavior:

```text
src/lib/api/domains/<domain>/
  contract.ts
  mapper.ts
  queries.ts        server-only reads, current pattern
  commands.ts       server-only writes, current pattern
  client.ts         browser-safe fetchers for TanStack Query
  query-keys.ts     stable TanStack Query key factory
  query-options.ts  reusable queryOptions/useQuery config
```

Keep `contract.ts` and `mapper.ts` as the shared boundary for backend DTOs and frontend models. Browser-safe `client.ts` functions should use public backend endpoints or Next.js route handlers; they must not import server-only helpers such as `src/lib/api/core/http.ts`.

### Example: adding a new endpoint

If you need a new `users` integration, add:

```text
src/lib/api/domains/users/
  contract.ts
  mapper.ts
  queries.ts
  commands.ts
```

Then:

- define the backend DTOs in `contract.ts`
- define the frontend model in `contract.ts`
- map DTO -> model in `mapper.ts`
- call `apiRequest()` in `queries.ts`
- call `apiRequest()` in `commands.ts` for writes
- import the query from the page or server component

### Example: command

For write flows, add a `commands.ts` file to the domain. A typical command keeps the request DTO, response DTO, and mapped frontend model inside the same domain boundary.

This repo now includes a concrete example in `src/lib/api/domains/applications/`.

CQRS rule of thumb:

- `queries.ts` is for reads.
- `commands.ts` is for writes.
- Both should call `apiRequest()`.
- Queries should not call commands, and commands should not call queries.
- Only the domain layer should know raw backend field names.
- Components should consume mapped frontend models, not DTOs.

### Transitional compatibility

Legacy flat files such as `src/lib/api/client.ts` and `src/lib/api/contracts.ts` currently re-export the new modules. That keeps the refactor incremental while new code moves to the domain-folder pattern.

## Deployment

CI deploys the `main` branch automatically. Check the CI configuration at `.github/workflows/` for pipeline details.

# CI-PRS Web

A Next.js web frontend for managing CI pull requests, built with a server-first API layer and domain-driven structure.

## Prerequisites

- Node.js 20+
- pnpm (recommended over npm/yarn)
- PostgreSQL database
- Backend API service running (defaults to `http://127.0.0.1:8000`)
- Optional: Keycloak instance if SSO is enabled

## Getting Started

```bash
git clone <repo-url>
cd web
cp .env.example .env   # fill in required values — see Environment Variables below
pnpm install
pnpm dev
```

The dev server starts at `http://localhost:3600`.

## Environment Variables

Copy `.env.example` to `.env` and fill in the required values. Never commit real secrets.

| Variable | Required | Description |
|----------|----------|-------------|
| `API_URL` | Yes | Base URL for the backend API (e.g. `http://127.0.0.1:8000`) |
| `BETTER_AUTH_SECRET` | Yes | Secret key used by better-auth to sign sessions |
| `BETTER_AUTH_URL` | Yes | Public URL of this Next.js app, used by better-auth for callbacks |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `LARAVEL_INTERNAL_AUTH_TOKEN` | Yes | Internal token for Laravel API auth |
| `LARAVEL_INTERNAL_AUTH_MAIL_TOKEN` | Yes | Internal token for Laravel mail flows |
| `LARAVEL_INTERNAL_AUTH_REVOKE_TOKEN` | Yes | Internal token for Laravel revoke flows |
| `AUTH_SIGNUP_ENABLED` | No | Enable/disable self-service sign-up (`true` or `false`, default `true`) |
| `AUTH_SSO_ENABLED` | No | Enable/disable SSO login (`true` or `false`, default `false`) |
| `AUTH_SUPPORT_LABEL` | No | Display label for the support link shown on auth pages |
| `AUTH_SUPPORT_URL` | No | URL for the support link shown on auth pages |
| `KEYCLOAK_CLIENT_ID` | SSO only | Keycloak OAuth client ID |
| `KEYCLOAK_CLIENT_SECRET` | SSO only | Keycloak OAuth client secret |
| `KEYCLOAK_ISSUER` | SSO only | Keycloak issuer URL (e.g. `https://keycloak.example.com/realms/myrealm`) |

## Available Scripts

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start the Next.js development server with hot reload |
| `pnpm build` | Compile a production build with type-checking |
| `pnpm start` | Serve the production build locally |
| `pnpm lint` | Run ESLint across the entire project |

## Project Structure

```
src/
  app/            Next.js App Router pages and layouts
  components/     Shared and domain UI components
  hooks/          Custom React hooks
  lib/
    api/
      core/       Shared fetch wrapper and API config
      contracts/  Common request/response types
      domains/    One folder per backend domain (contract, mapper, queries, commands)
context/          Project documentation for AI and human contributors
specs/            Spec Kit feature specs and implementation plans
```

## Architecture Overview

**Server components by default.** Add `'use client'` only at interactive leaves or for browser-only APIs.

**Server-first API layer.** All backend calls go through `src/lib/api/`. Pages import domain query functions and receive mapped frontend models — they never call `fetch` directly or consume raw backend DTOs.

**CQRS in API domains.** Each domain under `src/lib/api/domains/<domain>/` keeps reads in `queries.ts` and writes in `commands.ts`. Both call the shared `apiRequest()` helper in `src/lib/api/core/http.ts`. Only the domain mapper (`mapper.ts`) translates backend snake_case field names into frontend camelCase models.

**TanStack Query for dynamic CRUD.** For screens with tables, filters, pagination, optimistic updates, or background sync, add `client.ts`, `query-keys.ts`, and `query-options.ts` to the domain folder.

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 16.2.2 |
| Runtime | React | 19.x |
| Styling | Tailwind CSS | 4.x |
| UI components | shadcn/ui (`base-nova` style) | 4.x |
| Auth | better-auth | 1.x |
| Database client | pg (PostgreSQL) | 8.x |
| Tables | TanStack React Table | 8.x |
| Charts | Recharts | 3.x |
| Drag and drop | dnd-kit | 6.x |
| Validation | Zod | 4.x |
| Language | TypeScript | 5.x |

## Contributing

**Branches.** Use feature branches off `master`. Follow `<type>/<short-description>` (e.g. `feat/add-auth-sso`).

**Commits.** Use Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `style:`, `perf:`.

**PRs.** Open against `master`. Run `pnpm lint` and `pnpm build` locally before requesting review.

**New API integrations.** Add a domain folder under `src/lib/api/domains/<domain>/` with `contract.ts`, `mapper.ts`, `queries.ts`, and `commands.ts`. Do not wire `fetch` directly in pages.

See `context/coding-standards.md` and `context/ai-interaction.md` for more detail.

## Deployment

CI deploys to production automatically on merge to `master`.

---

## Further Reading

- `context/project-overview.md` — product goals, target users, and UX direction
- `context/project-spec.md` — feature scope, data model, and roadmap
- `context/coding-standards.md` — TypeScript, React, Next.js, and Tailwind conventions
- `context/ai-interaction.md` — collaboration, testing, and commit expectations
- `specs/001-app-auth/plan.md` — current active implementation plan

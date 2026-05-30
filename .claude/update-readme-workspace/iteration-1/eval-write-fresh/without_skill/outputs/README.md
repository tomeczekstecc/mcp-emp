# CI-PRS Web

A server-first Next.js frontend for the CI-PRS Web Platform. It provides a public-facing landing page and an internal dashboard UI, built to connect to a backend API without requiring rewrites to the page layer.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Development](#development)
- [API Integration Pattern](#api-integration-pattern)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript 5 |
| UI Library | React 19 |
| Styling | Tailwind CSS v4 |
| Components | shadcn/ui (`base-nova` style) |
| Icons | lucide-react |
| Theming | next-themes |
| Tables | TanStack Table v8 |
| Charts | Recharts |
| Validation | Zod |
| Forms | TanStack Form |
| Auth | better-auth |
| Database client | pg (PostgreSQL) |
| Drag and drop | dnd-kit |

---

## Prerequisites

- **Node.js** 20 or later
- **pnpm** 9 or later (`npm install -g pnpm`)
- A running backend API (see `API_URL` in [Environment Variables](#environment-variables))
- A PostgreSQL database (see `DATABASE_URL`)

---

## Getting Started

1. **Clone the repository.**

   ```bash
   git clone <repo-url>
   cd ci-prs/web
   ```

2. **Install dependencies.**

   ```bash
   pnpm install
   ```

3. **Set up environment variables.**

   Copy the example file and fill in the required values:

   ```bash
   cp .env.example .env.local
   ```

   See the [Environment Variables](#environment-variables) section for a description of each variable.

4. **Start the development server.**

   ```bash
   pnpm dev
   ```

   The app is available at [http://localhost:3600](http://localhost:6000).

---

## Environment Variables

Copy `.env.example` to `.env.local` and populate the values before running the app.

| Variable | Required | Description |
|---|---|---|
| `API_URL` | Yes | Base URL of the backend API. Defaults to `http://127.0.0.1:8000` for local development. |
| `BETTER_AUTH_SECRET` | Yes | Secret key used by better-auth to sign sessions. Use a long random string in production. |
| `BETTER_AUTH_URL` | Yes | Public URL of this Next.js app. Used by better-auth for redirects. |
| `DATABASE_URL` | Yes | PostgreSQL connection string used by the auth layer. |
| `LARAVEL_INTERNAL_AUTH_TOKEN` | Yes | Shared secret for internal server-to-server calls to the Laravel backend. |
| `LARAVEL_INTERNAL_AUTH_MAIL_TOKEN` | Situational | Shared secret for mail-related internal calls. |
| `LARAVEL_INTERNAL_AUTH_REVOKE_TOKEN` | Situational | Shared secret for token revocation calls. |
| `AUTH_SIGNUP_ENABLED` | No | Set to `true` to allow new sign-ups. Defaults to `true`. |
| `AUTH_SSO_ENABLED` | No | Set to `true` to enable SSO via Keycloak. Defaults to `false`. |
| `AUTH_SUPPORT_LABEL` | No | Label text shown on the auth support link. |
| `AUTH_SUPPORT_URL` | No | URL for the auth support link. |
| `KEYCLOAK_CLIENT_ID` | If SSO | Keycloak client ID. Required when `AUTH_SSO_ENABLED=true`. |
| `KEYCLOAK_CLIENT_SECRET` | If SSO | Keycloak client secret. Required when `AUTH_SSO_ENABLED=true`. |
| `KEYCLOAK_ISSUER` | If SSO | Keycloak issuer URL. Required when `AUTH_SSO_ENABLED=true`. |

---

## Project Structure

```text
src/
  app/                      # Next.js App Router routes
    auth/                   # Authentication routes (sign-in, sign-up, etc.)
    dashboard/              # Internal dashboard route
    page.tsx                # Public landing page
    layout.tsx              # Root layout
    globals.css             # Global styles and Tailwind CSS v4 theme
  components/               # Shared React components
    ui/                     # shadcn/ui primitives
    auth/                   # Auth-specific UI
  hooks/                    # Reusable client-side hooks
  lib/
    api/
      core/
        config.ts           # Reads API_URL and builds backend URLs
        http.ts             # Shared fetch wrapper and error handling
      contracts/
        common.ts           # Shared request/response/error types
      domains/              # One folder per backend domain
        <domain>/
          contract.ts       # Raw backend DTOs + frontend models
          mapper.ts         # DTO -> frontend model conversion
          queries.ts        # Read operations (CQRS read side)
          commands.ts       # Write operations (CQRS write side)
    auth.ts                 # better-auth server configuration
    auth-client.ts          # better-auth browser client
    utils.ts                # General utilities
context/                    # Project documentation for AI and humans
specs/                      # Spec Kit feature artifacts
docs/                       # Backend integration notes
```

---

## Development

### Scripts

| Script | Description |
|---|---|
| `pnpm dev` | Start the development server with hot reload |
| `pnpm build` | Build the production bundle |
| `pnpm start` | Start the production server (run `build` first) |
| `pnpm lint` | Lint the codebase with ESLint |

### Component Library

This project uses **shadcn/ui** with the `base-nova` style. To add a new component:

```bash
pnpm dlx shadcn@latest add <component-name>
```

Components are installed into `src/components/ui/`.

### Server vs. Client Components

- Components are server components by default. Do not add `'use client'` unless the component uses hooks, browser APIs, or interactive state.
- When a component needs client behavior, extract only the interactive leaf into a separate `'use client'` file and keep the shell as a server component.

### Adding a New Domain

1. Create a folder under `src/lib/api/domains/<domain>/`.
2. Add `contract.ts` with the backend DTO types and the frontend model types.
3. Add `mapper.ts` to convert DTO fields to camelCase frontend fields.
4. Add `queries.ts` for read operations that call `apiRequest()` from `src/lib/api/core/http.ts`.
5. Add `commands.ts` for write operations (create, update, delete) that call `apiRequest()`.
6. Import queries in server components or page files; import commands in server actions or route handlers.

For domains that need browser-side state management (CRUD tables, pagination, background refresh), also add:

- `client.ts` — browser-safe fetchers (no server-only imports)
- `query-keys.ts` — stable TanStack Query key factories
- `query-options.ts` — reusable `queryOptions` / `useQuery` config

---

## API Integration Pattern

This project uses a server-first API layer so pages and components stay simple even as backend integration grows.

### Request Flow

1. A page imports a domain query from `src/lib/api/domains/<domain>/queries.ts`.
2. The query calls `apiRequest()` in `src/lib/api/core/http.ts`.
3. The HTTP layer builds the full URL from `API_URL` and handles fetch, JSON parsing, and errors.
4. The response is typed as a raw DTO.
5. The domain mapper converts the DTO into the frontend model.
6. The page renders the mapped model without knowing any transport details.

### CQRS Rule of Thumb

- `queries.ts` is the read side. Query functions fetch data and return mapped models. They must not cause backend state changes.
- `commands.ts` is the write side. Command functions create, update, submit, revoke, provision, or delete.
- Queries must not call commands; commands must not call queries.
- Only mappers translate raw backend field names into frontend field names.
- Pages and components must consume mapped frontend models, not raw DTOs.

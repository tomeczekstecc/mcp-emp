# CI-PRS Web

## Prerequisites

- Node.js 20 or later
- pnpm (install via `npm install -g pnpm` if not already available)
- A running instance of the backend API (default: `http://127.0.0.1:8000`)
- PostgreSQL database accessible via connection string

## Getting started

### 1. Install dependencies

```bash
pnpm install
```

### 2. Configure environment variables

Copy the example environment file and fill in the required values:

```bash
cp .env.example .env.local
```

Open `.env.local` and set the following:

| Variable | Required | Description |
|---|---|---|
| `API_URL` | Yes | URL of the backend API (default: `http://127.0.0.1:8000`) |
| `BETTER_AUTH_SECRET` | Yes | Random secret string for session signing (generate with `openssl rand -hex 32`) |
| `BETTER_AUTH_URL` | Yes | Public URL of this Next.js app (default: `http://127.0.0.1:3000`) |
| `DATABASE_URL` | Yes | PostgreSQL connection string (e.g. `postgresql://user:pass@localhost:5432/dbname`) |
| `LARAVEL_INTERNAL_AUTH_TOKEN` | Yes | Internal token for backend auth calls |
| `LARAVEL_INTERNAL_AUTH_MAIL_TOKEN` | Yes | Internal token for backend mail auth calls |
| `LARAVEL_INTERNAL_AUTH_REVOKE_TOKEN` | Yes | Internal token for backend revoke auth calls |
| `AUTH_SIGNUP_ENABLED` | No | Enable or disable user self-registration (default: `true`) |
| `AUTH_SSO_ENABLED` | No | Enable SSO login (default: `false`) |
| `AUTH_SUPPORT_LABEL` | No | Label shown on the support link on auth pages |
| `AUTH_SUPPORT_URL` | No | URL for the support link on auth pages |
| `KEYCLOAK_CLIENT_ID` | No | Keycloak client ID (required when `AUTH_SSO_ENABLED=true`) |
| `KEYCLOAK_CLIENT_SECRET` | No | Keycloak client secret (required when `AUTH_SSO_ENABLED=true`) |
| `KEYCLOAK_ISSUER` | No | Keycloak issuer URL (required when `AUTH_SSO_ENABLED=true`) |

### 3. Run the development server

```bash
pnpm dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

## Available scripts

| Script | Description |
|---|---|
| `pnpm dev` | Start the Next.js development server with hot reload |
| `pnpm build` | Build the app for production |
| `pnpm start` | Start the production server (requires `pnpm build` first) |
| `pnpm lint` | Run ESLint across the project |

## Project structure

```text
src/
  app/           Next.js App Router routes (domain folders under src/app/<domain>/)
  components/    Shared and domain UI components (src/components/<domain>/)
  hooks/         Shared React hooks
  lib/
    api/         Server-first API layer (see API integration pattern below)
```

## Tech stack

- **Next.js 16** App Router with React 19 and server components by default
- **TypeScript 5** with strict mode
- **Tailwind CSS v4** for styling
- **shadcn/ui** (`base-nova` style) for UI primitives
- **better-auth** for authentication
- **TanStack Table v8** and **TanStack Query v5** for data-heavy screens
- **Zod v4** for schema validation
- **PostgreSQL** via `pg`

---

## API integration pattern

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

Define stable query keys per domain from the first CRUD screen:

```ts
export const applicationsKeys = {
  all: ["applications"] as const,
  lists: () => [...applicationsKeys.all, "list"] as const,
  list: (filters: ApplicationFilters) =>
    [...applicationsKeys.lists(), filters] as const,
  detail: (id: string) => [...applicationsKeys.all, "detail", id] as const,
};
```

After mutations, invalidate the smallest related surfaces that must reflect the write:

```ts
const queryClient = useQueryClient();

useMutation({
  mutationFn: updateApplication,
  onSuccess: async (_, variables) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: applicationsKeys.lists() }),
      queryClient.invalidateQueries({
        queryKey: applicationsKeys.detail(variables.id),
      }),
    ]);
  },
});
```

Add the TanStack Query provider and hydration setup when the first real CRUD domain needs it. Avoid adding global Query usage for static landing content, route-level auth gates, or simple one-shot server-rendered data.

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

If the endpoint belongs to an interactive CRUD surface, also add:

```text
src/lib/api/domains/users/
  client.ts
  query-keys.ts
  query-options.ts
```

Then:

- keep browser-safe fetchers in `client.ts`
- keep stable query key factories in `query-keys.ts`
- keep reusable TanStack Query options in `query-options.ts`
- invalidate list and detail keys after successful writes

### Example: command

For write flows, add a `commands.ts` file to the domain. A typical command keeps the request DTO, response DTO, and mapped frontend model inside the same domain boundary.

This repo now includes a concrete example in `src/lib/api/domains/applications/`.

```ts
// src/lib/api/domains/applications/commands.ts
import "server-only";

import { apiRequest } from "@/lib/api/core/http";
import type { ApiResult } from "@/lib/api/contracts/common";
import { mapApplication } from "@/lib/api/domains/applications/mapper";
import type {
  Application,
  ApplicationPayload,
  CreateApplicationInput,
} from "@/lib/api/domains/applications/contract";

export async function createApplication(
  input: CreateApplicationInput,
): Promise<ApiResult<Application>> {
  const result = await apiRequest<ApplicationPayload, CreateApplicationInput>({
    path: "/api/applications",
    method: "POST",
    body: input,
  });

  if (!result.ok) {
    return result;
  }

  return {
    ok: true,
    status: result.status,
    data: mapApplication(result.data),
  };
}
```

Example contract shape:

```ts
// src/lib/api/domains/applications/contract.ts
export type CreateApplicationInput = {
  firstName: string;
  lastName: string;
  email: string;
};

export type ApplicationPayload = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  status: "draft" | "submitted";
};

export type Application = {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  status: "draft" | "submitted";
};
```

Example mapper:

```ts
// src/lib/api/domains/applications/mapper.ts
import type {
  Application,
  ApplicationPayload,
} from "@/lib/api/domains/applications/contract";

export function mapApplication(payload: ApplicationPayload): Application {
  return {
    id: payload.id,
    firstName: payload.first_name,
    lastName: payload.last_name,
    email: payload.email,
    status: payload.status,
  };
}
```

CQRS rule of thumb:

- `queries.ts` is for reads.
- `commands.ts` is for writes.
- Both should call `apiRequest()`.
- Queries should not call commands, and commands should not call queries.
- Only the domain layer should know raw backend field names.
- Components should consume mapped frontend models, not DTOs.

### Transitional compatibility

Legacy flat files such as `src/lib/api/client.ts` and `src/lib/api/contracts.ts` currently re-export the new modules. That keeps the refactor incremental while new code moves to the domain-folder pattern.

---
name: update-readme
description: Use when creating or updating a README.md file, when the user asks what a README should contain, wants to document their project, needs to onboard new developers, or asks to review or improve existing README content. Trigger proactively when a project is newly set up and has no README, or when the user says "add docs", "document this", "write a README", or "update the README". Even vague requests like "help new devs get started" or "describe the project" should trigger this skill.
---

# Update README

A README is often the first thing a developer reads about a project. The goal is to let a new contributor be running locally in under 5 minutes with zero tribal knowledge.

## Workflow

1. Read the existing `README.md` if one exists — preserve accurate sections, update what is stale.
2. Read `package.json` (or equivalent) to get the actual script names and key dependencies with versions.
3. Check for `.env.example` to populate the environment variables table accurately.
4. Inspect the top-level project structure to describe directories from what actually exists, not from memory.
5. Check for a `context/` or `docs/` folder — link to those instead of duplicating their content inline.
6. Write or update the README, then re-read it as if you have never seen this project before. Ask: can a new developer follow this without asking anyone a question?

## Sections (in order)

### 1. Project Name + One-liner
One sentence: what the project is and what problem it solves. No jargon, no marketing language.

### 2. Prerequisites
What must be installed before starting:
- Runtime with version (e.g. Node 20+, Python 3.11+)
- Package manager (pnpm, yarn, pip — include version if it matters)
- External services or accounts required (database, cloud credentials)

### 3. Getting Started
Step-by-step from clone to running locally. Every command must be copy-paste runnable — test them.

```bash
git clone <repo-url>
cd <project>
cp .env.example .env   # fill in required values
pnpm install
pnpm dev
```

### 4. Environment Variables
List every variable with a one-line description. Point to `.env.example` as the source of truth. Never include real values.

| Variable | Description |
|----------|-------------|
| `API_URL` | Base URL for the backend API |
| `DATABASE_URL` | PostgreSQL connection string |

### 5. Available Scripts
Each script with a plain-language description of what it does — not just the name.

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start development server |
| `pnpm build` | Production build with type-checking |
| `pnpm lint` | Run ESLint across the project |

### 6. Project Structure
Top-level directories with one line each. Skip obvious ones (`node_modules`, `.git`, `.next`).

```
src/
  app/          Next.js App Router pages and layouts
  components/   Shared UI components
  lib/          Business logic, API clients, utilities
context/        Project documentation for AI and human contributors
```

### 7. Architecture Overview
Key patterns a contributor must know before touching code. Include this section only when the architecture has non-obvious conventions. Examples:

- "Server components by default; add `'use client'` only at interactive leaves"
- "API layer follows CQRS: reads in `queries.ts`, writes in `commands.ts`"
- "All external API calls route through `src/lib/api/core/http.ts`"

### 8. Tech Stack
Major dependencies with versions — framework, runtime, auth, database, UI library, and hosting/infra. Versions matter; omit them only for obvious transitive deps.

### 9. Contributing *(for team or open-source projects)*
- Branch naming convention
- Commit message format (e.g. Conventional Commits)
- PR process and review expectations
- Whether tests are required to merge

### 10. Deployment
How to ship to production. Even a one-liner ("CI deploys `main` to Vercel automatically") is enough. Point to CI config if it exists.

## Principles

**Lean over comprehensive.** If the project has a `context/` folder or dedicated docs, link there instead of duplicating. A short, accurate README beats a long, stale one.

**Commands must work.** Run every command in Getting Started from a clean state before publishing. Broken commands destroy trust faster than missing sections.

**Versions matter.** "Use Node" is unhelpful. "Use Node 20+" is actionable. Pull version requirements from `package.json` engines, `.nvmrc`, or similar sources of truth.

**Keep it current.** When a PR changes setup steps, scripts, or env vars, update the README in the same PR.

**Link, don't duplicate.** If architectural detail lives in `context/` or an ADR, reference it with a path. Don't copy it into the README where it will silently fall out of sync.

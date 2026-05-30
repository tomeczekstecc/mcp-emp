---
name: design-patterns-search
description: Scans the codebase for recurring design patterns that are not yet documented in context/ and proposes them to the user for registration. Use when the user asks to find undocumented patterns, wants to grow the context folder, or says "look for patterns", "find patterns", "what patterns are missing", or "scan for undocumented patterns".
---

# Design Patterns Search

Use this skill to discover recurring conventions and architectural patterns in the codebase that are not yet captured in `context/`.

## Goal

Find patterns that appear in two or more real places, are non-obvious to a new contributor, and would benefit from explicit documentation. Surface them as candidates and let the user decide what to register.

## Workflow

### 1. Read existing context docs

List the current `context/` contents dynamically — do not rely on a hardcoded list, it goes stale:

```bash
ls context/*.md
```

Read every pattern file to know what is already documented. Do not re-propose patterns already covered.

Skip these files when looking for patterns (they are not patterns):

- `project-overview.md`, `project-spec.md` — product/feature scope
- `TODO.md` — backlog
- `coding-standards.md` — baseline rules
- `ai-interaction.md` — agent collaboration notes

### 2. Scan the codebase

Look for patterns across these dimensions:

**Component conventions**
- Naming conventions (file names, component names, prop names)
- Recurring composition shapes (Provider + Consumer, Shell + Pages, etc.)
- Shared layout or wrapper components used across routes

**Hook patterns**
- Hooks that follow the same structure across domains
- Custom hook return shapes (`{ data, isLoading, isError }` vs others)
- Where hooks live relative to the components that use them

**API layer**
- Consistency of `queries.ts` / `commands.ts` / `client.ts` / `mapper.ts` / `contract.ts` split
- How domains expose data to components (direct fetch vs TanStack Query options)
- Server-only vs browser-safe module separation

**State management**
- Zustand slice conventions (if Zustand is used)
- Where global vs local state lives
- How state is initialized, reset, and scoped

**Error and loading handling**
- How loading states are rendered across different component types
- How errors from API calls surface in the UI
- Consistent use of Alert, Skeleton, or other primitives

**Form conventions**
- How forms are structured (TanStack Form + Zod or other)
- Where schemas are defined relative to the form component
- How field-level errors are displayed

**Navigation and routing**
- How redirects and auth guards work
- URL parameter handling conventions
- How `returnTo` or similar patterns are used

**Domain-specific systems**
- Any system that spans multiple files with a clear internal protocol
  (e.g. wizard, menu system, auth redirects, MSW mocks)

### 3. Identify candidates

A pattern is a candidate for registration when:
- It appears in **two or more** real places in the codebase
- It is **non-obvious** — a new contributor would not guess it from the file names alone
- It has **enough rules or conventions** to be worth writing down (at least 3-5 decisions)
- It is **not already covered** (even partially) in an existing context file

Skip:
- One-off implementation details
- Patterns fully explained by the library's own docs (e.g. basic TanStack Query `useQuery`)
- Things that are obvious from the file structure alone

### 4. Present candidates

For each candidate, present:

```
## [Pattern Name]

**Where it appears:** list 2-3 file paths
**What it is:** one-sentence description of the pattern
**Why it's non-obvious:** what a new contributor would get wrong without docs
**Proposed context file:** `context/<slug>.md` or section in existing file
```

After listing all candidates, ask:
> Which of these do you want to register? (name them, say "all", or "skip" any)

### 5. Write documentation

For each approved candidate, write a new `context/<slug>.md` (or extend an existing file if the pattern is a subsection of something already there).

Documentation must include:
- **Overview** — what the pattern is and when to use it
- **File map** — where the relevant files live
- **Usage example** — minimal concrete code showing the pattern in action
- **Key rules** — 3-10 bullet points a contributor must follow
- **Anti-patterns** — at least one "don't do this" example if applicable

Keep documentation grounded in the actual codebase — use real file paths, real type names, and real API shapes. Do not invent generic examples.

### 6. Register matching skill

Every registered pattern must have a corresponding skill. Without it, `pattern-skill-sync-check` will flag the pattern as missing coverage.

For each approved pattern:

1. Create `.agents/skills/<slug>-check/SKILL.md` with front-matter (`name`, `description`) and a body that:
   - Opens with `**Pattern source:** \`context/<slug>.md\`` as the first non-heading line — the literal path is required so the meta-skill grep finds it.
   - Has `## Overview`, `## Workflow`, `## Rules`, `## Validation` sections aligned with the pattern doc.
2. Mirror the file to `.claude/skills/<slug>-check/SKILL.md` (byte-identical).
3. Run `pattern-skill-sync-check` to confirm the new pattern is covered and both skill copies are in sync.

Naming: `<pattern-slug>-check` matching the pattern file slug (e.g. `context/foo-pattern.md` → `.agents/skills/foo-pattern-check/`).

### 7. Commit (optional)

If the user wants to commit after registration, use the `git-add-push` skill.

## Rules

- Never register a pattern without user approval.
- Always read existing context files first — never duplicate what is already documented.
- Prefer adding to an existing context file over creating a new one when the pattern is a small extension of documented behaviour.
- A pattern found in only one place is a candidate only if it is clearly intended to be reused (e.g. it is exported as a public API or referenced in multiple routes).
- Keep proposed file names lowercase, hyphenated, and under 40 characters.
- When in doubt about whether a pattern deserves its own file, propose it as a section in the most relevant existing file and let the user decide.
- Registering a pattern in `context/` without a matching `<slug>-check` skill is incomplete — always finish step 6 and verify with `pattern-skill-sync-check`.
- When extending an existing context file instead of creating a new one, update the corresponding existing skill (do not create a duplicate skill).

---
name: wizard-pattern-check
description: Use when adding, modifying, or reviewing a wizard (multi-step form) feature in this repository, including new wizard pages, field components, validation schemas, summary handling, or backend mapping/data/save endpoints. Ensures the Wizard/WizardProvider/WizardShell composition and hook layering are respected.
---

# Wizard Pattern Check

**Pattern source:** `context/wizard-pattern.md` — read it before applying this skill. It describes the architecture, file map, and validation flow end-to-end.

## Overview

The Wizard is a backend-driven, multi-page form framework:

- Field metadata (labels, types, constraints) comes from the backend via `mappingUrl`.
- Form state is shared via Zustand + React Context.
- Each page can declare a Zod schema for local validation before navigation.
- A summary page triggers server-side validation before final submission.

Composition:

```
<Wizard>
  <WizardProvider>
    <WizardContext.Provider>
      <WizardShell>
        pages[page].form
```

## Workflow

1. Open `context/wizard-pattern.md` and confirm the current file map and hook contracts.
2. Place wizard UI under `src/components/wizard/` (shell + inputs) and hooks under `src/hooks/wizard/`.
3. New field components go into `src/components/wizard/inputs/` and consume `useWizardField`.
4. New pages register in the `pages` map with `{ form, schema? }`. Use the page's Zod schema for local validation gating "Next".
5. For data flow, use the standard hooks: `useWizardMapping` (GET mapping, `staleTime: Infinity`), `useWizardData` (GET data, `staleTime: Infinity`), `useWizardSave` (PUT save).
6. Cross-check `context/zustand-store.md` when touching the wizard slice and `context/api-mutation-pattern.md` for the save mutation.

## Rules

- Page components must call `useWizard()` — never read context directly.
- `useWizard()` throws outside `<WizardProvider>`; do not catch and swallow.
- Field components never own form state — they read/write through `useWizardField`.
- Backend metadata is the source of truth for labels, types, options; never hardcode them in pages.
- Summary errors/warnings drive the disabled state of the final submit; do not bypass them.

## Validation

- Navigate through all pages with valid input → summary → submit; confirm server validation surfaces in the summary.
- Force a save error and confirm the mutation rollback / toast path works.
- `pnpm lint` and `pnpm build` succeed.

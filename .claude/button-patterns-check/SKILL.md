---
name: button-patterns-check
description: Use when adding, changing, or reviewing a `<Button>` in this repository — picking a variant, sizing a button, building an icon-only toolbar action, wiring a loading state, or composing multiple buttons in a dialog/form/toolbar surface. Ensures variant=intent (not color), one primary forward action per surface, and the icon-only + tooltip + aria-label pattern.
---

# Button Patterns Check

**Pattern source:** `context/button-patterns.md` — read it before applying this skill. It is the single source of truth for variant choice, sizing, icon-only buttons, and multi-button surface composition.

## Overview

The project ships only these variants: `default` · `outline` · `secondary` · `ghost` · `destructive` · `link`. **There is no `success` / `warning` / `info` variant.** Variant = intent, not color.

Heuristic for any surface (dialog, form, card footer, toolbar) — one decision tree, one path forward:

- One **primary forward** action → `default`
- "Cancel / back / leave as is" → `outline`
- "Discard / delete / wycofaj" → `destructive`
- Anything else → `ghost`

## Workflow

1. Open `context/button-patterns.md` and confirm the intent→variant table and the multi-button heuristic.
2. For each new button, name the intent first ("primary forward", "destructive", "secondary cancel", "tertiary toolbar action"), then map it to a variant — do not start from the desired color.
3. For icon-only buttons: wrap in `<Tooltip>`, set `aria-label`, use the size pairing table (`size="default"` neighbours → `size="icon"`, etc.), resolve the icon via `resolveIcon` (see `context/icon-system.md`).
4. For destructive flows: trigger is `ghost`/`outline`, the **confirm dialog button** is `destructive`. Cross-check `context/destructive-actions.md`.
5. For loading: pass `disabled={isPending}` and swap the label for a spinner + pending text.

## Rules

- Exactly **one** `default` (primary forward) button per surface.
- `destructive` only when the action is irreversible — never for cancel/styling.
- No hard-coded `bg-red-*` / `bg-green-*` to fake a missing variant. Add a real CSS-variable-driven variant instead, and only with explicit approval.
- Icon-only buttons must have both `aria-label` and a `<Tooltip>` (sighted users need a visible label too).
- Trigger of a destructive flow is **not** `destructive` if the confirm dialog already is — avoid double-red.
- Do not introduce two primary buttons competing for attention on the same surface.

## Validation

- Run the "Checklist before merging a surface with multiple buttons" from `context/button-patterns.md` against the changed file.
- `pnpm lint` and `pnpm build` succeed.
- Manually tab through the surface and confirm focus order leads to the primary forward action last.

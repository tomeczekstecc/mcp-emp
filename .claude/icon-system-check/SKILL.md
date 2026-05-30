---
name: icon-system-check
description: Use when adding, replacing, or reviewing an icon in this repository's UI — including dynamic icon names from backend data, icon pickers, icon-only buttons, or any new `lucide-react` icon introduction. Ensures all icons go through the central `resolveIcon` registry, follow the sizing convention, and stay accessible.
---

# Icon System Check

**Pattern source:** `context/icon-system.md` — read it before applying this skill. It is the single source of truth for the `resolveIcon` registry, naming, sizing, and a11y rules.

## Overview

All icon usage in the app must go through the central registry at `src/lib/icons.ts` via `resolveIcon()`. Direct `import { X } from "lucide-react"` in components is forbidden. The registry accepts kebab-case, snake_case, and PascalCase names, falls back to `Circle` for unknown values, and provides TypeScript autocomplete.

## Workflow

1. Open `context/icon-system.md` and confirm the current registry API (`resolveIcon`, `getIconNames`, `isIconName`).
2. For a new static icon, check if it already exists in `src/lib/icons.ts`. If not, import it from `lucide-react` and add it to `iconRegistry` under the right category.
3. Resolve the icon **once at module scope**, not inside the render body: `const ArrowRight = resolveIcon("ArrowRight")`.
4. For dynamic icon names (from backend / config), call `resolveIcon(name)` inside the component — the fallback is safe.
5. Apply the sizing convention from the table: inline text & button → `h-4 w-4`, nav → `h-4 w-4` / `h-5 w-5`, empty state → `h-12 w-12`, hero → `h-16 w-16+`.
6. For a11y: decorative icons get `aria-hidden="true"`; icon-only buttons get `aria-label` on the button (cross-check `context/button-patterns.md`).

## Rules

- Never `import { X } from "lucide-react"` directly in a component file (only allowed in `src/lib/icons.ts`).
- Never `import * as Icons from "lucide-react"` and key into it dynamically — bypasses the fallback and bloats the bundle.
- Resolve at module scope for hardcoded names; resolve in render only for dynamic strings.
- Status icons that convey meaning need an accompanying text label (sr-only is fine).
- Adding a new registry entry requires importing it in `src/lib/icons.ts` — do not add it elsewhere.

## Validation

- `grep -rn "from \"lucide-react\"" src/` returns only `src/lib/icons.ts`.
- `pnpm lint` and `pnpm build` succeed.
- Unknown icon names render the `Circle` fallback at runtime without errors.

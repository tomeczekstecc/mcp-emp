---
name: aria-check
description: Use when the user asks for an ARIA or screen-reader review, or when a component has dialogs, menus, tabs, forms, custom controls, focus behavior, or semantic accessibility risk. Focus on semantic HTML first, then ARIA correctness only where needed.
---

# ARIA Check

Use this skill for screen-reader and semantic accessibility review.

## Workflow

1. Prefer native semantics before ARIA additions.
2. Inspect roles, names, labels, descriptions, and keyboard flow.
3. Check focus order, focus visibility, and state announcements.
4. Verify custom widgets only use ARIA patterns that match real behavior.

## Rules

- Native HTML beats custom ARIA when both solve the problem.
- No ARIA is better than incorrect ARIA.
- Check `aria-label`, `aria-labelledby`, `aria-describedby`, `aria-expanded`, `aria-controls`, and landmark usage only where relevant.
- Call out mismatches between visual state and announced state.
- Treat dialogs, popovers, sheets, comboboxes, and form errors as high-risk areas.

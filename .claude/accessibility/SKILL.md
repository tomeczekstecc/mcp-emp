---
name: web-accessibility
description: Use when improving accessibility in this repository's frontend, especially for semantics, keyboard support, focus management, labels, contrast, dialog behavior, and inclusive interactions in apps/web.
---

# Web Accessibility

**Pattern source:** `context/accessibility.md` — read it before applying this skill. It is the single source of truth for the project's accessibility rules and examples.

## Overview

Use this skill when frontend work changes interaction, forms, modals, navigation, or custom UI. Keep accessibility built into the design instead of treating it as cleanup at the end.

## Workflow

1. Identify the user interaction path affected by the change.
2. Check semantics first: headings, buttons, labels, landmarks, and form relationships.
3. Check keyboard flow and visible focus behavior.
4. Check dynamic UI such as dialogs, dropdowns, tabs, and uploads for screen-reader and focus behavior.
5. Prefer accessible primitives and patterns over custom implementations when possible.

## Rules

- Do not use clickable non-buttons when a button fits.
- Keep labels, helper text, and error states explicit.
- Ensure dialog and menu interactions return focus correctly.
- Maintain color contrast and readable text sizes.
- Avoid animations that hide important state changes.

## Validation

- Manually test keyboard navigation on the changed flow.
- Run `npm run build` from `apps/web`.

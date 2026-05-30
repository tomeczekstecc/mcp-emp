---
name: web-ui-design
description: Use when designing or redesigning UI in this repository, especially for page composition, visual hierarchy, spacing, typography, color systems, interaction details, and frontend polish in apps/web. Use this skill to avoid generic layouts and produce intentional, cohesive interfaces.
---

# Web UI Design

**Pattern source:** `context/ui-patterns.md` — read it before applying this skill. It is the single source of truth for the project's visual hierarchy, spacing, and design system rules.

## Overview

Use this skill for visual design quality in `apps/web`. Favor intentional hierarchy, strong composition, and cohesive styling over generic card grids or default-looking interfaces.

## Workflow

1. Read the surrounding route and shared components before changing the visual language.
2. Decide whether to preserve an existing pattern or introduce a stronger one for the target area.
3. Build the layout around hierarchy first: primary action, focal content, support content.
4. Use spacing, scale, and contrast deliberately before adding decorative complexity.
5. Keep interactions clear, calm, and supportive of the task.

## Rules

- Avoid generic "AI slop" layouts.
- Prefer a clear visual direction over many competing accents.
- Use typography, spacing, and rhythm to make sections legible.
- Keep reusable UI primitives in `src/components/ui` and feature-specific composition elsewhere.
- Preserve mobile and desktop quality together.

## Validation

- Check the affected page visually on desktop and mobile.
- Run `npm run build` from `apps/web` after structural UI changes.

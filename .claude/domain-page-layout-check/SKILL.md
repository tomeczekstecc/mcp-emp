---
name: domain-page-layout-check
description: Use when creating or modifying a page under `src/app/(app)/` in this repository, or when adding a new route that needs breadcrumbs or a page title. Ensures domain pages render content only and that breadcrumbs + `<h2>` flow through `MenuConfig` or `breadcrumbRegistry`, never inline in the page.
---

# Domain Page Layout Check

**Pattern source:** `context/domain-page-layout.md` — read it before applying this skill. It is the single source of truth for breadcrumbs, page title rendering, and sidebar trigger placement.

## Overview

Domain pages under `src/app/(app)/` render **content only**. The app shell (`AppShell`) renders breadcrumbs, the `<h2>` page title, and the sidebar trigger **once**, deriving them from the pathname via:

1. `breadcrumbRegistry` (`src/lib/breadcrumbs/registry.ts`) — longest-pattern wins, supports `:param` segments.
2. `MenuConfig` fallback (`src/lib/breadcrumbs/from-menu.ts`) — automatic for any route already in the menu.

The last breadcrumb entry has no `href` and is reused by `PageTitle` as the `<h2>` text.

## Workflow

1. Open `context/domain-page-layout.md` and confirm the resolver order and `BreadcrumbEntry` shape.
2. If the new route is in `MenuConfig`, write nothing — the breadcrumb appears automatically.
3. If the route is dynamic, not in the menu, or needs custom labels, add a `breadcrumbRegistry` entry with a `match` pattern and a `map({ params })` returning the trail. Last entry has no `href`.
4. Keep `page.tsx` to content only. Optional `layout.tsx` may exist for metadata or shared padding — never for chrome.
5. Cross-check `context/nextjs-patterns.md` for server/client component placement and `context/ddd-patterns.md` for folder placement.

## Rules

- Pages **never** import `SiteHeader`, `DomainLayout`, `getNavLayout`, `useNavLayout`, or any `<Breadcrumb*>` primitive.
- Pages **never** render their own `<h1>` / `<h2>` page title.
- Trails are config: edit `breadcrumbRegistry` or `MenuConfig` — never inline a trail in a page or layout.
- Last entry in any trail has no `href`. Preceding entries always have `href`.
- Standard trail depth is 3 (`Start → Domain → Page`); 4 is acceptable for dynamic sub-pages.
- Root anchor for explicit registry trails is `{ label: "Start", href: "/dashboard" }`.
- `SidebarTrigger` stays in `AppSidebar`'s `SidebarHeader`; do not render it elsewhere.

## Validation

- Visit the new route and confirm breadcrumbs + `<h2>` render automatically without page-level code.
- `grep -rn "SiteHeader\\|DomainLayout\\|getNavLayout\\|<Breadcrumb" src/app/(app)/<route>` returns nothing.
- Run the "Checklist — before marking a domain complete" from `context/domain-page-layout.md`.
- `pnpm lint` and `pnpm build` succeed.

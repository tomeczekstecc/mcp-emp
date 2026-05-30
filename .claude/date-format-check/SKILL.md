---
name: date-format-check
description: Use when rendering, formatting, parsing, or exporting any date or timestamp in this repository's UI — table columns, badges, cards, CSV/XLSX exports, tooltips, relative-time displays, date pickers, and form inputs. Ensures the ISO 8601 short default (`YYYY-MM-DD` / `YYYY-MM-DD HH:mm`) is used via the shared helpers, and that relative time surfaces always carry an ISO tooltip.
---

# Date Format Check

**Pattern source:** `context/date-format.md` — read it before applying this skill. It is the single source of truth for the ISO default, the helper module location, the `<RelativeTime>` component, and approved deviations.

## Overview

Default visible date format: **ISO 8601 short** — `YYYY-MM-DD`, or `YYYY-MM-DD HH:mm` for timestamps. All formatting goes through shared helpers in `src/lib/format/date.ts` (`formatDate`, `formatDateTime`, `formatRelative`). Relative time (`<RelativeTime>` or `formatRelative`) is reserved for activity/audit surfaces and must always carry an ISO value in `title` and `dateTime`.

## Workflow

1. Open `context/date-format.md` and confirm the helper signatures, the relative-time decision table, and the deviations table.
2. For any new visible date, import `formatDate` or `formatDateTime` from `src/lib/format/date.ts`. If the helper module does not exist yet, create it as documented.
3. Pick ISO vs relative using the table:
   - Operational data (deadlines, submission dates, exports, pickers, form state) → ISO via `formatDate` / `formatDateTime`.
   - Activity / audit / "ostatnio edytowane" → `<RelativeTime value={…} />` (preferred) or manual `<time>` with `formatRelative` + ISO `title`.
4. For inputs, keep form state in `yyyy-MM-dd`. Native `<input type="date">` already does this; for `react-day-picker`, format the displayed value via `formatDate`.
5. For long-lived screens that need a ticking relative clock, build a thin `<RelativeTimeLive>` client wrapper (not inline `setInterval` per call site).
6. For an exception (prose/marketing surface needing `d MMMM yyyy`), document it in the "Approved Deviations" table in `context/date-format.md`.

## Rules

- No `toLocaleDateString()`, `Intl.DateTimeFormat` without explicit locale, or manual `${y}-${m}-${d}` concatenation in app code.
- No inline `format(date, "PPP")` or other ad-hoc patterns — always go through the shared helpers.
- Relative time renderings (`<RelativeTime>`, custom `<time>`) **must** carry the ISO value in both `dateTime` and `title`.
- Exports (CSV / XLSX) keep ISO unless the report has a documented exception.
- Date inputs return ISO (`yyyy-MM-dd`) to form state — never localised strings.
- Auto-refreshing relative time uses `setInterval >= 30s`; never tighter.
- Any new deviation requires an entry in the "Approved Deviations from the ISO Date Rule" table.

## Validation

- `grep -rn "toLocaleDateString\\|toLocaleString" src/` returns only entries from `src/components/ui/calendar.tsx` (the approved deviation).
- `grep -rn "format(.*\\"PPP\\"\\|d MMMM yyyy" src/` returns nothing new.
- Run the "Checklist" from `context/date-format.md`.
- `pnpm lint` and `pnpm build` succeed.

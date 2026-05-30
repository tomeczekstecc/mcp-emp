---
name: cleanup
description: Clean up project housekeeping tasks (add "run" to execute fixes)
argument-hint: run|check
---

Review the codebase for cleanup tasks:

1. Find unnecessary console.log statements in src/
2. Find unused imports (skip imports on lines immediately preceded by a `[keep-commented:*]` comment)
3. Check for stale TODO comments (skip any line or block tagged `[keep-commented:*]` — those are intentionally commented-out blocks pending config/env wiring and must not be removed)
4. Find orphaned/unused files
5. Check that context files match actual project state
6. Keep `.env` and `.env.example` in sync — compare variable names (not values); whichever file has more variables wins, add any missing keys to the other.
7. Find `@ts-ignore` comments that might be stale
8. Run `/ai-artifacts-sync` to keep `.claude/` and `.agents/` skill directories in sync
9. Run `@agent-seo-checker` to audit SEO coverage — check for missing metadata exports, robots.ts, sitemap.ts, and unindexed protected routes
10. Audit dead Tailwind classes — find utility classes referencing removed components or conflicting with Tailwind v4 syntax
11. Verify env var consumption — check that every variable declared in `.env.example` is actually used somewhere in `src/`
12. Find `any` type sprawl — locate `any` casts beyond known intentional ones
13. Find unused dependencies — flag packages in `package.json` that are imported nowhere in `src/`

**Mode: $ARGUMENTS**

If no argument or argument is "check":

- Only report findings, don't modify anything
- List what WOULD be cleaned up

If the argument is "run" or "fix":

- First, report all findings with numbered items
- Then ask: "Which items would you like me to fix? (enter numbers like 1,3,5 or 'all' or 'none')"
- Wait for user response before making any changes
- Only fix the items the user specifies
- Report what you changed

---
name: pattern-skill-sync-check
description: Use when auditing whether every documented pattern in `context/` has a matching skill that explicitly references its `context/<file>.md` path, and vice versa. Run after adding a new pattern doc, after adding a new skill, or when the user asks to verify pattern/skill consistency. Reports missing skills, orphan skills, and skills that fail to reference their source pattern file.
---

# Pattern ↔ Skill Sync Check

**Meta-skill.** Verifies the 1:1 mapping between `context/*.md` pattern docs and skills under `.agents/skills/` (mirrored to `.claude/skills/`).

## Scope

Pattern files (must have a corresponding skill) = every `context/*.md` **except** these meta/non-pattern files:

- `context/project-overview.md`
- `context/project-spec.md`
- `context/TODO.md`
- `context/coding-standards.md`
- `context/ai-interaction.md`

Do not hardcode the in-scope list — it grows. Always derive it from `ls context/*.md` minus the skip list above.

## Workflow

1. List pattern files:
   ```bash
   ls context/*.md
   ```
2. List skills:
   ```bash
   ls .agents/skills/
   ls .claude/skills/
   ```
3. For each pattern file in scope, verify a skill exists whose `SKILL.md` contains the literal string `context/<file>.md`:
   ```bash
   for f in context/*.md; do
     base=$(basename "$f")
     case "$base" in
       project-overview.md|project-spec.md|TODO.md|coding-standards.md|ai-interaction.md) continue ;;
     esac
     hits=$(grep -rl "context/$base" .agents/skills/ 2>/dev/null | wc -l)
     echo "$base → $hits skill ref(s)"
   done
   ```
4. Verify `.agents/skills/` and `.claude/skills/` contain the same directory set:
   ```bash
   diff <(ls .agents/skills/) <(ls .claude/skills/)
   ```
5. For each pattern-targeted skill, verify the two copies are byte-identical:
   ```bash
   for d in $(ls .agents/skills/); do
     diff -q ".agents/skills/$d/SKILL.md" ".claude/skills/$d/SKILL.md" 2>&1
   done
   ```

## Rules

- Every in-scope pattern file must have **at least one** skill whose `SKILL.md` references the literal path `context/<file>.md` in a "Pattern source" line.
- Skills covering a pattern must live in **both** `.agents/skills/` and `.claude/skills/` with identical `SKILL.md` content.
- Orphan skills (no matching pattern) are allowed only for cross-cutting agent tooling (e.g. `git-add-push`, `speckit-*`, `cleanup`); flag any new domain-looking orphan.
- The reference must be the exact path string `context/<file>.md`, not a paraphrase, so grep stays reliable.

## Report Format

Produce a short markdown report:

```
## Pattern ↔ Skill Sync Report

### Missing skills (pattern → no skill references it)
- context/<file>.md

### Skills missing the pattern reference
- .agents/skills/<name>/SKILL.md — expected ref to context/<file>.md

### .agents vs .claude divergence
- <skill-name>: differs / missing in one side

### OK
- N patterns mapped, M skill pairs in sync.
```

## Validation

- The report runs cleanly with no items under "Missing", "Missing reference", or "divergence" sections.
- Re-running the workflow on a clean repo yields the same OK summary.

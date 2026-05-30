---
name: list-custom-skills
description: Lists all custom (non-built-in) skills installed in this project with a brief description of each. Use whenever the user asks what skills are available, wants to see custom skills, asks "what can you do", asks to list or show skills, or wants a skills overview for this project. Speckit/Specify workflow skills are listed separately at the end.
---

# List Custom Skills

Scan the project's skill directories, read each skill's name and description, and present a clean formatted list. Speckit/Specify skills go in their own section at the end.

## Where skills live

Check both directories — they mirror each other for most skills:
- `.claude/skills/` — Claude Code skills
- `.agents/skills/` — OpenAI/Codex/OpenCode skills

Use `.claude/skills/` as the primary source. Each subdirectory contains a `SKILL.md` with YAML frontmatter holding `name` and `description`.

## How to build the list

1. List all subdirectories under `.claude/skills/`
2. For each, read the first ~5 lines of `SKILL.md` to extract `name` and `description` from the frontmatter
3. Split into two groups:
   - **Custom skills**: everything whose directory name does not start with `speckit`
   - **Speckit skills**: directories starting with `speckit` (e.g. `speckit-specify`, `speckit-plan`, `speckit-git-*`)
4. Sort each group alphabetically by name
5. Output the formatted report below

## Output format

Use this structure exactly:

```
## Custom Skills

**<name>**
<one-sentence description — trim to ~120 chars if the original is longer>

...one block per skill...

---

## Speckit / Specify Skills

**<name>**
<one-sentence description>

...
```

Keep descriptions to a single sentence. If the SKILL.md description is a long paragraph, extract the first sentence or the clearest summary clause — the goal is a quick scannable reference, not the full trigger spec.

If a skill directory exists in `.agents/skills/` but not in `.claude/skills/` (or vice versa), include it and note which side it came from in parentheses, e.g. `(agents only)`.

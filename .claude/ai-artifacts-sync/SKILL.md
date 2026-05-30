---
name: ai-artifacts-sync
description: Syncs AI agent artifacts between .agents/ and .claude/ skill directories in this project, and keeps CLAUDE.md, AGENTS.md, and CURSOR.md identical. Use whenever the user wants to sync, align, or check consistency of AI tool configs, skills, or agent definitions across Claude Code and OpenAI/Codex ecosystems. Triggers on "sync skills", "sync agents", "sync AI artifacts", "are .agents and .claude in sync", "sync CLAUDE.md and AGENTS.md", or any request to check or ensure consistency between AI tool configurations.
---

# AI Artifacts Sync

Keeps AI configuration artifacts consistent across the two tool ecosystems in this project:

- **`.claude/skills/`** — Claude Code (Anthropic)
- **`.agents/skills/`** — OpenAI Codex / OpenCode and compatible agents

## What gets synced

### Skill directories
Each skill lives at `<dir>/skills/<name>/`. Both directories should contain the same set of skill names with identical content, except for tool-specific config files (see below).

### Bundled resources
All files inside a skill directory — `SKILL.md`, `references/`, `assets/`, `evals/`, `rules/`, `cli.md`, `customization.md`, and any other non-config files — are synced in both directions.

### Tool-specific configs — never cross the boundary
- `.agents/skills/<name>/agents/openai.yaml` and `openai.yml` — stays in `.agents/` only
- `.claude/agents/<name>.md` — Claude Code subagent definitions, stays in `.claude/` only

### CLAUDE.md ↔ AGENTS.md ↔ CURSOR.md
These three root files must always be identical.

## Sync rules

**Source of truth**: the more recently modified file always wins. Never ask — just use recency.

**Never delete**: only add or overwrite. A skill present on one side but not the other gets copied across; skills are never removed during sync.

## Workflow

### Step 1: Detect drift

Run these checks in parallel:

```bash
# Skills only in .agents/
comm -23 <(ls .agents/skills/ | sort) <(ls .claude/skills/ | sort)

# Skills only in .claude/
comm -13 <(ls .agents/skills/ | sort) <(ls .claude/skills/ | sort)

# CLAUDE.md vs AGENTS.md vs CURSOR.md
diff CLAUDE.md AGENTS.md
diff CLAUDE.md CURSOR.md
```

For each shared skill, diff the full directory content (excluding tool-specific configs):
```bash
diff -r --exclude="openai.yaml" --exclude="openai.yml" \
  .agents/skills/<name>/ .claude/skills/<name>/
```

### Step 2: Report findings

Show a summary before making any changes:

```
## Sync report

Skills only in .agents/:   <list or "none">
Skills only in .claude/:   <list or "none">
Shared skills with drift:  <list of skill names with differing files, or "none">
CLAUDE.md vs AGENTS.md:    <"identical" or "differ">
CLAUDE.md vs CURSOR.md:    <"identical" or "differ">
```

### Step 3: Sync

For each item with drift:

**Skill only in `.agents/`** — copy the full directory to `.claude/skills/<name>/`, skipping `agents/openai.yaml` and `agents/openai.yml`.

**Skill only in `.claude/`** — copy the full directory to `.agents/skills/<name>/`, skipping nothing (`.claude/agents/` subagent defs are at `.claude/agents/`, not inside skill directories).

**Shared skill with differing files** — for each differing file, compare modification timestamps and overwrite the older with the newer. Use:
```bash
# Compare timestamps
python -c "import os; a=os.path.getmtime('.agents/skills/<name>/<file>'); c=os.path.getmtime('.claude/skills/<name>/<file>'); print('agents' if a>c else 'claude')"
```

**CLAUDE.md ↔ AGENTS.md ↔ CURSOR.md** — compare modification times across all three, use the newest as source of truth and overwrite the other two.

### Step 4: Confirm

Re-run the diffs from Step 1 and report that everything is now aligned. List all files that were changed.

## This skill syncs itself

`ai-artifacts-sync` must exist in both `.claude/skills/ai-artifacts-sync/SKILL.md` and `.agents/skills/ai-artifacts-sync/SKILL.md`. If it is missing from either side, copy it as part of the sync pass.

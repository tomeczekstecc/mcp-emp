---
name: todo-context
description: Add structured TODO items to this repository's context/TODO.md file. Use when the user asks to add, record, capture, track, or remember a TODO, follow-up, task, backlog note, improvement, or action item in the project context, especially when content, priority, branch, date, or related domain should be recorded.
---

# Context TODO

## Overview

Append TODO items to `context/TODO.md` using a consistent, auditable format that includes content, priority, date, current branch, and related domain.

## Workflow

1. Gather required fields:
   - `content`: Ask the user if the TODO content is missing or vague.
   - `priority`: Ask the user if priority is missing. Accept `low`, `medium`, `high`, or `critical`; default only when the user explicitly allows it.
   - `related domain`: Infer from the request or touched files when obvious, otherwise ask. Use concise domain names such as `auth`, `api`, `ui`, `docs`, `dashboard`, `landing-page`, or `general`.
2. Get the current date from the environment context when available; otherwise run the local date command.
3. Get the current branch with `git branch --show-current`.
4. Ensure `context/TODO.md` exists. If missing, create it with:

```md
# TODO

Project-level follow-ups captured by agents.
```

5. Append the item under a `## Open` section. If the section does not exist, add it after the title/intro.
6. Preserve existing TODO content and ordering. Never rewrite completed/history sections unless the user asks.

## Item Format

Use this exact block:

```md
- [ ] <content>
  - Priority: <low|medium|high|critical>
  - Date: <YYYY-MM-DD>
  - Branch: `<branch-name>`
  - Domain: <related-domain>
```

## Rules

- Keep TODO content as a single clear action sentence.
- Do not invent priority. Ask for it unless the user already provided it.
- Prefer the current git branch exactly as reported by Git. If Git returns nothing, use `unknown`.
- Use ASCII unless the user-provided TODO content requires otherwise.
- After editing, briefly report the appended TODO item and file path.

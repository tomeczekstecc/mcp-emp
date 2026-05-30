---
name: code-review
description: Use when the user asks for a review, bug scan, regression check, or implementation critique for frontend code in this repository. Focus on defects, behavioral regressions, risky assumptions, missing edge handling, and maintainability risks before style notes.
---

# Code Review

Use this skill when the user asks for a review or when a change needs a focused quality pass.

## Review Priorities

1. Bugs and behavioral regressions
2. Security or data exposure concerns
3. Accessibility and UX breakage
4. Performance and rendering risks
5. Maintainability and design issues

## Workflow

1. Read only the files relevant to the change.
2. Compare intent against the implementation.
3. Look for broken states, edge cases, and risky assumptions.
4. Prefer concrete findings with file references over broad opinions.
5. Keep summaries short after findings are listed.

## Rules

- Findings come first, ordered by severity.
- Prioritize real breakage over stylistic commentary.
- Call out missing validation, incorrect state flow, and surprising side effects.
- Respect the project constitution: no automated test recommendations unless the user explicitly overrides project rules.
- If no findings exist, say so clearly and note any residual risk.

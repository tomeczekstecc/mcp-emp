---
name: destructive-actions-check
description: Use when implementing or reviewing any destructive action in this repository — delete, remove, discard, withdraw, revoke, archive-without-undo, single-row and bulk variants. Ensures the trigger is non-destructive, a named confirmation dialog gates the mutation, and the confirm button carries the `destructive` variant with a pending state.
---

# Destructive Actions Check

**Pattern source:** `context/destructive-actions.md` — read it before applying this skill. It is the single source of truth for the confirm-before-delete pattern, including bulk variants and the soft-delete-with-undo exception.

## Overview

Every irreversible action must be preceded by a confirmation dialog. The trigger is **non-destructive** (`ghost` / `outline`). The **dialog's confirm button** carries the `destructive` variant. The trigger is never `destructive` itself — otherwise the user sees red twice with no escalation.

Exception: soft-delete with an immediate undo toast (Sonner `action: { label, onClick }`) — no dialog needed.

## Workflow

1. Open `context/destructive-actions.md` and confirm the pattern shape and checklist.
2. Wrap the action in a `<Dialog>` (or `<AlertDialog>`). Trigger button = `ghost` or `outline` with a clear `aria-label`.
3. Dialog title names the **specific resource** (e.g. `Usunąć wniosek „{title}"?`) or the count for bulk operations.
4. Dialog description states irreversibility explicitly (e.g. `Tej operacji nie można cofnąć`).
5. Confirm button uses `variant="destructive"`, an action-verb label (`Usuń`, not `OK`), and shows a pending state (`Usuwanie…` + `disabled={isPending}`).
6. Cancel button uses `variant="outline"` with `Anuluj`.
7. For very large operations (10+ records or cascading effects), require typing a confirm phrase (`USUŃ`) before enabling the destructive button.
8. Cross-check `context/button-patterns.md` for the variant rationale and `context/api-mutation-pattern.md` for the mutation hook running after confirm.

## Rules

- Trigger button is **never** `destructive`.
- Never call the mutation directly from the trigger — always go through the dialog.
- Never use `window.confirm` — it does not match the app's style or a11y baseline.
- Dialog title must name the specific resource or count — never just `Czy na pewno?`.
- Dialog must describe the irreversibility in plain text.
- Confirm button disables and shows a pending label while the mutation runs.
- Bulk operations show the count in both trigger and confirm.
- Soft-delete + undo is the only allowed dialog-free destructive path; it requires a visible Sonner undo action.

## Validation

- Walk the destructive flow in the UI: trigger opens dialog, cancel closes without mutation, confirm runs mutation with pending UI, and on error the dialog stays open with the error visible.
- Run the "Checklist for every destructive action" from `context/destructive-actions.md`.
- `pnpm lint` and `pnpm build` succeed.

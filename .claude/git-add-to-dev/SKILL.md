---
name: git-add-to-dev
description: Stage changes, commit with a conventional prefix, push the current feature branch, merge it into `feature/dev` (if it exists locally or on any remote) or `master`, push the integration branch, then check out that integration branch. Use whenever the user says "add to dev", "ship to dev", "merge to dev", "push and merge", "send to dev", "merge feature to dev", "commit and merge to dev", or any request to land current work on the dev/master integration branch.
---

# Git Add → Commit → Push → Merge to Dev → Checkout Dev

This skill lands the current feature branch on the integration branch (`feature/dev`
if it exists, `master` otherwise). It is the "Mantis-style ship to integration" workflow.

## Workflow

### 1. Inspect the working tree

Run in parallel to understand what changed:

```bash
git status
git diff --stat
git branch --show-current
git log --oneline -5
```

Identify the **current branch** (call it `FEATURE_BRANCH`). If the working tree
is clean and there is nothing to commit, skip steps 2–3 and go straight to step 4.

### 2. Choose the commit type

| Prefix | When to use |
|--------|-------------|
| `feat:` | New feature or user-visible capability |
| `fix:` | Bug fix |
| `chore:` | Tooling, config, deps, build, CI — no production logic |
| `docs:` | Documentation only |
| `refactor:` | Code restructuring with no behavior change |
| `test:` | Adding or updating tests |
| `style:` | Formatting, whitespace — no logic change |
| `perf:` | Performance improvement |

Add an optional scope: `feat(auth):`, `chore(deps):`, etc.

### 3. Stage and commit

Prefer staging specific files; use `git add -A` only when every change is intentional:

```bash
git add <file1> <file2> ...
# or
git add -A
```

Commit with a short imperative-mood subject (≤ 50 chars):

```bash
git commit -m "feat(scope): short description"
```

### 4. Push the feature branch

Push `FEATURE_BRANCH` to every configured remote:

```bash
git remote          # list remotes
git push <remote> HEAD
```

Stop and report if any remote rejects the push. Do **not** force-push.

### 5. Resolve the integration branch

Check whether `feature/dev` exists — locally **or** on any remote:

```bash
git branch -a | grep -E "^(\*| )\s*feature/dev$|remotes/.*/feature/dev"
```

- If **found** → `INTEGRATION_BRANCH=feature/dev`
- If **not found** → `INTEGRATION_BRANCH=master`

### 6. Merge feature branch into the integration branch

```bash
git checkout <INTEGRATION_BRANCH>
git pull <remote> <INTEGRATION_BRANCH>          # fast-forward to latest
git merge --no-ff <FEATURE_BRANCH> -m "chore: merge <FEATURE_BRANCH> into <INTEGRATION_BRANCH>"
```

If the merge produces **conflicts**, stop immediately:
- Report which files conflict.
- Instruct the user to resolve conflicts manually, then run `git merge --continue`.
- Do **not** attempt automatic conflict resolution.

### 7. Push the integration branch

```bash
git push <remote> <INTEGRATION_BRANCH>
```

Push to every remote, same as step 4. Stop and report on rejection.

### 8. Stay on the integration branch

After pushing, remain checked out on `INTEGRATION_BRANCH` (`feature/dev` or `master`).
Confirm to the user:

```
✔ Committed on <FEATURE_BRANCH>
✔ Pushed <FEATURE_BRANCH> to <remotes>
✔ Merged into <INTEGRATION_BRANCH>
✔ Pushed <INTEGRATION_BRANCH> to <remotes>
✔ Now on <INTEGRATION_BRANCH>
```

## Rules

- Never force-push (`--force`, `--force-with-lease`) unless the user explicitly asks.
- Never use `--no-verify` or bypass hooks.
- Always pull the integration branch before merging to minimise conflicts.
- Always use `--no-ff` for the merge so the feature boundary is visible in history.
- If `FEATURE_BRANCH` is already `feature/dev` or `master`, skip the merge step and
  just commit + push.
- Stage thoughtfully — check for `.env`, credentials, or large binaries before `git add -A`.

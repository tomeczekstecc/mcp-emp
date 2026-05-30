---
name: git-add-push
description: Stage changes, commit with a conventional commit prefix (feat:, fix:, chore:, docs:, refactor:, test:, style:, perf:), and push to every configured remote. Use whenever the user says "commit and push", "push my changes", "save and push", "add commit push", "ship this", or wants to send their current work to the remote. Also triggers on "stage and commit", "push to all remotes", or any request to persist local work upstream.
---

# Git Add, Commit, and Push

## Workflow

### 1. Inspect the working tree

Run these in parallel to understand what changed and why:

```bash
git status
git diff --stat
git diff
```

Also check recent commits to match the repo's message style:

```bash
git log --oneline -5
```

### 2. Choose the commit type

Pick the prefix that best describes the dominant intent of the changes:

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

If the changes span multiple types, use the one that describes the biggest impact. A commit that adds a feature and updates docs is `feat:`.

Optionally add a scope in parentheses when it clarifies the area: `feat(auth):`, `chore(deps):`.

### 3. Stage the files

Prefer staging specific files over `git add -A` to avoid accidentally including secrets or unrelated noise:

```bash
git add <file1> <file2> ...
```

If everything in the working tree is intentional, `git add -A` is fine — but verify with `git status` first.

### 4. Commit

Write a short, imperative-mood subject line (50 chars or less):

```bash
git commit -m "feat(auth): add JWT refresh token rotation"
```

If the reason behind the change isn't obvious from the subject, add a body:

```bash
git commit -m "$(cat <<'EOF'
feat(auth): add JWT refresh token rotation

Tokens now rotate on each use to reduce the window for replay attacks.
EOF
)"
```

### 5. Push to all remotes

Discover all configured remotes and push to each:

```bash
git remote
```

Then push to each one:

```bash
git push <remote> HEAD
```

If a remote rejects the push (non-fast-forward), report it to the user and stop — do not force-push without explicit instruction.

## Rules

- Never use `--no-verify` or bypass hooks unless the user explicitly asks.
- Never force-push (`--force`, `--force-with-lease`) without explicit instruction.
- If there is nothing to commit (`git status` shows clean), say so and skip.
- If pre-commit hooks fail, fix the underlying issue and retry rather than bypassing.
- Stage thoughtfully — check for `.env`, credentials, or large binaries before `git add -A`.

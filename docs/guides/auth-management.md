# Auth Management Guide

mcp-emp can require API-key authentication when running in HTTP transport mode.
This guide covers everything: setup, user management, key lifecycle, and
security practices.

---

## Overview

| Transport | Auth | Notes |
|---|---|---|
| `stdio` | **None** — OS process isolation | Desktop hosts: Claude Desktop, pi, Cursor |
| `http` + `AUTH_ENABLED=false` | None | Localhost-only, single-user setups |
| `http` + `AUTH_ENABLED=true` | **Bearer API key** | Multi-client, LAN, or hosted setups |

When auth is enabled, every HTTP request to `/mcp`, `/sse`, and `/messages`
must include:

```
Authorization: Bearer emp_<username>_<32hex>
```

The `/healthz` endpoint is **always open** (used by health probes).

---

## Storage

Keys are stored in a SQLite database (default `~/.mcp_emp/auth.db`).

- **Plaintext keys are never stored** — only the SHA-256 hash.
- The key is shown exactly once: at `add-user` and `revoke-key` time.
- If you lose a key, revoke it and generate a new one.

Configure a custom path:

```env
MCP_EMP_AUTH_DB_PATH=/srv/mcp_emp/auth.db
```

---

## First-time setup

```bash
# 1. Initialise the database
mcp-emp auth init

# 2. Create the first superuser
#    --force is required when no superuser exists yet (bootstrap)
mcp-emp auth add-user tomasz --superuser --force

# API key (shown once): emp_tomasz_a3f9c2b1d4e8f7a2b3c4d5e6f7a8b9c0
# Store this key securely!

# 3. Enable auth in .env
echo "MCP_EMP_AUTH_ENABLED=true" >> .env
echo "MCP_EMP_TRANSPORT=http"    >> .env
```

---

## User roles

| Role | Can add users | Can add superusers | Can delete/revoke any user |
|---|---|---|---|
| **superuser** | Yes (via CLI `--force`) | Yes (via CLI `--force`) | Yes |
| **user** | No | No | No |

> For now, all user management is done through the CLI by someone with
> filesystem access to the DB. There are no MCP tools for auth management —
> auth management is an operator concern, not an LLM concern.

---

## CLI reference

### `mcp-emp auth init`

Initialise the SQLite database.  Safe to run multiple times (idempotent).

```bash
mcp-emp auth init
# Auth DB initialised at C:\Users\stect\.mcp_emp\auth.db
```

---

### `mcp-emp auth add-user <username> [--superuser] [--force]`

Create a user and generate their API key.

```bash
# Add a regular user
mcp-emp auth add-user alice
# Created user 'alice'.
# API key (shown once): emp_alice_7f3a9b2c1d4e5f6a7b8c9d0e1f2a3b4c
# Store this key securely — it cannot be retrieved again.

# Add a superuser (requires --force when bootstrapping)
mcp-emp auth add-user bob --superuser --force
# Created superuser 'bob'.
# API key (shown once): emp_bob_...
```

| Flag | Description |
|---|---|
| `--superuser` | Grant superuser privileges. |
| `--force` | Allow creation even when no existing superuser is present (bootstrap). |

---

### `mcp-emp auth list-users`

List all registered users with key prefix and status.

```bash
mcp-emp auth list-users
# USERNAME             ROLE         KEY PREFIX       ACTIVE   CREATED
# -----------------------------------------------------------------------
# alice                user         emp_alice_7f3...  yes      2026-05-30T14:00:00
# bob                  superuser    emp_bob_a1b2...   yes      2026-05-30T14:01:00
# tomasz               superuser    emp_tomasz_c3...  yes      2026-05-30T13:55:09
```

The key prefix shows the first 12 characters of the key followed by `...`.
It is safe to share — it cannot be used to authenticate.

---

### `mcp-emp auth revoke-key <username>`

Invalidate the current key and generate a new one.  The old key stops working
**immediately** on the next request.

```bash
mcp-emp auth revoke-key alice
# New API key for 'alice' (shown once): emp_alice_9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a
# Store this key securely!
```

Use this when:
- A key is compromised or leaked.
- Rotating keys on a schedule.
- Handing a key to a new person.

---

### `mcp-emp auth delete-user <username>`

Remove a user and their key permanently.

```bash
mcp-emp auth delete-user alice
# Deleted user 'alice'.
```

Their key stops working immediately.

---

## Connecting clients with an API key

### MCP Inspector (browser)

1. Open the Inspector and configure your server URL.
2. Add a custom header:
   - **Header name:** `Authorization`
   - **Header value:** `Bearer emp_alice_7f3a9b2c...`

### Claude Desktop (HTTP mode)

```json
{
  "mcpServers": {
    "emp": {
      "url": "http://127.0.0.1:8765/mcp",
      "headers": {
        "Authorization": "Bearer emp_alice_7f3a9b2c..."
      }
    }
  }
}
```

### n8n

In the MCP node credentials, set:

```
Authentication: Header Auth
Header Name: Authorization
Header Value: Bearer emp_alice_7f3a9b2c...
```

### curl / scripting

```bash
KEY="emp_alice_7f3a9b2c1d4e5f6a7b8c9d0e1f2a3b4c"

# Healthz (no key needed)
curl http://127.0.0.1:8765/healthz

# List tools
curl -X POST http://127.0.0.1:8765/mcp \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## Running the HTTP server with auth

```bash
# .env
MCP_EMP_TRANSPORT=http
MCP_EMP_AUTH_ENABLED=true
MCP_EMP_AUTH_DB_PATH=~/.mcp_emp/auth.db
MCP_EMP_SSE_HOST=127.0.0.1   # change to 0.0.0.0 only on a trusted LAN
MCP_EMP_SSE_PORT=8765

# Start
mcp-emp
```

Startup log will confirm auth is active:

```
HTTP auth enabled (API-key, db=/home/user/.mcp_emp/auth.db)
mcp-emp ready, transport=http
```

---

## Security notes

| Practice | Recommendation |
|---|---|
| **Key storage** | Store keys in your LLM host's secret manager, not in plain config files. |
| **Scope** | Keep `SSE_HOST=127.0.0.1` unless you need LAN access. Never expose to the public internet without a TLS reverse proxy. |
| **Rotation** | Run `revoke-key` whenever a team member leaves or a key may have been exposed. |
| **Least privilege** | Regular users (non-superuser) are sufficient for all LLM workflows. |
| **DB backup** | The DB contains key hashes, not plaintexts. Backing it up is safe. |
| **Lost key** | If you lose a key, run `revoke-key` — the new key is shown once. |

---

## Key format

```
emp_<username>_<32 hex characters>
│   │           │
│   │           └─ 16 random bytes → 128 bits of entropy
│   └─────────────── username (makes keys identifiable by prefix)
└─────────────────── "emp" prefix (distinguishes from other Bearer tokens)
```

Example: `emp_alice_7f3a9b2c1d4e5f6a7b8c9d0e1f2a3b4c`

The full key is **212+ bits of effective security** (prefix is predictable but
the 32-hex suffix is random).  SHA-256 hash is stored in the DB.

---

## Template management (mcp-emp template)

Task templates live in a separate SQLite database at `~/.mcp_emp/templates.db`.
They are managed independently from auth users.

```bash
# Create a template for daily standups
mcp-emp template add daily_standup \
  --task-type-id 28 \
  --subject "Standup {today}" \
  --deadline-days 0

# Create a template with tags
mcp-emp template add bug_fix \
  --task-type-id 28 \
  --subject "Poprawka: {today}" \
  --tags "1,5"

# List all templates
mcp-emp template list

# Show a specific template in JSON
mcp-emp template show daily_standup

# Delete a template
mcp-emp template delete old_template
```

Then in your LLM session:
```
> "create a standup task for today"
LLM → list_templates() → picks "daily_standup"
LLM → apply_template("daily_standup", dry_run=true) → preview
LLM → apply_template("daily_standup") → task created
```

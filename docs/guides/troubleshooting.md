# Troubleshooting Guide

---

## Server won't start — exit code 77

**Symptom:** `mcp-emp` exits immediately with code 77.

**Cause:** Keycloak login failed (`AUTH_MISCONFIGURED`).

**Fix:**

```bash
# Check the KC URL is reachable
curl https://emp-auth.slaskie.pl/realms/eMP/.well-known/openid-configuration

# Test login manually
curl -X POST https://emp-auth.slaskie.pl/realms/eMP/protocol/openid-connect/token \
  -d "grant_type=password&client_id=eMP&username=YOUR_USER&password=YOUR_PASS"

# Common mistakes:
# - MCP_EMP_KC_BASE_URL includes /auth suffix but KC doesn't need it
#   Wrong: https://emp-auth.slaskie.pl/auth
#   Right: https://emp-auth.slaskie.pl
#
# - Wrong client_id — use "eMP" (public client), not "eMP-REST-API"
# - Password contains special characters — wrap in single quotes in shell
```

---

## All EMP endpoints return 500

**Symptom:** `health_check` works but every tool call fails with
`"Błąd ogólny. Skontaktuj się z administratorem."` (500).

**Cause:** The KC access token is missing `team`/`unit`/`azp` claims needed
by the EMP authorization middleware, OR the user is not provisioned in the
EMP database.

**Fix — wrong `client_id`:**

```bash
# Confirm which client_id you're using
echo $MCP_EMP_KC_CLIENT_ID   # should be "eMP", not "eMP-REST-API"
```

The `eMP` (frontend) client has the correct role mappers that put roles under
`resource_access['eMP']` matching `azp=eMP`.  The `eMP-REST-API` client needs
additional mapper configuration in KC admin.

**Fix — missing team/unit claims:**

Add fallbacks to `.env`:

```env
MCP_EMP_KC_UNIT=CI
MCP_EMP_KC_TEAM=CI-PRS
```

Note: these fallbacks fix our identity tracking but don't fix the EMP
middleware if it also reads from the JWT.  In that case, a KC admin must add
the `team` and `unit` user-attribute mappers to the access token.

---

## MCP Inspector shows "not connected"

**Symptom:** The Inspector UI says the server is not connected.

**Cause 1 — typo in command name.**
`mcp-emp` not `mcp-em` or `mcp_emp`.

**Cause 2 — wrong working directory.**
The server can't find `.env`.  Run the Inspector from the project directory:

```bash
cd C:\dev\python\mcp_emp
npx @modelcontextprotocol/inspector uv run mcp-emp
```

**Cause 3 — Inspector too old.**
The Inspector proxy may have a race condition.  Try:

```bash
npx @modelcontextprotocol/inspector@latest uv run mcp-emp
```

**Cause 4 — port already in use (HTTP mode).**

```bash
netstat -ano | findstr :8765
# Kill the PID listed
taskkill /F /PID <PID>
```

---

## HTTP 401 Unauthorized

**Symptom:** HTTP transport returns 401 on every request.

**Cause:** `MCP_EMP_AUTH_ENABLED=true` but no valid key provided.

**Fix:**

```bash
# Check the DB has users
mcp-emp auth list-users

# If empty, add one
mcp-emp auth init
mcp-emp auth add-user yourname --superuser --force

# Confirm the header format in your client
Authorization: Bearer emp_yourname_<32hex>   # note: "Bearer " with a space
```

---

## HTTP 401 after restart

**Symptom:** Key was working but stopped after a server restart.

**Cause:** API keys are stored in SQLite and survive restarts.  This is
probably a `.env` issue — `MCP_EMP_AUTH_ENABLED` may have been unset.

**Fix:**

```bash
# Confirm auth is still enabled
grep AUTH_ENABLED .env

# Confirm the DB path is correct
mcp-emp auth list-users
```

---

## `add_my_task` fails with VALIDATION_FAILED

**Symptom:** `{"code": "VALIDATION_FAILED", "message": "task_type_id=X not found..."}`

**Cause:** The `task_type_id` is not in the cached dictionary for the current user's team.

**Fix:**

```bash
# Find valid task types for your team
list_task_types(team_id="CI-PRS")

# If the type exists in EMP but not in results, the cache may be stale
# Restart mcp-emp to clear the in-memory cache
```

---

## `complete_task` fails with INVALID_TRANSITION

**Symptom:** `{"code": "INVALID_TRANSITION", "current_status": "W_EDYCJI", "attempted_operation": "zakoncz"}`

**Cause:** The task is still in `W_EDYCJI` (draft). It must be in `REALIZOWANE`
or `DO_OCENY` to be completed.

`add_my_task` creates tasks directly in `REALIZOWANE` — this error usually
means the task was manually set back to `W_EDYCJI` in the EMP web UI.

**Fix:** Start the task first (not yet exposed as a tool — use the EMP web UI),
then call `complete_task`.

---

## `delete_task` token expired

**Symptom:** Step-2 delete fails with `{"code": "CONFIRMATION_INVALID", "reason": "expired"}`.

**Cause:** The confirmation token has a 5-minute TTL.  More than 5 minutes
passed between step 1 and step 2.

**Fix:** Call `delete_task(task_id=X)` again (no token) to get a fresh token,
then immediately call with the new token.

---

## DEBUG logging

Enable debug logs to diagnose any issue:

```env
MCP_EMP_LOG_LEVEL=DEBUG
```

Debug logs include all httpx request/response details.  Credentials are
**automatically redacted** — it is safe to share debug output.

```bash
mcp-emp 2>debug.log   # redirect stderr to file
```

---

## Checking connectivity manually

```bash
# Is EMP reachable?
curl https://emp-api.slaskie.pl/api

# Is KC reachable?
curl https://emp-auth.slaskie.pl/realms/eMP/.well-known/openid-configuration

# Does login work?
curl -X POST https://emp-auth.slaskie.pl/realms/eMP/protocol/openid-connect/token \
  -d "grant_type=password&client_id=eMP&username=USER&password=PASS" \
  | python -m json.tool
```

---

## Getting help

1. Check this guide first.
2. Enable `DEBUG` logging and review stderr.
3. Call `health_check` — it shows auth status and EMP reachability.
4. Check the planning docs in `docs/` for architectural context.

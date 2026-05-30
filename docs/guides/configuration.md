# Configuration Reference

All settings are read from environment variables (prefix `MCP_EMP_`) or from
a `.env` file in the working directory.

---

## EMP Backend

| Variable | Default | Description |
|---|---|---|
| `MCP_EMP_API_BASE_URL` | `http://localhost:480/api` | EMP API base URL. All tool calls go here. |

---

## Keycloak Authentication

| Variable | Default | Description |
|---|---|---|
| `MCP_EMP_KC_BASE_URL` | `https://auth-lsi2021-dev.slaskie.pl/auth` | Keycloak base URL (no trailing slash). |
| `MCP_EMP_KC_REALM` | `eMP` | Keycloak realm name. |
| `MCP_EMP_KC_CLIENT_ID` | `eMP-REST-API` | OAuth2 client ID. Use `eMP` (public client) if the API client doesn't have the right role mappers. |
| `MCP_EMP_KC_CLIENT_SECRET` | *(empty)* | Client secret. Leave empty for public clients. |
| `MCP_EMP_KC_USERNAME` | *(empty)* | EMP username (Resource Owner Password grant). |
| `MCP_EMP_KC_PASSWORD` | *(empty — required)* | EMP password. |
| `MCP_EMP_KC_UNIT` | *(empty)* | Fallback `unit` claim when KC token doesn't include it (e.g. `CI`). |
| `MCP_EMP_KC_TEAM` | *(empty)* | Fallback `team` claim when KC token doesn't include it (e.g. `CI-PRS`). |

> **Why `KC_CLIENT_ID=eMP`?**  
> The EMP middleware reads roles from `resource_access[azp]['roles']` in the
> JWT.  If using `eMP-REST-API` as client, roles land under
> `resource_access['eMP-REST-API']` but `azp` is also `eMP-REST-API` — this
> only works when the KC client has the correct role mappers configured.
> The `eMP` public client (the frontend client) already has the correct mappers
> and no secret is required.

---

## Transport

| Variable | Default | Description |
|---|---|---|
| `MCP_EMP_TRANSPORT` | `stdio` | `stdio` — for desktop hosts; `http` — for web/hosted agents. |
| `MCP_EMP_SSE_HOST` | `127.0.0.1` | Bind host for HTTP transport. |
| `MCP_EMP_SSE_PORT` | `8765` | Bind port for HTTP transport. |

---

## Runtime

| Variable | Default | Description |
|---|---|---|
| `MCP_EMP_LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. DEBUG is safe — credentials are redacted. |
| `MCP_EMP_READ_ONLY` | `false` | When `true`, all mutating tools are blocked (including `dry_run=true`). |

---

## Cache

| Variable | Default | Description |
|---|---|---|
| `MCP_EMP_TASK_TYPE_TTL` | `600` | Task type cache TTL in seconds (10 min). |
| `MCP_EMP_TAG_TTL` | `300` | Tag cache TTL in seconds (5 min). |

---

## MCP API-key Auth (HTTP transport only)

| Variable | Default | Description |
|---|---|---|
| `MCP_EMP_AUTH_ENABLED` | `false` | Enable API-key auth on HTTP transport. Has no effect on stdio. |
| `MCP_EMP_AUTH_DB_PATH` | `~/.mcp_emp/auth.db` | Path to the SQLite database of API users and keys. |

---

## Complete `.env.example`

```env
# ── EMP Backend ──────────────────────────────────────────────────────────────
MCP_EMP_API_BASE_URL=https://emp-api.slaskie.pl/api

# ── Keycloak ─────────────────────────────────────────────────────────────────
MCP_EMP_KC_BASE_URL=https://emp-auth.slaskie.pl
MCP_EMP_KC_REALM=eMP
MCP_EMP_KC_CLIENT_ID=eMP
MCP_EMP_KC_CLIENT_SECRET=
MCP_EMP_KC_USERNAME=your_username
MCP_EMP_KC_PASSWORD=your_password

# Optional: fallback when KC token lacks team/unit LDAP claims
MCP_EMP_KC_UNIT=CI
MCP_EMP_KC_TEAM=CI-PRS

# ── Transport ─────────────────────────────────────────────────────────────────
MCP_EMP_TRANSPORT=stdio          # or: http
MCP_EMP_SSE_HOST=127.0.0.1
MCP_EMP_SSE_PORT=8765

# ── Runtime ───────────────────────────────────────────────────────────────────
MCP_EMP_LOG_LEVEL=INFO
MCP_EMP_READ_ONLY=false

# ── Cache ─────────────────────────────────────────────────────────────────────
MCP_EMP_TASK_TYPE_TTL=600
MCP_EMP_TAG_TTL=300

# ── API-key auth (HTTP only) ──────────────────────────────────────────────────
MCP_EMP_AUTH_ENABLED=false
MCP_EMP_AUTH_DB_PATH=~/.mcp_emp/auth.db
```

---

## Startup exit codes

| Code | Meaning |
|---|---|
| `0` | Clean shutdown |
| `1` | Unhandled exception |
| `77` | `AUTH_MISCONFIGURED` — KC credentials wrong or realm unreachable |

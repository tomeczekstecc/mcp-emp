# 09 — Configuration

How `mcp-emp` is configured at runtime. Locks the keys, defaults,
precedence, and startup-validation rules implied by docs 05–08.

---

## 1. Configuration sources & precedence

```
process env vars                  ← highest priority
   │
   ▼
.env file in CWD (if present)     ← convenience for local dev
   │
   ▼
hard-coded defaults               ← lowest priority
```

- We use **`pydantic-settings`** to parse env + `.env`.
- **No global config file** in `~/.config/mcp-emp/` for P0 — keep it
  simple, env-driven, MCP-host friendly (Claude Desktop / pi / Ollama
  all pass env vars to spawned processes).
- `.env` file is **for local dev only** and is gitignored.

---

## 2. Configuration keys — canonical table

All keys use the `MCP_EMP_` prefix. Required keys cause **fail-fast at
startup** with `AUTH_MISCONFIGURED` (per doc 08 §2.1) printed to stderr.

### 2.1 Connectivity — EMP backend

| Key | Required | Default | Type | Description |
|---|---|---|---|---|
| `MCP_EMP_API_BASE_URL` | yes | — | URL | EMP API root, e.g. `http://localhost:480/api` |
| `MCP_EMP_API_TIMEOUT_SECONDS` | no | `10` | int | httpx request timeout |
| `MCP_EMP_API_VERIFY_TLS` | no | `true` | bool | Set `false` only for dev with self-signed certs |

### 2.2 Authentication — Keycloak

| Key | Required | Default | Type | Description |
|---|---|---|---|---|
| `MCP_EMP_KC_BASE_URL` | yes | — | URL | Keycloak base, e.g. `https://auth-lsi2021-dev.slaskie.pl/auth` |
| `MCP_EMP_KC_REALM` | no | `eMP` | str | Keycloak realm |
| `MCP_EMP_KC_CLIENT_ID` | no | `eMP-REST-API` | str | OAuth client id |
| `MCP_EMP_KC_CLIENT_SECRET` | no | — | secret | Only if the client requires a secret (confidential client) |
| `MCP_EMP_KC_USERNAME` | yes | — | str | The human user's KC username |
| `MCP_EMP_KC_PASSWORD` | yes | — | secret | The human user's KC password |
| `MCP_EMP_KC_TOKEN_SAFETY_MARGIN_SECONDS` | no | `30` | int | Refresh tokens this many seconds before expiry (doc 08 §5) |

### 2.3 Behaviour

| Key | Required | Default | Type | Description |
|---|---|---|---|---|
| `MCP_EMP_READ_ONLY` | no | `false` | bool | Global kill-switch for mutations (doc 08 §8) |
| `MCP_EMP_DICT_CACHE_TTL_SECONDS` | no | `600` | int | Task-types cache TTL (doc 06 tool 2) |
| `MCP_EMP_TAGS_CACHE_TTL_SECONDS` | no | `300` | int | Tags cache TTL (doc 06 tool 3) |
| `MCP_EMP_LIST_DEFAULT_LIMIT` | no | `100` | int | Default `limit` for `list_my_tasks` |
| `MCP_EMP_LIST_MAX_LIMIT` | no | `500` | int | Hard cap on `limit` |
| `MCP_EMP_CONFIRMATION_TTL_SECONDS` | no | `300` | int | Confirmation token lifetime (doc 08 §7) |

### 2.4 Runtime

| Key | Required | Default | Type | Description |
|---|---|---|---|---|
| `MCP_EMP_TRANSPORT` | no | `stdio` | enum | `stdio` or `sse` (doc 12 will lock this) |
| `MCP_EMP_SSE_HOST` | no | `127.0.0.1` | str | Bind host when `transport=sse` |
| `MCP_EMP_SSE_PORT` | no | `8765` | int | Bind port when `transport=sse` |
| `MCP_EMP_LOG_LEVEL` | no | `INFO` | enum | `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `MCP_EMP_TIMEZONE` | no | `Europe/Warsaw` | str | Used only for `overdue` computation; data stays naive (doc 07 §5) |

---

## 3. Required vs optional — what you actually need

**Bare minimum to start mcp-emp:**

```bash
MCP_EMP_API_BASE_URL=http://localhost:480/api
MCP_EMP_KC_BASE_URL=https://auth-lsi2021-dev.slaskie.pl/auth
MCP_EMP_KC_USERNAME=tkowalski
MCP_EMP_KC_PASSWORD=••••••••
```

Everything else has a sensible default.

---

## 4. Internal config model

Single pydantic-settings model. One source of truth for the rest of the
codebase.

```python
# config.py

from pydantic import AnyUrl, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_EMP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # connectivity
    api_base_url: AnyUrl
    api_timeout_seconds: int = 10
    api_verify_tls: bool = True

    # keycloak
    kc_base_url: AnyUrl
    kc_realm: str = "eMP"
    kc_client_id: str = "eMP-REST-API"
    kc_client_secret: SecretStr | None = None
    kc_username: str
    kc_password: SecretStr
    kc_token_safety_margin_seconds: int = 30

    # behaviour
    read_only: bool = False
    dict_cache_ttl_seconds: int = 600
    tags_cache_ttl_seconds: int = 300
    list_default_limit: int = 100
    list_max_limit: int = 500
    confirmation_ttl_seconds: int = 300

    # runtime
    transport: str = "stdio"
    sse_host: str = "127.0.0.1"
    sse_port: int = 8765
    log_level: str = "INFO"
    timezone: str = "Europe/Warsaw"
```

`SecretStr` ensures repr/serialisation cannot accidentally leak the
password into logs or error envelopes (doc 08 §9).

---

## 5. Startup validation checklist

In order. Any failure → log a clear English message to stderr → exit
non-zero. **No partial startup.**

1. **Parse env / `.env`** — pydantic raises on missing required keys.
   On failure: list missing keys + types. Exit code `64` (EX_USAGE).
2. **Validate ranges** — TTLs > 0, port in 1..65535, log level valid.
   Exit code `64`.
3. **Resolve KC well-known config** — `GET ${kc_base_url}/realms/${realm}/.well-known/openid-configuration`.
   On failure → `AUTH_MISCONFIGURED { realm }`. Exit code `69`
   (EX_UNAVAILABLE).
4. **KC login** — Resource Owner Password grant; obtain access +
   refresh + user identity. On failure → `AUTH_MISCONFIGURED { realm,
   client_id }`. Exit code `77` (EX_NOPERM).
5. **EMP health check** — `GET ${api_base_url}/health-check` with the
   token. On failure → `EMP_UNREACHABLE { url }` printed but **do not
   exit** — log a WARN. Rationale: EMP may come up shortly after; tools
   surface real-time errors anyway.
6. **Identity resolution** — parse `roles` from KC token; load EMP
   user join if needed. Store in process-local `IdentityContext`.
7. **Role-gated tool registration** — register only tools the user can
   actually use (doc 06 conventions). Log the set at INFO.
8. **Ready** — start the transport (stdio listener or SSE server).

Total startup time target: < 2 seconds on a warm KC.

---

## 6. Secret handling

| Rule | Enforcement |
|---|---|
| Never serialise `SecretStr` to JSON in any response | `model_dump()` always called on non-secret payloads only; reviewed in tests |
| Never echo passwords / tokens / client_secret in error `details` | EMP client redacts before mapping (doc 08 §3) |
| Never log secrets, even at DEBUG | logging filter scans for `MCP_EMP_KC_PASSWORD`, `MCP_EMP_KC_CLIENT_SECRET`, raw bearer tokens |
| `.env` is gitignored | enforced at repo root |
| Secrets in env vars when launched by an MCP host | host's responsibility; we don't persist what we receive |
| No keyring / OS credential store integration in P0 | per Q3 (in-memory only); revisit in P2 |

---

## 7. Hardcoded vs configurable — and why

| Hardcoded (P0) | Why |
|---|---|
| Status enum values & alias map (doc 07 §8) | Domain constants; changing them is a code change |
| Error codes (doc 08 §2) | Stable contract; new codes require code change |
| Confirmation token format `<op>_<id>_<hex>` | Internal protocol, not user-visible |
| Tool names | Part of the LLM contract |
| KC grant type (`password`) | Decided in Q1 |
| Backoff durations (250ms / 500ms) | Implementation detail; revisit only if metrics demand |

| Configurable | Why |
|---|---|
| All URLs, realms, client ids | Vary between dev / staging / prod |
| Credentials | Per user |
| Cache TTLs | Tunable for load characteristics |
| List limits | Tunable per deployment |
| Read-only mode | Operator safety switch |
| Transport, host, port | Deployment-specific |
| Log level | Debugging |

---

## 8. `.env.example` (committed)

To be created at repo root **at build time**. Sketch:

```bash
# .env.example — copy to .env and fill in.
# .env is gitignored.

# --- EMP backend ---
MCP_EMP_API_BASE_URL=http://localhost:480/api
# MCP_EMP_API_TIMEOUT_SECONDS=10
# MCP_EMP_API_VERIFY_TLS=true

# --- Keycloak ---
MCP_EMP_KC_BASE_URL=https://auth-lsi2021-dev.slaskie.pl/auth
# MCP_EMP_KC_REALM=eMP
# MCP_EMP_KC_CLIENT_ID=eMP-REST-API
# MCP_EMP_KC_CLIENT_SECRET=
MCP_EMP_KC_USERNAME=your.username
MCP_EMP_KC_PASSWORD=changeme

# --- Behaviour ---
# MCP_EMP_READ_ONLY=false
# MCP_EMP_DICT_CACHE_TTL_SECONDS=600
# MCP_EMP_TAGS_CACHE_TTL_SECONDS=300

# --- Runtime ---
# MCP_EMP_TRANSPORT=stdio          # stdio | sse
# MCP_EMP_SSE_HOST=127.0.0.1
# MCP_EMP_SSE_PORT=8765
# MCP_EMP_LOG_LEVEL=INFO
# MCP_EMP_TIMEZONE=Europe/Warsaw
```

---

## 9. Per-environment recipes

### 9.1 Local dev (default)

Stdio transport; EMP on localhost; KC on dev URL; `.env` file in repo
root; INFO logging.

### 9.2 Local dev, "exploration" mode

Add `MCP_EMP_READ_ONLY=true` while testing a new LLM prompt — every
mutation is blocked even if the LLM tries.

### 9.3 Hosted (Claude Desktop, pi)

Env vars passed by the host config. No `.env` file used. Stdio transport.

```jsonc
// Claude Desktop config snippet
{
  "mcpServers": {
    "emp": {
      "command": "python",
      "args": ["-m", "mcp_emp"],
      "env": {
        "MCP_EMP_API_BASE_URL": "http://localhost:480/api",
        "MCP_EMP_KC_BASE_URL": "https://auth-lsi2021-dev.slaskie.pl/auth",
        "MCP_EMP_KC_USERNAME": "...",
        "MCP_EMP_KC_PASSWORD": "..."
      }
    }
  }
}
```

### 9.4 Remote / network (SSE)

`MCP_EMP_TRANSPORT=sse` + `MCP_EMP_SSE_HOST=0.0.0.0` (only if exposed
inside a trusted network). Not recommended for P0 — single-user
deployment assumption (Q2) means stdio is the right default.

---

## 10. What this doc fixes

| Question | Answer |
|---|---|
| Where does config come from? | env + optional `.env`; pydantic-settings (§1) |
| What's the full key list? | §2 |
| What's the bare minimum? | §3 — 4 vars |
| What happens on bad config? | Fail-fast with specific exit codes (§5) |
| How do we keep secrets out of logs? | `SecretStr` + redaction filter (§6) |
| What's hardcoded? | §7 |
| Where's a starter `.env`? | §8 (created at build time) |

---

## 11. Cascades

- **Doc 10 (modules):** implies a `config.py` module with the
  `Settings` class; `IdentityContext` referenced in step 6.
- **Doc 11 (tests):** Settings parses cleanly from a minimal env;
  startup validation tested with fake KC + fake EMP.
- **Doc 12 (runtime):** confirms `MCP_EMP_TRANSPORT` semantics and
  finalises SSE bindings.
- **Doc 13 (roadmap):** `.env.example` is a P0 deliverable.

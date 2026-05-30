# 12 — Runtime & Deployment

How `mcp-emp` actually runs, how clients reach it, and how to operate it.
Locks the transport decision and the lifecycle / install / host
recipes.

---

## 1. Transports — what we support

| Transport | Spec form | Use case | Default? |
|---|---|---|---|
| **stdio** | JSON-RPC over `stdin`/`stdout` | Desktop hosts (Claude Desktop, pi, Cursor, Cline, Continue, Ollama-based) | ✅ yes |
| **Streamable HTTP** | Single endpoint (`POST` + optional SSE upgrade), MCP spec rev 2025-03-26+ | Web / hosted / remote agents (ChatGPT MCP, Claude.ai, n8n) | opt-in |
| **SSE (legacy)** | Two endpoints (`GET /sse`, `POST /messages`) | Older HTTP clients that haven't migrated to Streamable HTTP | exposed alongside HTTP |

Selected via `MCP_EMP_TRANSPORT` (doc 09 §2.4):

```
MCP_EMP_TRANSPORT=stdio     # default
MCP_EMP_TRANSPORT=http      # Starts an HTTP server that speaks BOTH
                            # Streamable HTTP AND legacy SSE at the same time
```

There is **no separate `sse` value** — when HTTP is enabled, SSE is too.
This matches what the official MCP server SDKs do and gives the LLM
host whichever flavour it asks for.

---

## 2. HTTP transport — endpoints

When `MCP_EMP_TRANSPORT=http`:

| Endpoint | Method | Purpose |
|---|---|---|
| `/mcp` | `POST` (JSON-RPC) and optional `GET` (SSE upgrade) | **Streamable HTTP** — modern |
| `/sse` | `GET` (server-sent events) | **Legacy SSE** — server→client stream |
| `/messages` | `POST` (JSON-RPC) | **Legacy SSE** — client→server messages |
| `/healthz` | `GET` | Process liveness probe (no auth, no MCP) |

Bind defaults (doc 09): `127.0.0.1:8765`. **Localhost-only** is the P0
security posture (level A from the earlier decision) — no MCP-layer
auth, relying on OS process isolation.

If a host requires a different port / interface:

```bash
MCP_EMP_TRANSPORT=http
MCP_EMP_SSE_HOST=127.0.0.1     # set to 0.0.0.0 only inside a trusted network
MCP_EMP_SSE_PORT=8765
```

> The env var name kept its `SSE_` prefix from doc 09 for stability; it
> binds the HTTP listener regardless of which sub-protocol the client
> uses. We'll rename to `MCP_EMP_HTTP_*` only if/when SSE is removed
> upstream (no signal of that yet).

**Deferred to P2:** shared-secret auth (`Authorization: Bearer
<MCP_EMP_HTTP_TOKEN>`), config key reserved as
`MCP_EMP_HTTP_SHARED_SECRET`. When set, all `/mcp`, `/sse`, `/messages`
require it; `/healthz` stays open.

---

## 3. Process model

| Aspect | Spec |
|---|---|
| Concurrency | Single asyncio event loop; no threads |
| Lifecycle | One process = one user = one identity (per Q2) |
| Multiple MCP clients on HTTP | Allowed; per-client MCP sessions; all share the one KC identity and one set of caches |
| Stdio + HTTP at once | **Not supported** — one transport per process. Run two processes if you really need both |
| Signal handling | `SIGINT` / `SIGTERM` → graceful shutdown (drain in-flight tool calls; close httpx clients; flush logs) |
| Crash behaviour | Exit non-zero; host is expected to restart |
| State on restart | Nothing persists — tokens, caches, confirmation tokens all in-memory (Q3) |

---

## 4. Startup & shutdown flow

Tying together doc 09 §5 (startup checklist) and doc 10 §7 (entry point):

```
on launch:
   parse settings  →  configure logging  →  KC login  →  identity  →
   EMP healthcheck (WARN only)  →  build ToolContext  →  register tools  →
   start transport listener  →  READY (log "mcp-emp ready, transport=...")

on SIGINT/SIGTERM:
   stop accepting new MCP requests
   await in-flight tool calls (with a 5s deadline)
   close EMP httpx client
   close KC httpx client
   close transport
   flush + close log handlers
   exit 0

on uncaught exception in event loop:
   log ERROR with full traceback
   exit 1   (host restarts)
```

No PID files, no daemonisation; if you want it as a service, use the
init system (systemd / launchd / Windows service wrapper).

---

## 5. Install methods

In recommended order:

| Method | Command | When |
|---|---|---|
| **`uv tool install`** | `uv tool install mcp-emp` | Preferred; isolated venv, latest |
| **`pipx install`** | `pipx install mcp-emp` | Same idea, classic |
| **`pip install -e .` from source** | inside a venv | Dev / debugging |
| **`uv run` ad-hoc** | `uv run python -m mcp_emp` | No-install, repo-local |

After install, the binary entry point is:

```
mcp-emp           # equivalent to:  python -m mcp_emp
```

Defined in `pyproject.toml` as a `[project.scripts]` entry.

---

## 6. Host recipes

Concrete configs for each major host. All use **stdio** unless noted.

### 6.1 Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```jsonc
{
  "mcpServers": {
    "emp": {
      "command": "mcp-emp",
      "env": {
        "MCP_EMP_API_BASE_URL": "http://localhost:480/api",
        "MCP_EMP_KC_BASE_URL":  "https://auth-lsi2021-dev.slaskie.pl/auth",
        "MCP_EMP_KC_USERNAME":  "tkowalski",
        "MCP_EMP_KC_PASSWORD":  "••••••••"
      }
    }
  }
}
```

### 6.2 pi

`~/.pi/config.json` (or whatever pi uses for MCP servers — confirm at
build time):

```jsonc
{
  "mcpServers": {
    "emp": {
      "command": "mcp-emp",
      "env": { /* same as above */ }
    }
  }
}
```

### 6.3 Cursor / Cline / Continue (VS Code-family)

Same shape as Claude Desktop, under each extension's MCP config block.

### 6.4 Ollama-based hosts (e.g. mcp-cli, custom)

```bash
MCP_EMP_API_BASE_URL=http://localhost:480/api \
MCP_EMP_KC_BASE_URL=https://auth-lsi2021-dev.slaskie.pl/auth \
MCP_EMP_KC_USERNAME=tkowalski \
MCP_EMP_KC_PASSWORD=•••••••• \
mcp-emp
```

The host spawns `mcp-emp` and talks stdio over the spawned pipes.

### 6.5 HTTP host (ChatGPT MCP, Claude.ai web, n8n, custom)

Run mcp-emp as a long-lived process:

```bash
MCP_EMP_TRANSPORT=http \
MCP_EMP_SSE_HOST=127.0.0.1 \
MCP_EMP_SSE_PORT=8765 \
MCP_EMP_API_BASE_URL=http://localhost:480/api \
MCP_EMP_KC_BASE_URL=https://auth-lsi2021-dev.slaskie.pl/auth \
MCP_EMP_KC_USERNAME=tkowalski \
MCP_EMP_KC_PASSWORD=•••••••• \
mcp-emp
```

Then point the host at:
- Streamable HTTP-capable: `http://127.0.0.1:8765/mcp`
- Legacy SSE-only: `http://127.0.0.1:8765/sse`

### 6.6 Raw invocation (debugging)

```bash
mcp-emp                      # stdio; hangs waiting for JSON-RPC on stdin
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | mcp-emp
```

For interactive poking: use `npx @modelcontextprotocol/inspector
mcp-emp` — official MCP inspector UI talks stdio to your local server.

---

## 7. Logs & operations

- **Where:** stderr only (stdio transport reserves stdout for MCP
  protocol). HTTP transport may also log to stderr; no file logging in
  P0.
- **Format:** plain text, one record per line, ISO timestamp prefix,
  English. Polish content allowed in messages.
- **Level:** `INFO` by default; `MCP_EMP_LOG_LEVEL=DEBUG` for diagnosis.
- **DEBUG safely:** redaction filter (doc 08 §9 + doc 09 §6) strips
  tokens / passwords / client_secret even at DEBUG, so it's safe to
  share a DEBUG capture.

**Verify it's working** without an LLM in the loop:

```bash
# stdio:
npx @modelcontextprotocol/inspector mcp-emp        # GUI

# http:
curl http://127.0.0.1:8765/healthz                 # → 200 "ok"
curl -X POST http://127.0.0.1:8765/mcp \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

The `health_check` MCP tool (doc 06 tool 1) is the in-band verification
path — once a host is connected, calling it confirms EMP + KC are both
healthy from inside the running process.

---

## 8. Versioning

- **SemVer 2.0** — `MAJOR.MINOR.PATCH`.
- **Stable contract** (changes require **MAJOR**):
  - Tool names
  - Tool input parameter names and types
  - Envelope shape (`{ok, data|error}`)
  - Error `code` values
  - Status / role enum identifiers
- **Backward-compatible additions** (require **MINOR**):
  - New tools
  - New optional parameters
  - New fields in `data` payloads
  - New error codes (existing ones never go away)
- **PATCH**: bug fixes, doc tweaks, internal refactors, dep bumps.

Current version: pre-1.0 (`0.x`). MINOR bumps may include breaking
changes during P0–P2; we lock to SemVer rules at `1.0.0`, which is the
end of P1 by the doc 04 prioritisation.

---

## 9. Upgrade & downgrade

Trivial because **nothing persists**:

| Concern | Behaviour |
|---|---|
| Token state | Re-acquired at startup |
| Caches | Re-warm on first call |
| Confirmation tokens | Lost on restart — LLM gets `CONFIRMATION_INVALID { reason: "unknown" }` and re-previews |
| Config | Re-read from env / `.env` |
| EMP API compatibility | Tested via captured fixtures (doc 11 §4); EMP-side changes show up in test diffs first |

Downgrade rule: any 0.x → 0.x within the same MINOR is safe. Cross-MINOR
downgrades during 0.x may require checking the changelog for
config-key renames.

---

## 10. Observability (P0 minimum)

We deliberately keep this small for P0.

- **Logs:** structured-ish text on stderr (§7). One log line per tool
  call: `tool=<name> ok=<bool> duration_ms=<n> [error_code=<code>]`.
- **`health_check` tool:** in-band liveness/identity (doc 06 tool 1).
- **`/healthz` endpoint** (HTTP only): out-of-band liveness for the
  process itself. Returns `200 ok` always while the loop is running.
- **No metrics, no tracing, no Sentry** in P0. Reserved for P3+ if
  multi-user / hosted ever happens.

---

## 11. What this doc fixes

| Question | Answer |
|---|---|
| Which transports? | stdio (default) + Streamable HTTP + legacy SSE (under same HTTP server) (§1) |
| Stdio + HTTP at the same time? | Not in one process; spin up two (§3) |
| HTTP security in P0? | Localhost-only; shared-secret deferred (§2) |
| Process model? | Single asyncio loop; SIGINT/SIGTERM graceful (§3–4) |
| How do users install? | `uv tool install` / `pipx` / source (§5) |
| Host-specific configs? | §6 |
| Where do logs go? | stderr only; safe at DEBUG (§7) |
| Versioning? | SemVer; stable contract list in §8 |
| Upgrade story? | Restart; nothing persists (§9) |
| What observability? | Minimal: logs + health_check + /healthz (§10) |

---

## 12. Cascades

- **Doc 13 (roadmap):** P0 ships **stdio only**; HTTP transport is a
  P1 deliverable (small effort, but not on the UC-1/2/3 critical path).
- **Doc 14 (risks):** transport churn in the MCP spec is a real risk;
  using the official SDK's transport classes is the mitigation.

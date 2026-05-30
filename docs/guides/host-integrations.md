# Host Integration Guide

How to connect mcp-emp to every supported LLM host.

> **Before you start:** the server uses `python.exe -m mcp_emp` from the
> project venv. This avoids Windows file-locking issues that occur when the
> `.exe` script is held by another process.

---

## Common env block

Every host needs the same environment variables. Fill in your values once
and copy the block to each config:

```
MCP_EMP_API_BASE_URL = https://emp-api.slaskie.pl/api
MCP_EMP_KC_BASE_URL  = https://emp-auth.slaskie.pl
MCP_EMP_KC_REALM     = eMP
MCP_EMP_KC_CLIENT_ID = eMP
MCP_EMP_KC_USERNAME  = your_username
MCP_EMP_KC_PASSWORD  = your_password
MCP_EMP_KC_UNIT      = CI
MCP_EMP_KC_TEAM      = CI-PRS
MCP_EMP_LOG_LEVEL    = INFO

# Optional — direct DB access for backdate_task tool
MCP_EMP_DB_ENABLED   = true
MCP_EMP_DB_HOST      = https://emp-db.slaskie.pl
MCP_EMP_DB_USER      = emp
MCP_EMP_DB_PASS      = your_db_password
MCP_EMP_DB_DATABASE  = emp
```

> **`MCP_EMP_DB_ENABLED`**: set to `false` (or omit) to hide the
> `backdate_task` tool entirely. DB credentials are only needed when
> `DB_ENABLED=true`.

---

## Claude Desktop

**Config file:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "emp": {
      "command": "C:\\dev\\python\\mcp_emp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_emp"],
      "env": {
        "MCP_EMP_API_BASE_URL": "https://emp-api.slaskie.pl/api",
        "MCP_EMP_KC_BASE_URL":  "https://emp-auth.slaskie.pl",
        "MCP_EMP_KC_REALM":     "eMP",
        "MCP_EMP_KC_CLIENT_ID": "eMP",
        "MCP_EMP_KC_USERNAME":  "your_username",
        "MCP_EMP_KC_PASSWORD":  "your_password",
        "MCP_EMP_KC_UNIT":      "CI",
        "MCP_EMP_KC_TEAM":      "CI-PRS",
        "MCP_EMP_LOG_LEVEL":    "INFO",
        "MCP_EMP_DB_ENABLED":   "true",
        "MCP_EMP_DB_HOST":      "https://emp-db.slaskie.pl",
        "MCP_EMP_DB_USER":      "emp",
        "MCP_EMP_DB_PASS":      "your_db_password",
        "MCP_EMP_DB_DATABASE":  "emp"
      }
    }
  }
}
```

**After saving:** fully quit and relaunch Claude Desktop.

---

## Claude Code (CLI)

**Config file:** `~/.claude.json`

Add or update the `mcpServers` key:

```json
{
  "mcpServers": {
    "emp": {
      "command": "C:\\dev\\python\\mcp_emp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_emp"],
      "env": {
        "MCP_EMP_API_BASE_URL": "https://emp-api.slaskie.pl/api",
        "MCP_EMP_KC_BASE_URL":  "https://emp-auth.slaskie.pl",
        "MCP_EMP_KC_REALM":     "eMP",
        "MCP_EMP_KC_CLIENT_ID": "eMP",
        "MCP_EMP_KC_USERNAME":  "your_username",
        "MCP_EMP_KC_PASSWORD":  "your_password",
        "MCP_EMP_KC_UNIT":      "CI",
        "MCP_EMP_KC_TEAM":      "CI-PRS",
        "MCP_EMP_LOG_LEVEL":    "INFO",
        "MCP_EMP_DB_ENABLED":   "true",
        "MCP_EMP_DB_HOST":      "https://emp-db.slaskie.pl",
        "MCP_EMP_DB_USER":      "emp",
        "MCP_EMP_DB_PASS":      "your_db_password",
        "MCP_EMP_DB_DATABASE":  "emp"
      }
    }
  }
}
```

**Verify:**
```bash
claude mcp list          # should show "emp"
claude mcp get emp       # shows connection details
```

---

## Cursor

**Config file:** `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "emp": {
      "command": "C:\\dev\\python\\mcp_emp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_emp"],
      "env": {
        "MCP_EMP_API_BASE_URL": "https://emp-api.slaskie.pl/api",
        "MCP_EMP_KC_BASE_URL":  "https://emp-auth.slaskie.pl",
        "MCP_EMP_KC_REALM":     "eMP",
        "MCP_EMP_KC_CLIENT_ID": "eMP",
        "MCP_EMP_KC_USERNAME":  "your_username",
        "MCP_EMP_KC_PASSWORD":  "your_password",
        "MCP_EMP_KC_UNIT":      "CI",
        "MCP_EMP_KC_TEAM":      "CI-PRS",
        "MCP_EMP_LOG_LEVEL":    "INFO",
        "MCP_EMP_DB_ENABLED":   "true",
        "MCP_EMP_DB_HOST":      "https://emp-db.slaskie.pl",
        "MCP_EMP_DB_USER":      "emp",
        "MCP_EMP_DB_PASS":      "your_db_password",
        "MCP_EMP_DB_DATABASE":  "emp"
      }
    }
  }
}
```

**After saving:** reload Cursor (`Ctrl+Shift+P` → *Reload Window*) or
restart the app. The `emp` server appears in
*Cursor Settings → MCP*.

> **Note for pi users:** pi imports MCP servers from Cursor's `mcp.json`
> automatically — configuring Cursor is enough to enable mcp-emp in pi too.

---

## pi

pi auto-imports from Cursor's `~/.cursor/mcp.json`. No separate config
needed if Cursor is already configured.

If you want a **project-local** override (only active in one repo), add
`.pi/settings.json` at the project root:

```json
{
  "mcpServers": {
    "emp": {
      "command": "C:\\dev\\python\\mcp_emp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_emp"],
      "env": { "...same env block..." }
    }
  }
}
```

---

## OpenAI Codex CLI

**Config file:** `~/.codex/config.toml`

```toml
[mcp_servers.emp]
command = 'C:\dev\python\mcp_emp\.venv\Scripts\python.exe'
args    = ["-m", "mcp_emp"]

  [mcp_servers.emp.env]
  MCP_EMP_API_BASE_URL = "https://emp-api.slaskie.pl/api"
  MCP_EMP_KC_BASE_URL  = "https://emp-auth.slaskie.pl"
  MCP_EMP_KC_REALM     = "eMP"
  MCP_EMP_KC_CLIENT_ID = "eMP"
  MCP_EMP_KC_USERNAME  = "your_username"
  MCP_EMP_KC_PASSWORD  = "your_password"
  MCP_EMP_KC_UNIT      = "CI"
  MCP_EMP_KC_TEAM      = "CI-PRS"
  MCP_EMP_LOG_LEVEL    = "INFO"
  MCP_EMP_DB_ENABLED   = "true"
  MCP_EMP_DB_HOST      = "https://emp-db.slaskie.pl"
  MCP_EMP_DB_USER      = "emp"
  MCP_EMP_DB_PASS      = "your_db_password"
  MCP_EMP_DB_DATABASE  = "emp"
```

---

## Cline / Continue (VS Code extensions)

Both extensions use the VS Code MCP settings. Open
*Settings → Extensions → Cline / Continue → MCP Servers* and add:

```json
{
  "name": "emp",
  "command": "C:\\dev\\python\\mcp_emp\\.venv\\Scripts\\python.exe",
  "args": ["-m", "mcp_emp"],
  "env": { "...same env block..." }
}
```

Or edit `.vscode/settings.json` directly:

```json
{
  "cline.mcpServers": {
    "emp": {
      "command": "C:\\dev\\python\\mcp_emp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_emp"],
      "env": { "...same env block..." }
    }
  }
}
```

---

## HTTP hosts (n8n, ChatGPT MCP, Claude.ai, custom agents)

For web-based or remote agents that cannot spawn a local process, run
mcp-emp as a long-lived HTTP server:

```bash
# Terminal / systemd / Docker
MCP_EMP_TRANSPORT=http \
MCP_EMP_AUTH_ENABLED=true \
MCP_EMP_SSE_HOST=127.0.0.1 \
MCP_EMP_SSE_PORT=8765 \
C:\dev\python\mcp_emp\.venv\Scripts\python.exe -m mcp_emp
```

Then initialise API keys:

```bash
C:\dev\python\mcp_emp\.venv\Scripts\python.exe -m mcp_emp auth init
C:\dev\python\mcp_emp\.venv\Scripts\python.exe -m mcp_emp auth add-user alice --superuser --force
# → API key (shown once): emp_alice_...
```

Point the host at one of these endpoints:

| Protocol | Endpoint | Notes |
|---|---|---|
| Streamable HTTP (modern) | `http://127.0.0.1:8765/mcp` | Preferred for all new MCP clients |
| Legacy SSE | `http://127.0.0.1:8765/sse` | For older MCP clients |
| Health probe | `http://127.0.0.1:8765/healthz` | No auth required |

All requests to `/mcp` and `/sse` must include:
```
Authorization: Bearer emp_alice_<32hex>
```

See [auth-management.md](auth-management.md) for full key management docs.

---

## MCP Inspector (testing / debugging)

```bash
# stdio
npx @modelcontextprotocol/inspector \
  C:\dev\python\mcp_emp\.venv\Scripts\python.exe \
  -m mcp_emp

# HTTP (if server already running)
npx @modelcontextprotocol/inspector
# → set URL to http://127.0.0.1:8765/mcp in the UI
```

Open the printed URL in your browser → **Tools** tab → call `health_check`.

---

## macOS / Linux paths

Replace `C:\dev\python\mcp_emp\.venv\Scripts\python.exe` with:

```bash
/path/to/mcp_emp/.venv/bin/python
```

The module invocation (`-m mcp_emp`) is identical on all platforms.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `mcp-emp.exe` locked by another process | Use `python.exe -m mcp_emp` instead of the script |
| `uv` not found in host PATH | Use full path: `C:\Users\<you>\.local\bin\uv.exe` |
| 500 errors from EMP API | KC token missing `team`/`unit` claims → add `MCP_EMP_KC_UNIT` / `MCP_EMP_KC_TEAM` |
| `backdate_task` not in tool list | Set `MCP_EMP_DB_ENABLED=true` and add DB credentials |
| HTTP auth 401 | Run `mcp-emp auth list-users` — if empty, run `auth add-user` first |

For more: [troubleshooting.md](troubleshooting.md)

# Quick Start Guide

Get mcp-emp running in 5 minutes.

---

## 1. Install

```bash
# Recommended — isolated environment, binary on PATH
uv tool install mcp-emp

# Alternative
pipx install mcp-emp

# Development / from source
git clone <repo>
cd mcp_emp
uv sync
uv pip install -e .
```

Verify installation:

```bash
mcp-emp --help        # should print usage
mcp-emp auth --help   # auth sub-commands
```

---

## 2. Configure

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Minimum `.env`:

```env
MCP_EMP_API_BASE_URL=https://emp-api.slaskie.pl/api
MCP_EMP_KC_BASE_URL=https://emp-auth.slaskie.pl
MCP_EMP_KC_REALM=eMP
MCP_EMP_KC_CLIENT_ID=eMP
MCP_EMP_KC_USERNAME=your_username
MCP_EMP_KC_PASSWORD=your_password
```

> **Tip:** If your Keycloak token does not include `team`/`unit` claims,
> add fallbacks:
> ```env
> MCP_EMP_KC_UNIT=CI
> MCP_EMP_KC_TEAM=CI-PRS
> ```

---

## 3. Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run mcp-emp
```

Open the printed URL (e.g. `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=...`).

In the Inspector UI:
1. **Transport** → `STDIO`
2. **Command** → `uv`
3. **Arguments** → `run mcp-emp`
4. Click **Connect**

You should see startup logs in the terminal:
```
Authenticated as your_username roles=[...]
EMP API reachable at https://emp-api.slaskie.pl/api
mcp-emp ready, transport=stdio
```

Then call `health_check` in the Tools tab — it should return:

```json
{
  "emp_api": "reachable",
  "auth": "valid",
  "user": { "username": "your_username", "unit": "CI", "team": "CI-PRS", "roles": [...] }
}
```

---

## 4. Connect your LLM host

See **[host-integrations.md](host-integrations.md)** for complete,
copy-paste configs for every supported host. Quick summary below.

### Claude Desktop

`%APPDATA%\Claude\claude_desktop_config.json` (Windows)  
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "emp": {
      "command": "mcp-emp",
      "env": {
        "MCP_EMP_API_BASE_URL": "https://emp-api.slaskie.pl/api",
        "MCP_EMP_KC_BASE_URL":  "https://emp-auth.slaskie.pl",
        "MCP_EMP_KC_REALM":     "eMP",
        "MCP_EMP_KC_CLIENT_ID": "eMP",
        "MCP_EMP_KC_USERNAME":  "your_username",
        "MCP_EMP_KC_PASSWORD":  "your_password",
        "MCP_EMP_KC_UNIT":      "CI",
        "MCP_EMP_KC_TEAM":      "CI-PRS"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

### pi

`~/.pi/config.json`:

```json
{
  "mcpServers": {
    "emp": {
      "command": "mcp-emp",
      "env": { "...same as above..." }
    }
  }
}
```

### Cursor / Cline / Continue

Same JSON shape as Claude Desktop, under each extension's MCP server config.

### HTTP-capable host (n8n, ChatGPT MCP, Claude.ai)

Run mcp-emp as a long-lived HTTP server:

```bash
MCP_EMP_TRANSPORT=http \
MCP_EMP_AUTH_ENABLED=true \
mcp-emp
```

Then point your host at:
- **Streamable HTTP** (modern): `http://127.0.0.1:8765/mcp`
- **Legacy SSE**: `http://127.0.0.1:8765/sse`

Set `Authorization: Bearer <your_api_key>` header.

See [auth-management.md](auth-management.md) for creating API keys.

---

## 5. First tasks

Once connected, try these prompts:

```
"Show me my tasks for today"
→ calls get_daily_stats + list_my_tasks

"Log a meeting I just had about the DB migration, 45 minutes"
→ calls list_task_types(search="spotkanie"), then add_my_task(dry_run=true)

"Mark task 134343 as done"
→ calls get_task, then complete_task(dry_run=true), then complete_task

"What are my point totals this cycle?"
→ calls get_cycle_stats
```

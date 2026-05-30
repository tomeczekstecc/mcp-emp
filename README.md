# mcp-emp

**MCP server for Elektroniczna Miara Pracy (EMP)**

Bridges LLM clients (Claude Desktop, pi, Cursor, Cline, n8n, …) to the EMP
work-record backend via the Model Context Protocol.  Authenticates as a single
EMP user through Keycloak and exposes 13 tools covering task CRUD, reference
data, statistics, and user info.

---

## Features

| Area | Tools |
|---|---|
| **Reference data** | `list_task_types`, `list_tags` |
| **Tasks — read** | `list_my_tasks`, `get_task`, `list_team_tasks` |
| **Tasks — write** | `add_my_task`, `complete_task`, `edit_task`, `delete_task`, `bulk_create_tasks`, `bulk_delete_tasks` |
| **Tasks — lifecycle** | `start_task`, `reject_task`, `withdraw_task` |
| **User** | `get_my_profile`, `get_my_permissions`, `list_users` |
| **Statistics** | `get_cycle_stats`, `get_daily_stats`, `get_team_cycle_stats` |
| **Server health** | `health_check` |
| **Templates** | `list_templates`, `apply_template` |

Key behaviours:
- **Dry-run** on all mutating tools — preview before committing.
- **Two-step confirmation** on destructive operations (`delete_task`).
- **Pre-flight validation** against cached EMP dictionaries before every write.
- **Structured error codes** — LLMs can branch on `TASK_NOT_FOUND`,
  `INVALID_TRANSITION`, `VALIDATION_FAILED`, etc.
- **Cached dictionaries** — task types cached 10 min, tags 5 min.

---

## Quick start

```bash
# 1. Install
pip install mcp-emp          # or: uv tool install mcp-emp

# 2. Configure (copy and fill in your values)
cp .env.example .env
$EDITOR .env

# 3. Verify it works
npx @modelcontextprotocol/inspector mcp-emp
# → open http://localhost:6274, call health_check
```

See **[docs/guides/quick-start.md](docs/guides/quick-start.md)** for step-by-step
instructions and **[docs/guides/host-integrations.md](docs/guides/host-integrations.md)**
for every supported host (Claude Desktop, Claude Code, Cursor, pi, Codex, n8n, HTTP).

---

## Configuration

All settings are `MCP_EMP_*` environment variables (or `.env` file).
See **[docs/guides/configuration.md](docs/guides/configuration.md)** for the
full reference.

Minimum required:

```env
MCP_EMP_API_BASE_URL=https://emp-api.slaskie.pl/api
MCP_EMP_KC_BASE_URL=https://emp-auth.slaskie.pl
MCP_EMP_KC_REALM=eMP
MCP_EMP_KC_CLIENT_ID=eMP
MCP_EMP_KC_USERNAME=your_username
MCP_EMP_KC_PASSWORD=your_password
```

---

## Tools reference

See **[docs/guides/tools-reference.md](docs/guides/tools-reference.md)** for every
tool with parameters, return shapes, and examples.

---

## HTTP transport & API-key auth

For web-based MCP hosts (ChatGPT, n8n, custom agents):

```env
MCP_EMP_TRANSPORT=http
MCP_EMP_AUTH_ENABLED=true
```

Manage API keys with the built-in CLI:

```bash
mcp-emp auth init
mcp-emp auth add-user alice --superuser --force
mcp-emp auth list-users
```

See **[docs/guides/auth-management.md](docs/guides/auth-management.md)** for the
complete auth guide.

---

## Troubleshooting

See **[docs/guides/troubleshooting.md](docs/guides/troubleshooting.md)**.

---

## Project docs

Planning documents (architecture, ADRs, risk register) live in
[docs/](docs/).  Start with [docs/README.md](docs/README.md).

---

## Requirements

- Python ≥ 3.12
- EMP backend + Keycloak realm accessible
- `uv` or `pip` for installation

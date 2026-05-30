# Domain-Driven Design Patterns (Lite) — Python / MCP

This project uses a pragmatic, lite DDD approach focused on clear domain boundaries and consistent file organization — not full tactical DDD with aggregates, repositories, or domain events.

## Core Principle

**Organize code by business domain, not by technical layer.**

Instead of:
```
mcp_emp/
  tools.py        # every tool, every domain
  clients.py      # every httpx call
  models.py       # every type
  mappers.py      # every transform
```

We use:
```
mcp_emp/
  domains/
    employees/
    tickets/
    timesheets/
```

---

## Domain Locations

| Location | Purpose | Example |
|----------|---------|---------|
| `mcp_emp/domains/<domain>/` | Domain package (contracts, client, mapper, tools) | `mcp_emp/domains/employees/` |
| `mcp_emp/core/` | Cross-cutting infrastructure (http, config, logging) | `mcp_emp/core/http.py` |
| `mcp_emp/server.py` | Server bootstrap + tool registration entry point | — |
| `tests/<domain>/` | Domain-specific tests mirroring the package | `tests/employees/test_client.py` |

---

## Domain Package Structure

Each domain in `mcp_emp/domains/<domain>/` follows this structure:

```
mcp_emp/domains/employees/
├── __init__.py
├── contract.py     # Pydantic: Payload (upstream), Model (MCP-facing), Input/Params
├── mapper.py       # map_payload_to_model(...)
├── client.py       # async httpx calls against the upstream API
├── tools.py        # MCP tool registration (@server.tool decorators)
├── errors.py       # Domain exceptions (optional, when the surface grows)
```

### File Responsibilities

#### `contract.py` — Domain Types

```python
from datetime import datetime
from pydantic import BaseModel, Field


# Raw upstream payload (matches API response, snake_case is fine here)
class EmployeePayload(BaseModel):
    id: str
    full_name: str
    status: str
    created_at: str  # raw ISO string from upstream
    updated_at: str


# MCP-facing model (clean, well-typed)
class Employee(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


# Input types for tools
class CreateEmployeeInput(BaseModel):
    name: str = Field(..., min_length=1)
```

#### `mapper.py` — Payload → Model

```python
from datetime import datetime
from .contract import Employee, EmployeePayload


def map_employee(payload: EmployeePayload) -> Employee:
    return Employee(
        id=payload.id,
        name=payload.full_name,
        status=payload.status,
        created_at=datetime.fromisoformat(payload.created_at),
        updated_at=datetime.fromisoformat(payload.updated_at),
    )
```

#### `client.py` — Async HTTP Calls

```python
from mcp_emp.core.http import get_client
from .contract import Employee, EmployeePayload
from .mapper import map_employee


async def fetch_employee(employee_id: str) -> Employee:
    client = get_client()
    response = await client.get(f"/employees/{employee_id}")
    response.raise_for_status()
    payload = EmployeePayload.model_validate(response.json())
    return map_employee(payload)
```

#### `tools.py` — MCP Tool Registration

```python
from mcp.server.fastmcp import FastMCP
from .client import fetch_employee
from .contract import Employee


def register(server: FastMCP) -> None:
    @server.tool()
    async def get_employee(employee_id: str) -> Employee:
        """Fetch a single employee by ID.

        Args:
            employee_id: The upstream employee identifier.

        Returns:
            The Employee record.
        """
        return await fetch_employee(employee_id)
```

---

## Core / Infrastructure (`mcp_emp/core/`)

Cross-cutting code that is not domain-specific:

```
mcp_emp/core/
├── http.py       # shared httpx.AsyncClient + lifespan management
├── config.py     # Settings (Pydantic BaseSettings) loaded once
├── logging.py    # logging configuration
├── errors.py     # base exception classes (UpstreamUnavailable, etc.)
```

---

## CQRS Lite

We follow a basic read/write separation inside each domain client:

| Function prefix | Purpose | Side effects |
|-----------------|---------|--------------|
| `fetch_*`, `get_*`, `list_*` | Read | None |
| `create_*`, `update_*`, `delete_*`, `submit_*` | Write | Mutates upstream state |

**Rules:**
- Read functions must not mutate upstream state.
- Write functions must not be called from read functions.
- Share pure code (mappers, contracts) — not operations.

When the write surface grows, split `client.py` into `queries.py` + `commands.py`.

---

## When to Create a New Domain

Create a new domain folder when:

1. **New bounded context** — distinct upstream capability (e.g., `employees`, `timesheets`, `tickets`).
2. **Own upstream endpoints** — the feature talks to its own set of API routes.
3. **Reusable across tools** — multiple tools consume the same models.

**Don't create a domain for:**
- A one-off helper (keep it in the file that uses it).
- A single utility function (keep in `mcp_emp/core/` or inline).
- Speculative future work.

---

## Naming Conventions

| Concept | Convention | Example |
|---------|------------|---------|
| Package / domain folder | `snake_case` | `employees`, `time_sheets` |
| Class names | `PascalCase` | `Employee`, `EmployeePayload` |
| Payload suffix | `*Payload` | `EmployeePayload` (raw upstream) |
| Input suffix | `*Input` | `CreateEmployeeInput` |
| Params suffix | `*Params` | `EmployeeListParams` |
| Mapper functions | `map_*` | `map_employee`, `map_employee_list` |
| Read functions | `fetch_*` / `get_*` / `list_*` | `fetch_employee` |
| Write functions | `create_*` / `update_*` / `delete_*` | `create_employee` |
| MCP tools | `verb_noun` | `get_employee`, `list_employees` |

---

## What We Don't Use (Full DDD)

This project intentionally skips these tactical DDD patterns:

| Pattern | Why Not |
|---------|---------|
| Aggregates | We don't own persistence. |
| Repositories | `client.py` async functions are simpler. |
| Domain Events | No event-driven architecture needed. |
| Value Objects | Pydantic models + type hints suffice. |
| Domain Services | Plain async functions in domain folders work. |
| Ubiquitous Language glossary | Capture terms in `CONTEXT.md` only when needed. |

---

## Quick Reference

```
# Full domain
mcp_emp/domains/employees/
  __init__.py
  contract.py     # Payload, Model, Input types
  mapper.py       # Payload → Model
  client.py       # fetch_* / create_* async functions
  tools.py        # @server.tool registrations
  errors.py       # (optional) domain exceptions

# Cross-cutting infrastructure
mcp_emp/core/
  http.py
  config.py
  logging.py

# Server entry
mcp_emp/server.py    # builds FastMCP, calls each domain's register()
main.py              # thin runner: imports server, starts transport

# Tests
tests/employees/
  test_client.py
  test_mapper.py
  test_tools.py
```

---

## Checklist for New Domains

- [ ] Create `mcp_emp/domains/<domain>/contract.py` with Payload and Model Pydantic types
- [ ] Create `mapper.py` for `Payload → Model` translation
- [ ] Create `client.py` with async `fetch_*` (and `create_*` if needed) functions
- [ ] Create `tools.py` with a `register(server)` function
- [ ] Wire `register()` into `mcp_emp/server.py`
- [ ] Add tests under `tests/<domain>/`
- [ ] Document upstream endpoints in `docs/<domain>.md` if non-trivial

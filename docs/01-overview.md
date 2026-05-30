# 01 — Overview

## What `mcp-emp` is

A **Python MCP (Model Context Protocol) server** that lets an AI agent
(pi, Claude, etc.) operate on tasks in the **EMP** system on behalf of a user.

It is a **bridge**: MCP tools in → EMP REST API calls out.

```
AI agent (pi / Claude)
       │
       │  MCP (stdio or SSE)
       ▼
   mcp-emp                       ← this project (Python)
       │
       │  httpx + Bearer JWT
       ▼
   EMP Laravel API               ← http://localhost:480/api
       │
       ▼
   PostgreSQL  +  Keycloak  +  RabbitMQ
```

---

## What EMP is

**Elektroniczna Miara Pracy** — "Electronic Work Measure".

A Laravel PHP REST API used inside an organisation (domain `slaskie.pl`,
likely Śląski Urząd Wojewódzki / regional government) to track employee
work as `zadania` (tasks) with a scoring system, lifecycle, and statistics.

### Stack

| Layer | Tech |
|---|---|
| Framework | Laravel (PHP), CQRS (Commands + Queries) |
| Database | PostgreSQL (`emp-dev` on `ci-prs-db.slaskie.pl:5432`) |
| Auth | Keycloak JWT (`auth-lsi2021-dev.slaskie.pl`, realm `eMP`) |
| Queue | RabbitMQ |
| API base | `http://localhost:480/api` (dev) |
| API style | REST, JSON, Polish field/route names |

---

## Core domain: `Rejestr` (task register)

A `zadanie` has:

| Field | Meaning |
|---|---|
| `id` | task ID |
| `dotyczy` | what it's about |
| `status` | lifecycle state |
| `slownik_typ_zadania_id` | task type (dictionary) |
| `created_user_id` | author |
| `assigned_user_id` | assignee |
| `data_zlecenia` | ordered date |
| `data_termin` | deadline |
| `data_rozpoczecia` | start date |
| `data_zakonczenia` | completion date |
| `nr_cyklu` | work cycle number |
| `punkty_domyslne` / `_przelozony` / `_pracownik` | scoring |
| `waga` / `punkty_wagi` | weight × score |
| `ilosc` / `czas` | quantity / time |
| `tags` | tag list |

### Status lifecycle

```
[create] utworz / utworzMoje
              │
              ▼
          W_EDYCJI ───────── usun (only here)
              │
              │ przekaz (kierownik)
              ▼
        (list) ── przydziel (kierownik)
              │
              │ realizuj
              ▼
        REALIZOWANE
              │
              │ zakoncz
              ├──────────── DO_OCENY (if type requires evaluation)
              │                   │
              │                   │ zakoncz (manager scores)
              ▼                   ▼
        ZAKOŃCZONE ◄──────────────┘

(any) ── odrzuc  → ODRZUCONE
(any) ── wycofaj → WYCOFANE
```

### Roles

| Role | Capabilities |
|---|---|
| `pracownik` | own tasks: realizuj, zakoncz, odrzuc, utworzMoje |
| `kierownik` | + utworz, przekaz, przydziel, klonuj, team stats |
| `dyrektor` | broader team scope |
| `zarzad` | read-only stats, aggregated |

---

## Three target scenarios

1. **Task CRUD** — add, mark done, delete obsolete zadania
2. **Self & team analysis** — fetch own + team stats, draw conclusions
3. **Work automation** — analyse current work, auto-suggest/create tasks

---

## What exists today

| | Status |
|---|---|
| EMP Laravel API | ✅ running |
| `mcp-emp` repo scaffolding | ✅ `pyproject.toml`, deps installed |
| `main.py` | 🟡 stub (`print("Hello from mcp-emp!")`) |
| MCP tools | ❌ none |
| Auth client | ❌ none |
| Docs | 🟡 this folder, in progress |

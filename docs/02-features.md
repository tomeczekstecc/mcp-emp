# 02 — Feature Catalog

Features are grouped into 5 capability areas. Each row maps to one or more
[use cases](03-use-cases.md) and (where applicable) an EMP endpoint.

---

## Area A — Connectivity & Auth (foundation)

| # | Feature | Description |
|---|---|---|
| A1 | **Keycloak login** | Authenticate against `auth-lsi2021-dev.slaskie.pl` using `eMP-REST-API` client, obtain JWT, refresh on expiry. |
| A2 | **EMP HTTP client** | Thin `httpx`-based wrapper that injects `Authorization: Bearer <jwt>` on every call to `http://localhost:480/api`. |
| A3 | **Identity context** | Know "who am I" — user id, role (pracownik / kierownik / dyrektor / zarząd), team. Drives tool availability and default filters. |
| A4 | **Config / secrets** | Load `.env`-style config (EMP base URL, Keycloak realm, client id/secret, user credentials). |
| A5 | **Health check** | Verify EMP reachable + token valid before exposing tools. |

---

## Area B — Task CRUD (Scenario 1)

| # | Feature | Description | EMP endpoint |
|---|---|---|---|
| B1 | **Dodaj własne zadanie** | Create my own task (`utworzMoje`). | `POST /rejestr/moje` |
| B2 | **Dodaj zadanie (kierownik)** | Manager creates a team task. | `POST /rejestr/kierownik` |
| B3 | **Edytuj zadanie** | Update fields while `status = W_EDYCJI`. | `PUT /rejestr` |
| B4 | **Rozpocznij realizację** | Mark task as `REALIZOWANE`. | `PUT /rejestr/realizuj` |
| B5 | **Zakończ zadanie** | Mark done — moves to `ZAKOŃCZONE` or `DO_OCENY`. | `PUT /rejestr/zakoncz` |
| B6 | **Odrzuć zadanie** | Reject with justification. | `PUT /rejestr/odrzuc` |
| B7 | **Wycofaj zadanie** | Withdraw a task. | `PUT /rejestr/wycofaj` |
| B8 | **Usuń zadanie** | Delete (only `W_EDYCJI` allowed). | `DELETE /rejestr/{id}` |
| B9 | **Pobierz zadanie po ID** | One task in detail. | `GET /rejestr/{id}` |
| B10 | **Lista moich zadań (aktywnych)** | All my tasks excluding `ZAKOŃCZONE`. | `GET /rejestr/lista/moje` |
| B11 | **Lista moich zadań (wszystkie)** | Incl. completed. | `GET /rejestr/lista/moje-wszystkie` |
| B12 | **Pobierz słowniki** | List task types, tags, teams (name ↔ id). | `GET /rejestr/slowniki/{slownik}`, `GET /rejestr/tag` |
| B13 | **Historia zadania** | Audit trail. | `GET /rejestr/kierownik/historia/{id}` |

---

## Area C — Team & Self Analysis (Scenario 2)

| # | Feature | Description | EMP endpoint |
|---|---|---|---|
| C1 | **Moje statystyki cyklu** | Points / count / time, current cycle. | `GET /rejestr/stat/pracownicy` |
| C2 | **Statystyki zespołu (kierownik)** | Team workload per employee. | `GET /rejestr/kierownik/stat/pracownicy` |
| C3 | **Statystyki cykli** | Multi-cycle trend. | `GET /rejestr/stat/cykle` |
| C4 | **Statystyki zadań** | Distribution by task type. | `GET /rejestr/stat/zadania` |
| C5 | **Statystyki dzienne** | Day-by-day activity. | `GET /rejestr/stat/dzienny` |
| C6 | **Raport dzienny** | Formatted daily summary. | `GET /rejestr/stat/dzienny-raport` |
| C7 | **Porównanie ja vs. zespół** | Composite: C1 + C2 → structured comparison. | (client-side) |
| C8 | **Wykrywanie problemów** | Composite: overdue, idle, overloaded peers. | (client-side) |

---

## Area D — Work Automation (Scenario 3)

| # | Feature | Description | Notes |
|---|---|---|---|
| D1 | **Kontekst bieżącej pracy** | `REALIZOWANE` + recent `ZAKOŃCZONE` + active tags. | composes B10 + B11 |
| D2 | **Sugestia zadań na bazie kontekstu** | LLM proposes new zadania from current work / patterns. | LLM-side; we supply data + preview |
| D3 | **Bulk create zadań** | Add many tasks in one batch with dry-run preview. | calls B1/B2 N times |
| D4 | **Szablony zadań** | Pre-filled templates for recurring types. | local config or `pobierzWzor` |
| D5 | **Recurring task detection** | Find weekly/monthly repeats, pre-create next. | client-side analysis |
| D6 | **Auto-tagging** | Suggest tags from `dotyczy` + history. | LLM + B12 |
| D7 | **Auto-zakończenie sugestie** | Identify stale `REALIZOWANE` that look done. | composes B10 + heuristics |

---

## Area E — Safety & UX (cross-cutting)

| # | Feature | Description |
|---|---|---|
| E1 | **Dry-run mode** | Mutating tools accept `dry_run=true`. |
| E2 | **Confirmation envelope** | Destructive ops return a confirmation token the agent must echo. |
| E3 | **PL ↔ EN aliasing** | Tool params accept Polish *and* English names. |
| E4 | **Error translation** | Map EMP exceptions to clear LLM-friendly messages. |
| E5 | **Caching of słowniki** | Cache rarely-changing lookups (types, tags, teams). |
| E6 | **Read-only mode flag** | Global kill-switch for all mutations. |

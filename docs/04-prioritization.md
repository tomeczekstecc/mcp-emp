# 04 — Prioritization

Four tiers from MVP to nice-to-have. Driven by:
- **Scenario coverage** — P0 must fully deliver scenario 1.
- **Dependency order** — Area A is prerequisite for everything.
- **User value per unit of work** — CRUD > simple stats > composite stats > automation.

---

## P0 — MVP (Scenario 1 working end-to-end)

| Item | Why |
|---|---|
| A1–A5 | Nothing works without auth + client + identity |
| B1 (dodaj_moje) | Core "add" |
| B5 (zakoncz) | Core "mark done" |
| B8 (usun) | Core "delete obsolete" |
| B9 (pobierz_po_id) | Needed to verify after writes |
| B10 (lista_moje) | Needed to find tasks to act on |
| B12 (slowniki) | Needed to translate names ↔ ids |
| E1 (dry-run) | Safety from day one |
| E2 (confirmation) | Safety for destructive ops |

**Use cases delivered:** UC-1, UC-2, UC-3.

---

## P1 — Full CRUD + basic analysis (Scenario 2 partial)

| Item | Why |
|---|---|
| B2, B3, B4, B6, B7 | Complete the lifecycle |
| B11 (lista_wszystkie) | Needed for historical filters |
| B13 (historia) | Needed for audit use case |
| C1 (moje stat) | Self analysis |
| C2 (zespol stat) | Team analysis |
| C5 (dzienny) | Day view |
| C6 (raport dzienny) | Standup helper |
| C7 (porownanie) | Direct value composite |
| E3 (PL/EN aliasing) | LLM ergonomics |
| E4 (error translation) | UX |
| E5 (cache słowników) | Latency + tokens |

**Use cases delivered:** UC-4, UC-5, UC-11, UC-12.

---

## P2 — Smart assistance (Scenario 2 complete + Scenario 3 partial)

| Item | Why |
|---|---|
| C3 (cykle) | Trends |
| C4 (zadania) | Type distribution |
| C8 (wykryj problemy) | Manager value |
| D1 (kontekst) | Foundation for automation |
| D2 (sugestia zadań) | First automation tool |
| D6 (auto-tag) | Quality-of-life |

**Use cases delivered:** UC-6, UC-7, UC-8.

---

## P3 — Full automation

| Item | Why |
|---|---|
| D3 (bulk create) | Power-user productivity |
| D4 (szablony) | Reduce repetition |
| D5 (recurring detect) | Proactive |
| D7 (auto-zakończenie) | Proactive |
| E6 (read-only flag) | Safety for risky modes |

**Use cases delivered:** UC-9, UC-10.

---

## Out of scope (for v1)

- Multi-user / multi-tenant operation
- Writing to anything outside the `rejestr` domain (raporty, słowniki admin, users)
- Real-time push from EMP → MCP
- Direct DB access (always via EMP REST API)
- Attachments / file uploads to tasks

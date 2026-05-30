# 13 — Roadmap & Milestones

Concrete build sequence. Each milestone has scope, exit criteria, and a
user-visible demo. Sized for a single developer.

> **Reading order:** docs 06 (tools), 10 (modules), 11 (testing), 12
> (runtime) are the source material; this doc only sequences them.

---

## 0. Conventions

- **DoD** = Definition of Done. Every box must be checked to close a
  milestone.
- **Demo** = the smallest user-visible thing that proves the milestone
  works. If you can't demo it, it's not done.
- **🟢 ship-blocker** boxes must be true; **🟡 nice-to-have** may slip.

---

## 1. Milestone overview

| ID | Name | Tier | Approx effort | Demo |
|---|---|---|---|---|
| **M0** | Repo skeleton + CI gate | P0 | 0.5 d | `pytest` green on an empty package |
| **M1** | Auth + EMP client + health_check | P0 | 1–1.5 d | `mcp-emp` starts, MCP Inspector shows `health_check` returning `ok` |
| **M2** | Domain types + translate + caches + dictionary tools | P0 | 1–1.5 d | `list_task_types`, `list_tags` callable, fixtures captured |
| **M3** | Read tools — `list_my_tasks`, `get_task` | P0 | 1 d | UC-2 read half: find a task by SOD number |
| **M4** | Write tool — `add_my_task` (with dry-run) | P0 | 1 d | UC-1 first half: agent creates a draft |
| **M5** | Transition — `complete_task` | P0 | 0.5 d | UC-2 full: list → find → complete |
| **M6** | Destructive — `delete_task` + confirmation tokens | P0 | 1 d | UC-3 full: bulk-delete drafts with confirmation |
| **M7** | Hardening + docs + release 0.1.0 (P0 ✅) | P0 | 0.5 d | `uv tool install mcp-emp` from local; LLM e2e demo |
| **M8** | HTTP transport (Streamable + legacy SSE) | P1 | 0.5 d | ChatGPT MCP / n8n connects |
| **M9** | Full lifecycle: start/edit/reject/withdraw + list_all + history | P1 | 1.5 d | UC-12 (audit one task) works |
| **M10** | Self & team stats — UC-4, UC-5, UC-11 | P1 | 2 d | Standup-note prompt produces usable output |
| **M11** | Polish — error translation, słownik cache refresh, schema snapshot pinned | P1 | 1 d | Release 0.2.0 (P1 ✅) |
| **M12** | Smart assistance — D1, D2, D6, C8 | P2 | 3 d | UC-6, UC-7, UC-8 |
| **M13** | Automation — bulk + templates + recurring + auto-finish | P3 | 3 d | UC-9, UC-10; release 1.0.0 |

**Total P0:** ~6–7 working days.
**P0 → 1.0:** ~18–20 working days.

---

## 2. M0 — Repo skeleton + CI gate

**Goal:** boring scaffolding so every later milestone has a green
baseline.

**Scope**
- `pyproject.toml` finalised: deps from doc 10 §9, `[project.scripts]`
  entry `mcp-emp = "mcp_emp.__main__:main_sync"`.
- `src/mcp_emp/` layout from doc 10 §1 created with empty modules + a
  one-line docstring each.
- `tests/` layout from doc 11 §3 created with `conftest.py` and one
  trivial passing test per tier.
- `.env.example` (doc 09 §8) committed.
- `.gitignore` covers `.env`, `__pycache__`, `.venv`, `.pytest_cache`,
  `dist/`, `*.egg-info/`.
- `README.md` at repo root: one paragraph + link to `docs/`.
- Lint / type configs: `ruff`, `mypy`, `pytest`.

**DoD**
- 🟢 `uv sync && uv run pytest -q` passes
- 🟢 `uv run ruff check src tests` passes
- 🟢 `uv run mypy src` passes
- 🟢 Import-direction lint (doc 11 §7.1) runs (vacuously passes on
  empty modules)
- 🟡 `pre-commit` hook installed locally

**Demo**
```
$ uv run pytest -q
.....                                                          [100%]
5 passed in 0.18s
```

---

## 3. M1 — Auth + EMP client + `health_check`

**Goal:** prove end-to-end plumbing — env → KC → EMP → MCP transport.

**Scope**
- `config.py` (doc 09 §4) — `Settings` parses cleanly.
- `logging_setup.py` with redaction filter (doc 08 §9).
- `auth/keycloak.py` + `auth/token_holder.py` (doc 10 §3).
  - Resource Owner Password grant.
  - asyncio lock around refresh.
- `emp/client.py` + `emp/endpoints.py` — bearer injection, error mapping
  (doc 08 §3) for: 401, 404, 5xx, network. Other codes mapped on demand.
- `identity.py` — parse user + roles from KC token.
- `errors.py` — codes from doc 08 §2.
- `server.py` skeleton — startup checklist (doc 09 §5), stdio transport
  only.
- `tools/_base.py` — `@mcp_tool` decorator: envelope wrap, error catch,
  `READ_ONLY` gate.
- `tools/health_check.py` — first end-to-end tool.

**Tests**
- Unit: auth/token_holder concurrency lock, errors module, config parse,
  redaction filter (doc 11 §7.2 introduced).
- Integration: `test_tool_health_check.py` happy + EMP-unreachable +
  auth-expired (doc 11 §6 scenarios 1, 3, 4).

**DoD**
- 🟢 `mcp-emp` starts with valid env, logs `mcp-emp ready, transport=stdio`
- 🟢 With bad password → exit 77, clear stderr message
- 🟢 With EMP down → starts anyway with WARN; `health_check` returns
  `EMP_UNREACHABLE`
- 🟢 Concurrent-refresh test passes (KC hit exactly once for N parallel
  calls)
- 🟢 No secret strings appear in any log capture
- 🟡 MCP Inspector connects and lists `health_check`

**Demo**
```
$ npx @modelcontextprotocol/inspector mcp-emp
# Inspector UI → call health_check → returns:
{ "ok": true, "data": { "emp_api": "reachable", "auth": "valid",
                        "user": { "username": "tkowalski", ... } } }
```

---

## 4. M2 — Domain + translate + caches + dictionary tools

**Goal:** lock the data layer with real EMP fixtures, ship the first
read tools.

**Scope**
- `domain/types.py` (doc 07 §4) — all pydantic models.
- `domain/coerce.py` — `parse_emp_datetime`, `tak_nie_to_bool`,
  `parse_time_hhmm`, alias maps.
- `domain/translate.py` — `task_type_from_emp`, `tag_from_emp`,
  `task_from_emp` (full task even though list tools come later).
- `cache/ttl_cache.py` with `get_or_load`.
- `permissions.py` — `compute()` from doc 06 tool 5.
- `tools/list_task_types.py` (doc 06 tool 2).
- `tools/list_tags.py` (doc 06 tool 3).
- **Capture EMP fixtures** (doc 11 §4) for: `slowniki/typ_zadania`,
  `tag`, `tag/pelna-lista`, `health-check`, plus a `lista/moje` sample
  and a `rejestr/{id}` sample (used by M3 but easier to grab in one
  session).
- Update doc 07 §2 to remove the "uncertainty" markers — pin real
  shapes.

**Tests**
- Unit: every translate function tested against captured fixtures;
  coerce helpers; TTL cache; permissions matrix.
- Integration: `list_task_types` + `list_tags` happy path; cache HIT vs
  MISS; `search` and `include_inactive` filters.
- Lint: schema-snapshot test (doc 11 §7.5) committed.

**DoD**
- 🟢 All captured fixtures live under `tests/fixtures/emp/`
- 🟢 Translate coverage ≥ 95% (doc 11 §10)
- 🟢 Inspector → `list_task_types` returns real data; second call shows
  `cached: true`
- 🟢 Doc 07 §2 amended; uncertainties resolved
- 🟢 Schema snapshot file committed

**Demo**
```
> "list every active task type"
LLM → list_task_types() →  27 types returned, named in Polish.
```

---

## 5. M3 — Read tools: `list_my_tasks` + `get_task`

**Goal:** the LLM can find any of your tasks.

**Scope**
- `tools/list_my_tasks.py` (doc 06 tool 4) — both scopes, all filters,
  client-side sorting + limit.
- `tools/get_task.py` (doc 06 tool 5) — full Task + `permissions` block.
- Capture two more fixtures: `lista/moje-wszystkie`, and a
  `rejestr/{id}` for a task in `DO_OCENY` (so `permissions` matrix is
  exercised).

**Tests**
- Integration: both tools across all 7 scenarios from doc 11 §6.
- `INVALID_TRANSITION` / `TASK_NOT_FOUND` paths verified.
- Status-alias map test (doc 11 §3 — `test_status_aliases.py`).

**DoD**
- 🟢 All filter combinations on `list_my_tasks` covered by tests
- 🟢 `get_task` returns a stable `permissions` block per the doc 07 §6
  matrix
- 🟢 `truncated: true` triggers correctly when limit is hit
- 🟢 No EMP call when `task_type_id` filter matches nothing in cache?
  N/A — filter is post-fetch; documented in doc 06.

**Demo**
```
> "find my task about SOD-2024/123"
LLM → list_my_tasks(sod_number="SOD-2024/123") → one match, id=1234
LLM → get_task(1234) → returns full detail with permissions.can_complete=true
```

Delivers UC-2 read half.

---

## 6. M4 — `add_my_task` (first write)

**Goal:** the LLM can create a task. Pre-flight validation, dry-run,
post-create read.

**Scope**
- `tools/add_my_task.py` (doc 06 tool 6).
- Pre-flight: validate `task_type_id` + `requires_*` + `tag_ids` against
  caches.
- Dry-run pipeline (local-only, no EMP call).
- Capture fixture: `POST /rejestr/moje` response.

**Tests**
- Integration: dry-run path (zero EMP calls asserted); happy create;
  `VALIDATION_FAILED` cases (missing `time`, unknown tag); `EMP_REJECTED`
  fallback; READ_ONLY blocks.
- Idempotency note in test: two consecutive `add_my_task` calls create
  two distinct tasks (no key in P0).

**DoD**
- 🟢 Dry-run never hits EMP (respx assertion)
- 🟢 Pre-flight validation catches every rule listed in doc 06 tool 6
- 🟢 `READ_ONLY=true` blocks even dry-run (doc 08 §8)
- 🟢 Successful create returns the full task (saved a `get_task` round-trip)
- 🟡 Schema snapshot updated and committed

**Demo**
```
> "log a meeting I just had about DB migration, 1.5h"
LLM → list_task_types(search="spotk") → picks one
LLM → add_my_task(dry_run=true, …) → preview shown to user
user → "yes"
LLM → add_my_task(…) → task 1287 created, status=W_EDYCJI
```

Delivers UC-1 first half.

---

## 7. M5 — `complete_task`

**Goal:** close a task with the right transition.

**Scope**
- `tools/complete_task.py` (doc 06 tool 7).
- Pre-flight `get_task` to check `permissions.can_complete`.
- Predict `would_transition_to` from task type's `requires_evaluation`.

**Tests**
- Integration: happy (→ZAKOŃCZONE); evaluation path (→DO_OCENY);
  `INVALID_TRANSITION` when status is W_EDYCJI; required `time` /
  `quantity` enforcement.

**DoD**
- 🟢 `next_step` text differs correctly for the two terminal targets
- 🟢 No retry on failed PUT (doc 08 §4)
- 🟢 Auth refresh transparent when token expires mid-call

**Demo**
```
> "mark SOD-2024/123 as done, took 2h15"
LLM → list_my_tasks(sod_number="SOD-2024/123") → 1234
LLM → complete_task(1234, time="02:15") → new_status=ZAKOŃCZONE
```

Delivers UC-2 full.

---

## 8. M6 — `delete_task` + confirmation tokens

**Goal:** the destructive pattern. Locks the E2 contract.

**Scope**
- `confirmations.py` — `TokenStore`, payload-hash binding (doc 08 §7).
- `tools/delete_task.py` (doc 06 tool 8).
- Capture fixture: `DELETE /rejestr/{id}` response + a 400 for
  non-W_EDYCJI delete.

**Tests**
- Unit: every TokenStore case from doc 11 §9 (7 cases).
- Integration: full two-step happy path; preview shows correct task;
  reuse rejected; expired rejected (time-machine); wrong task rejected;
  READ_ONLY blocks before token issuance.

**DoD**
- 🟢 Tokens are single-use; `used` reason returned on reuse
- 🟢 Tokens expire at exactly 5m; `expired` reason returned
- 🟢 Tokens are scoped: `del_1234_x` cannot delete task 1235
- 🟢 Payload hash binding works (test with tampered payload)
- 🟢 Delete forbidden on non-W_EDYCJI returns `INVALID_TRANSITION`
  *before* issuing a token (no wasted tokens)

**Demo**
```
> "delete all my drafts older than 2 weeks"
LLM → list_my_tasks(scope="all", status="W_EDYCJI", created_before=…)
LLM → delete_task(1234)  → preview + token returned
LLM → confirmation prompted to user → "yes"
LLM → delete_task(1234, confirmation_token="del_1234_a3f9…") → deleted
… (loop)
```

Delivers UC-3 full.

---

## 9. M7 — Hardening + 0.1.0 release (P0 ✅)

**Goal:** P0 is shippable.

**Scope**
- All lint tests from doc 11 §7 active and gating.
- README rewritten with: install, configure, host snippets (from doc
  12 §6), pointer to `docs/`.
- `CHANGELOG.md` started with the 0.1.0 entry.
- Manual e2e smoke (doc 11 §11) run once against the real EMP dev.
- `pyproject.toml` version bumped to `0.1.0`.
- Tag `v0.1.0`.

**DoD**
- 🟢 `uv run pytest tests/unit tests/integration tests/lint -q` green
  in < 10s
- 🟢 Coverage targets met (doc 11 §10)
- 🟢 e2e smoke passes manually
- 🟢 README install instructions verified on a clean machine
- 🟢 No `TODO` or `XXX` in shipped code paths
- 🟡 `uv tool install ./` works locally; binary `mcp-emp` on PATH

**Demo**
End-to-end with a real LLM host (Claude Desktop or pi):
1. UC-1: "log a meeting I just had…" → task created.
2. UC-2: "mark SOD-X as done" → task completed.
3. UC-3: "delete my old drafts" → confirmed and removed.

**P0 ✅ when M7 closes.**

---

## 10. M8 — HTTP transport (Streamable + legacy SSE)

**Goal:** universal MCP support (doc 12 §1–2).

**Scope**
- `server.py`: `start_transport` dispatches on `MCP_EMP_TRANSPORT`.
- Starlette + uvicorn + sse-starlette wiring.
- `/mcp`, `/sse`, `/messages`, `/healthz` endpoints.
- Localhost bind by default.

**Tests**
- Integration: in-process test client posts JSON-RPC to `/mcp`, asserts
  `tools/list` works.
- `/healthz` returns 200 even before MCP traffic.
- Transport choice respected via env.

**DoD**
- 🟢 `MCP_EMP_TRANSPORT=http mcp-emp` listens on `127.0.0.1:8765`
- 🟢 `curl /healthz` → 200
- 🟢 MCP Inspector (HTTP mode) connects and lists tools
- 🟡 n8n / ChatGPT MCP smoke test (manual)

**No new tools.** Just plumbing.

---

## 11. M9 — Full lifecycle (P1)

**Goal:** close out task lifecycle CRUD.

**Scope** (from doc 06's deferred P1 list)
- `start_task` (B4) — REALIZUJ
- `edit_task` (B3) — only when W_EDYCJI
- `reject_task` (B6) — needs confirmation token
- `withdraw_task` (B7) — TBD whether token needed
- `list_my_tasks` already supports `scope="all"` from M3
- `get_task_history` (B13)

**DoD**
- 🟢 Lifecycle round-trip test: create → start → complete (covers M4, M5, new start_task)
- 🟢 Reject flow uses the confirmation contract
- 🟢 History returns a sane chronological list

**Demo:** UC-12 audit.

---

## 12. M10 — Stats (P1)

**Goal:** UC-4, UC-5, UC-11.

**Scope**
- `my_cycle_stats` (C1)
- `team_stats` (C2) — only when current user has `kierownik` role; tool
  not registered otherwise
- `daily_stats` (C5), `daily_report` (C6)
- `compare_me_vs_team` (C7) — composite
- Cache identity-derived role; gate tool registration in `server.py`.

**Demo:** "prepare my standup note" → readable Polish/English output.

---

## 13. M11 — Polish + 0.2.0 (P1 ✅)

- Error translation pass — every EMP Polish error mapped to an English
  message + Polish original in `details`.
- Cache refresh story (no API change, internal `invalidate` helper).
- Schema snapshot updated and pinned.
- README updated; CHANGELOG 0.2.0 entry.
- Tag `v0.2.0`.

**P1 ✅ when M11 closes.**

---

## 14. M12 — Smart assistance (P2)

- `current_work_context` (D1)
- `suggest_tasks` (D2) — primarily an LLM-side prompt, plus a data
  feeder tool
- `auto_tag_suggestion` (D6)
- `detect_problems` (C8)
- `cycle_stats` (C3), `type_stats` (C4)
- HTTP shared-secret auth lands here (doc 12 §2 deferred).

**Demos:** UC-6, UC-7, UC-8.

---

## 15. M13 — Automation + 1.0.0 (P3 ✅)

- `bulk_create_tasks` (D3) — full payload-bound token flow
- `bulk_delete_tasks`
- `templates_*` (D4)
- `detect_recurring` (D5)
- `suggest_completions` (D7)
- Lock the SemVer-stable contract (doc 12 §8) at 1.0.0.

**Demos:** UC-9, UC-10.

---

## 16. Out-of-order risks (read this before slipping)

| Temptation | Why it's a trap |
|---|---|
| Start writing tools before M2 fixtures are captured | Translate layer ends up shaped wrong; rework cascades |
| Build HTTP transport before tools work (M8 before M7) | Two debugging surfaces at once; transport bugs masquerade as tool bugs |
| Add idempotency keys to writes "for safety" | Defeats the deliberate "verify via list" pattern (doc 08 §4); P3 candidate at earliest |
| Skip the lint tests | They're the cheapest insurance we have; they pay back on M9+ |
| Defer schema snapshot | Doubles the cost of every later refactor that touches `types.py` |

---

## 17. What this doc fixes

| Question | Answer |
|---|---|
| What's the build order? | M0–M13 in §1 |
| What ships in 0.1.0? | M0–M7 |
| What's the minimum demoable thing? | UC-1, UC-2, UC-3 after M7 |
| Where does HTTP transport go? | M8 (P1, not P0) |
| Per-milestone DoD? | Each §2–§15 |
| Where can I cut scope safely? | Drop M10/M11 → ship 0.2 lighter; drop M12/M13 entirely if value plateau hits |

---

## 18. Cascades

- **Doc 14 (risks):** the temptations in §16 are this doc's contribution
  to the risk register.
- **Code:** M0's first PR creates the doc 10 §1 skeleton; every later
  milestone is one or two PRs against that skeleton.

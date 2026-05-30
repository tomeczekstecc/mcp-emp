# 14 — Risks & Unknowns

The risk register. Each entry: description, likelihood × impact,
mitigation, trigger to re-open. Plus deliberately accepted risks and
"stop the line" conditions.

> **How to read severity:** L × I where each is L=low / M=medium / H=high.
> Severity = max(L, I) unless both are M → still M.

---

## 1. External risks (out of our control)

### R1 — EMP API shape drift

| | |
|---|---|
| Description | EMP's JSON response shapes change (field renamed, type changed, new required field) |
| Likelihood × Impact | **M × H** |
| Why it matters | Every translate function in `domain/translate.py` is derived from EMP shapes |
| Mitigation | Captured-fixture testing (doc 11 §4); translate functions raise `EmpParseError` → surfaces as `EMP_PARSE_ERROR` not silent corruption; schema snapshot test catches the downstream effect on tool contracts |
| Trigger to re-open | Any fixture-replay test fails after a backend update |
| Owner action | Re-capture fixture; update translate; bump MINOR with note in CHANGELOG |

### R2 — Keycloak realm/client config change

| | |
|---|---|
| Description | KC client renamed, realm migrated, ROPC grant disabled |
| Likelihood × Impact | **L × H** |
| Why it matters | mcp-emp doesn't start without working auth |
| Mitigation | `AUTH_MISCONFIGURED` at startup with the offending realm/client_id in the message; doc 09 §5 step 3 hits `/.well-known/openid-configuration` first |
| Trigger | M1's e2e smoke against KC dev fails |
| Owner action | Update env config; if ROPC removed, design a device-code or auth-code-with-PKCE fallback (out of P0 scope) |

### R3 — EMP availability (dev backend down)

| | |
|---|---|
| Description | EMP local instance crashed, network blip, VPN drop |
| Likelihood × Impact | **M × M** |
| Mitigation | `EMP_UNREACHABLE` is a clean, retriable user-facing error; startup health check is WARN not FATAL (doc 09 §5 step 5); read tools auto-retry once (doc 08 §4) |
| Trigger | Persistent `EMP_UNREACHABLE` across multiple sessions |
| Owner action | Operational, not code |

### R4 — Polish character handling in dependencies

| | |
|---|---|
| Description | An upstream lib mishandles `Ł/ł/ż/ó` etc. in identifiers or content |
| Likelihood × Impact | **L × M** |
| Mitigation | UTF-8 enforced (doc 07 §7); `ensure_ascii=False` on JSON dumps; `.casefold()` for case-insensitive search; dedicated test in `test_status_aliases.py` |
| Trigger | A status value comparison fails or a search misses a known match |
| Owner action | Add a focused test against the offending lib path |

---

## 2. MCP / protocol risks

### R5 — MCP spec churn (transports)

| | |
|---|---|
| Description | Streamable HTTP supersedes legacy SSE; spec adds new auth requirements; transport classes renamed in SDK |
| Likelihood × Impact | **M × M** |
| Mitigation | Use the **official `mcp` Python SDK's transport classes**, not hand-rolled wire formats; expose both Streamable HTTP and legacy SSE so client choice doesn't matter (doc 12 §1) |
| Trigger | SDK MINOR bump breaks our `tools/_base.py` or `server.py` |
| Owner action | Pin SDK upper bound in `pyproject.toml`; bump deliberately with a green test run |

### R6 — Tool-description quality drives wrong tool calls

| | |
|---|---|
| Description | LLM picks the wrong tool because descriptions are ambiguous (e.g. confuses `delete_task` and `withdraw_task`) |
| Likelihood × Impact | **M × M** |
| Mitigation | English-only descriptions (Q4); tool description lint test (doc 11 §7.3); each description names its required params and unique characteristics |
| Trigger | e2e test where the LLM picks the wrong tool |
| Owner action | Tighten description; possibly merge or rename tools |

### R7 — Tool surface too large → LLM token-budget pressure

| | |
|---|---|
| Description | When we hit ~30+ tools, smaller models start hallucinating or skipping tool registration |
| Likelihood × Impact | **L (in P0/P1) × M (later)** |
| Mitigation | Role-gated registration (doc 06 conventions) trims surface per user; tool descriptions stay short; defer convenience composites (`add_and_complete_task`) until proven necessary |
| Trigger | Tool count crosses 25 *or* local Ollama users report degraded selection |
| Owner action | Audit; consider an MCP **resource** explaining cross-cutting rules instead of repeating per-tool |

---

## 3. Internal-correctness risks

### R8 — Wrong status transition pre-flight

| | |
|---|---|
| Description | `permissions.compute()` allows an operation EMP forbids, or vice versa |
| Likelihood × Impact | **M × M** |
| Mitigation | Doc 06 tool 5's permissions matrix has unit tests; EMP-side rejection is always surfaced as `EMP_REJECTED` (we don't silently swallow) |
| Trigger | A tool returns `EMP_REJECTED` for an op our `permissions` block said was allowed |
| Owner action | Update `permissions.compute` + add regression test |

### R9 — Confirmation-token misuse

| | |
|---|---|
| Description | LLM (or buggy client) reuses tokens, generates fake tokens, or bypasses the two-step |
| Likelihood × Impact | **L × H** |
| Mitigation | Single-use, TTL, scoped to `(op, resource_id)`, **payload-hash binding** (doc 08 §7.4); no `force: true` escape hatch; lifecycle tests in doc 11 §9 |
| Trigger | Any test in §9 fails or a destructive op fires without a valid token |
| Owner action | This is the closest thing we have to a security-critical path — treat as a P0 ship-blocker bug |

### R10 — Token refresh race condition

| | |
|---|---|
| Description | N parallel tool calls trigger N parallel KC refreshes; one wins, others 401 |
| Likelihood × Impact | **L × M** |
| Mitigation | asyncio lock around refresh (doc 08 §5); dedicated concurrent-refresh test (doc 11 §8) |
| Trigger | Concurrent-refresh test goes red |
| Owner action | Fix lock; consider single-flight pattern |

### R11 — Duplicate writes on retried mutations

| | |
|---|---|
| Description | A client retries `add_my_task` thinking it timed out → two tasks created |
| Likelihood × Impact | **M × M** |
| Mitigation | Doc 08 §4: **we never auto-retry mutations**; tool description tells the LLM to verify via `list_my_tasks` |
| Trigger | A user reports duplicate tasks |
| Owner action | Don't retry. Add idempotency keys (deferred, see §6 — accepted risk) |

### R12 — Cache staleness on dictionaries

| | |
|---|---|
| Description | An admin adds a new task type; mcp-emp doesn't see it for up to 10 minutes |
| Likelihood × Impact | **L × L** |
| Mitigation | TTL of 10m for task types, 5m for tags; restart clears cache; explicit `invalidate` exists internally (M11) |
| Trigger | User reports "this task type doesn't exist" when it clearly does in the UI |
| Owner action | Document `restart to refresh` for P0; expose `refresh_cache` param in P2 if friction emerges |

---

## 4. Security & privacy risks

### R13 — Secrets leaked via logs / errors

| | |
|---|---|
| Description | KC password, client_secret, or bearer token appears in a log line or error envelope |
| Likelihood × Impact | **L × H** |
| Mitigation | `SecretStr` types (doc 09 §4); redaction filter (doc 08 §9); no-secrets-in-logs lint test (doc 11 §7.2) |
| Trigger | Lint test goes red |
| Owner action | Ship-blocker |

### R14 — HTTP transport exposed beyond localhost

| | |
|---|---|
| Description | Someone sets `MCP_EMP_SSE_HOST=0.0.0.0` on a public host without shared-secret auth |
| Likelihood × Impact | **L × H** |
| Mitigation | Localhost default (doc 12 §2); doc 12 warns against `0.0.0.0`; P2 adds `MCP_EMP_HTTP_SHARED_SECRET` |
| Trigger | A user asks how to expose remotely |
| Owner action | Direct them to wait for P2 or front it with their own auth proxy |

### R15 — PII in captured fixtures committed to git

| | |
|---|---|
| Description | EMP fixtures contain real names, SOD numbers, internal subjects |
| Likelihood × Impact | **M (in dev) × M** |
| Mitigation | P0 fixtures captured against dev EMP with dev data; doc 11 §4 flags this for revisit; `.gitattributes`/review checklist |
| Trigger | A fixture turns out to contain real prod data |
| Owner action | Add a scrubbing pass before commit (M2 task if triggered) |

---

## 5. Scope & process risks

### R16 — Scope creep into stats / automation before CRUD is solid

| | |
|---|---|
| Description | "Just one more cool thing" before M7 ships |
| Likelihood × Impact | **H × M** |
| Mitigation | Doc 13 §16 "out-of-order traps"; milestone DoD checklists; CHANGELOG-driven releases |
| Trigger | A new feature appears in code without a milestone reference |
| Owner action | Move to a milestone or to the backlog |

### R17 — EMP routes we read from the codebase don't match runtime

| | |
|---|---|
| Description | Route file says one thing; deployed EMP behaves differently |
| Likelihood × Impact | **L × M** |
| Mitigation | M2 captures fixtures from the live dev backend, not from reading code; doc 13 M2 DoD requires real-data fixtures |
| Trigger | A captured request 404s where the route file says it shouldn't |
| Owner action | Trust runtime; update doc 06's endpoint references |

### R18 — Bus factor / single developer

| | |
|---|---|
| Description | The one person who built this is out for a week |
| Likelihood × Impact | **M × M** |
| Mitigation | **This `docs/` folder is the mitigation.** Anyone reading docs 01–14 can pick up where M-x left off; CHANGELOG records what shipped |
| Trigger | A new contributor takes > 1 day to make their first PR |
| Owner action | Patch the doc gap they hit |

---

## 6. Deliberately accepted risks (we chose not to mitigate)

| # | Risk | Why accepted | Re-evaluate at |
|---|---|---|---|
| A1 | **No idempotency keys on writes** — duplicate creates possible on client retry | EMP doesn't natively support them; LLM can verify via `list_my_tasks`; complexity not worth P0 cost | M9 (P1) — only if a real duplicate-task incident occurs |
| A2 | **In-memory tokens only** — restart = re-login | Single-user local; KC login is < 1s; persistence adds a credential-leak surface (Q3) | Only if multi-user or unattended ops become a goal |
| A3 | **No background process management** — host owns lifecycle | Matches MCP idiom; less to maintain | If hosted/SaaS deployment ever happens |
| A4 | **Pre-flight `get_task` cost on every mutation** — extra round trip | Correctness > one round trip; lets us return rich errors before EMP rejects | When perf metrics show a clear regression |
| A5 | **Filter post-fetch on `list_my_tasks`** — entire list pulled, then filtered locally | EMP `lista/moje` doesn't accept filters; per-user volume is small (Q6) | If a user's history exceeds ~500 active tasks |
| A6 | **No structured logging / metrics in P0** | Adds dep + complexity for unclear value at single-user scale | M12 (P2) if observability needs emerge |
| A7 | **5-min confirmation TTL is fixed** (not configurable per-op) | Simpler reasoning for the LLM and the user | If a real workflow needs a different TTL |
| A8 | **No retry on tool calls from the LLM side** — we don't auto-retry mutations | Doc 08 §4; would risk duplicates | Won't change |
| A9 | **No support for stdio + HTTP in one process** | Doubles process model complexity; just run two | If hosting demands change |
| A10 | **Polish identifiers (`ZAKOŃCZONE`) returned as-is** | They're data; aliasing on output would lie about EMP's actual values | Won't change |

---

## 7. Known unknowns — things we'll learn on first contact

Each carried forward from doc 07 §2; resolution happens during M2.

| # | Question | Resolution path |
|---|---|---|
| U1 | Tag shape in task list responses: objects `[{id, nazwa}]` or just `[id]`? | Capture `lista/moje` fixture in M2 |
| U2 | Are joined name fields like `slownik_typ_zadania_nazwa` always present, or only on `/rejestr/{id}`? | Capture both fixtures; compare |
| U3 | Date format on the wire: `"YYYY-MM-DD HH:MM:SS"` (Laravel default) or ISO 8601? | Inspect captured `data_zlecenia` in fixtures |
| U4 | `czy_aktywny` returned as bool or `"Tak"/"Nie"`? | Capture dictionary fixture |
| U5 | Exact param name for the task id in `PUT /rejestr/zakoncz` body (`id` vs `rejestr_id`)? | Read `Zakoncz.php`; verify with capture |
| U6 | What does the EMP create response return — full task object or just `{id}`? | Capture in M4 |
| U7 | Does `withdraw` (`wycofaj`) require confirmation semantically? | Read `Wycofaj.php` in M9 |
| U8 | What's the actual `rodzaj_zadania` enum range? | Sample a broad `lista/moje-wszystkie` in M2 |

When each is resolved: amend doc 07 §2, drop the marker, add a fixture
test reference.

---

## 8. "Stop the line" triggers

Conditions where we **stop building** and re-plan before continuing.

| # | Trigger | Re-plan action |
|---|---|---|
| S1 | Captured fixtures contradict doc 07 §3 by **more than 5 fields** | Pause M2; rewrite translation table in doc 07; update doc 06 tool returns |
| S2 | KC ROPC grant disabled on the dev realm | Pause auth work; introduce doc 15 "Auth alternatives" (device code or PKCE) |
| S3 | EMP changes break > 3 captured fixtures in one update | Pause feature work; M2-style re-capture sweep; assess if upstream stability is sufficient to continue |
| S4 | Multi-user requirement emerges | Pause; revisit Q2 + Q3 + R14; produce doc 16 "Multi-user model" |
| S5 | MCP spec mandates a breaking change in stdio JSON-RPC framing | Pause; rebuild on the SDK's new transport |
| S6 | A confirmation-token bypass is observed in testing | Stop M-current; treat R9 as a security incident; bisect to root cause; add regression test before resuming |

---

## 9. Risk dashboard (snapshot)

| Severity | Open count | IDs |
|---|---|---|
| **High** | 0 | — |
| **Medium-high** | 1 | R1 (EMP shape drift) |
| **Medium** | 9 | R3, R5, R6, R7, R8, R10, R11, R15, R16 |
| **Low** | 6 | R2, R4, R12, R13, R14, R17, R18 |
| Accepted | 10 | A1–A10 |
| Unknowns | 8 | U1–U8 |

**Top mitigation per severity tier:**
- R1 → captured-fixture testing + schema snapshot (doc 11 §4 + §7.5)
- R5 → official MCP SDK, not hand-rolled wire (doc 12 §1)
- R6 → tool description lint (doc 11 §7.3)
- R16 → milestone DoD + CHANGELOG-driven releases (doc 13)

---

## 10. What this doc fixes

| Question | Answer |
|---|---|
| What can go wrong? | §1–§5 — 18 risks |
| What did we choose NOT to fix? | §6 — 10 accepted risks with re-evaluation triggers |
| What will we only learn later? | §7 — 8 known unknowns tied to M2 |
| When do we stop and re-plan? | §8 — 6 trigger conditions |
| What's the current risk picture? | §9 |

---

## 11. Living document

Every milestone close (doc 13) bumps this doc:
- Move U-items to resolved as fixtures land.
- Re-grade R-items if frequency/impact shifts.
- Add new R-items discovered during build (with a milestone reference).
- Review accepted risks at each MAJOR release (0.2, 1.0).

# 11 — Testing Strategy

What we test, how, with what tools, and where the lines are drawn.
Pragmatic and proportional to a single-user planning-stage project.

---

## 1. Goals (and non-goals)

**Goals**
- Catch contract drift between mcp-emp and EMP early (translate layer).
- Protect the locked-in patterns from docs 06–10: envelope shape, token
  lifecycle, redaction, import direction.
- Make refactors safe by pinning behaviour, not implementation.
- Run fast enough that the whole suite is a local pre-commit step.

**Non-goals**
- 100% line coverage.
- Mocking EMP's database or business logic.
- Load / performance / chaos testing.
- Testing pydantic, httpx, or the MCP SDK themselves.

---

## 2. The test pyramid

```
                       ┌─────────────────────┐
                       │   e2e (live EMP)    │  ~5 tests, manual / nightly
                       └──────────┬──────────┘
                       ┌──────────▼──────────┐
                       │ integration (fakes) │  ~30–40 tests
                       └──────────┬──────────┘
            ┌──────────────────────▼──────────────────────┐
            │              unit tests                     │  bulk of the suite
            │   domain/, coerce, translate, permissions,  │
            │   confirmations, ttl_cache, errors          │
            └─────────────────────────────────────────────┘
```

| Tier | What it covers | Speed | Required to merge? |
|---|---|---|---|
| **Unit** | Pure modules (doc 10 §2 layers 0–2) | < 1 s for full tier | Yes |
| **Integration** | Tools running end-to-end with mocked KC + mocked EMP HTTP | < 5 s for full tier | Yes |
| **e2e** | Real KC + real EMP (local docker / dev) | ~30 s; flaky-tolerant | No — opt-in via marker |

---

## 3. Tooling

| Tool | Purpose |
|---|---|
| `pytest` | Runner |
| `pytest-asyncio` (auto mode) | Async test support |
| `respx` | Mock httpx requests for KC + EMP |
| `freezegun` or `time-machine` | Freeze time for token TTL / overdue tests |
| `dirty-equals` *(optional)* | Loose JSON assertions (e.g. "any datetime") |
| `pytest-cov` | Coverage reports (informational, not gating) |
| `ruff` / `mypy` (already separate from tests) | Lint + types — gating |

Layout:

```
tests/
├── conftest.py                ← shared fixtures (settings, ctx, fakes, time)
├── unit/
│   ├── test_coerce.py
│   ├── test_translate_task.py
│   ├── test_translate_task_type.py
│   ├── test_translate_tag.py
│   ├── test_permissions.py
│   ├── test_confirmations.py
│   ├── test_ttl_cache.py
│   ├── test_errors.py
│   └── test_status_aliases.py
├── integration/
│   ├── test_tool_health_check.py
│   ├── test_tool_list_task_types.py
│   ├── test_tool_list_tags.py
│   ├── test_tool_list_my_tasks.py
│   ├── test_tool_get_task.py
│   ├── test_tool_add_my_task.py
│   ├── test_tool_complete_task.py
│   ├── test_tool_delete_task.py
│   ├── test_auth_lifecycle.py
│   ├── test_read_only_mode.py
│   └── test_envelope_shape.py
├── e2e/
│   ├── conftest.py            ← gated by env MCP_EMP_E2E=1
│   └── test_smoke.py
├── lint/
│   ├── test_import_direction.py
│   ├── test_no_secrets_in_logs.py
│   └── test_tool_descriptions.py
└── fixtures/
    └── emp/                   ← recorded EMP JSON (see §4)
        ├── rejestr_lista_moje.json
        ├── rejestr_get_1234.json
        ├── rejestr_create_response.json
        ├── slowniki_typ_zadania.json
        ├── tag_list.json
        ├── health_check.json
        ├── error_validation_422.json
        ├── error_access_denied_403.json
        └── error_invalid_status_400.json
```

Mirrors `src/mcp_emp/` 1:1 — easy to navigate.

---

## 4. EMP response fixtures

The single biggest risk for mcp-emp is **getting EMP's actual JSON
shape wrong**. We mitigate by:

1. **One captured fixture per endpoint we use.** Captured against the
   real EMP dev instance during the first build session.
2. Stored as **pristine, unedited JSON** under `tests/fixtures/emp/`.
3. Translate-layer tests run **against these exact fixtures** — no
   hand-written sample data for translation.
4. The captures are how the doc 07 §2 "uncertainties" get resolved.
   When captured, doc 07 §2 is amended to point at the fixture and the
   uncertainty marker removed.

**Re-capture protocol:** if EMP changes, capture new fixtures via the
real backend (a small recorder script in `tests/_capture.py`, not run
in CI). PRs include diff of the JSON fixtures alongside the code.

**No sanitisation needed** for P0 — single-user, dev-only data. If real
PII ever ends up in fixtures, we add a scrubbing pass.

---

## 5. What to mock vs not

### Mock

| Thing | How | Why |
|---|---|---|
| `httpx` requests to KC | `respx` | KC isn't always reachable; we want determinism |
| `httpx` requests to EMP | `respx`, returning fixtures from §4 | Same |
| Current time | `time-machine` (per test) | Token TTLs + `overdue` |
| `secrets.token_hex` | `monkeypatch` to fixed value | Predictable confirmation tokens in tests |

### Do **not** mock

| Thing | Why not |
|---|---|
| `pydantic` models | They're the schema; mocking defeats the purpose |
| `translate.py` functions | Their behaviour is what we're testing |
| `confirmations.TokenStore` | Pure in-memory; mocking adds nothing |
| `permissions.compute` | Pure function; test it for real |
| `ok()` / `err()` envelope helpers | One line each; test the envelope at integration |

---

## 6. Per-tool integration test pattern

One test module per tool. Each module covers:

1. **Happy path** — successful call, asserts envelope + key fields.
2. **Validation failure** — local pre-check trips before any EMP call
   (assert `respx` recorded zero EMP requests).
3. **EMP failure mapping** — fixture returns 4xx/5xx; assert correct
   `error.code`.
4. **Auth failure** — KC token expired mid-call; assert one transparent
   refresh + retry, then surface if still failing.
5. **Read-only mode** *(mutating tools only)* — `READ_ONLY=true` blocks
   the call without hitting EMP.
6. **Dry-run** *(mutating tools)* — no EMP write, `data.dry_run=true`,
   identical across N calls.
7. **Confirmation flow** *(destructive tools only)* — token issued,
   committed once, rejected on reuse / expiry / payload mismatch.

Shared assertion helpers in `tests/integration/_asserts.py`:

```python
def assert_envelope_ok(resp: dict) -> dict:
    assert resp["ok"] is True
    assert "data" in resp and "error" not in resp
    return resp["data"]

def assert_envelope_err(resp: dict, code: str) -> dict:
    assert resp["ok"] is False
    assert resp["error"]["code"] == code
    return resp["error"]
```

---

## 7. Special tests (the "rules tests")

These pin the architectural decisions from docs 06–10. They're cheap
and catch a whole class of mistakes.

### 7.1 Import-direction lint (`tests/lint/test_import_direction.py`)

Walks `src/mcp_emp/`, parses `import` / `from` statements, asserts no
module imports from a higher layer per doc 10 §2.

Failure example:
> `domain/translate.py` imports `mcp_emp.emp.client` — forbidden (domain
> is layer 2, emp/client.py is layer 3).

### 7.2 No-secrets-in-logs (`tests/lint/test_no_secrets_in_logs.py`)

Runs the full integration tier with `caplog` and a configured logger;
asserts no log record contains:
- The KC password from settings
- The KC client secret (if set)
- A literal `Bearer eyJ` token prefix
- Anything matching the access/refresh token regex

### 7.3 Tool description compliance (`tests/lint/test_tool_descriptions.py`)

For every registered tool:
- Description is non-empty, English, ≥ 20 chars.
- Description mentions every required parameter by name.
- For mutating tools: description mentions `dry_run`.
- For destructive tools: description mentions `confirmation_token`.

### 7.4 Envelope shape (`tests/integration/test_envelope_shape.py`)

Every tool, on success and on its most-common failure, returns the
exact envelope shape from doc 08 §1.

### 7.5 Schema stability

Snapshot test: dump `domain/types.py` model JSON schemas to a file
committed to the repo. Test asserts current schemas match the snapshot.
Snapshot updates are explicit PR-level decisions — protects the LLM
contract from accidental shape changes.

---

## 8. Auth lifecycle tests

`tests/integration/test_auth_lifecycle.py` — pinned scenarios from doc 08 §5:

| Scenario | Setup | Assert |
|---|---|---|
| Token still valid | KC mock not called | Tool succeeds; KC hit 0 times |
| Token expiring within safety margin | Time advanced 11m | KC refresh hit once |
| Refresh token rejected | KC returns 400 on refresh | Full re-login attempted |
| Re-login fails | KC returns 401 | `AUTH_EXPIRED` envelope |
| Concurrent calls hit refresh | 5 parallel tool calls when expired | KC refresh hit **exactly once** (lock works) |
| EMP returns 401 once | First request 401, second OK | One transparent retry; tool returns success |

---

## 9. Confirmation-token tests

`tests/unit/test_confirmations.py` — pinned from doc 08 §7:

| Case | Expected |
|---|---|
| Issue + validate same payload | `validate_and_use` succeeds |
| Reuse same token | `CONFIRMATION_INVALID { reason: "used" }` |
| Wait > TTL then use | `... { reason: "expired" }` |
| Tamper resource_id | `... { reason: "wrong_task" }` |
| Tamper payload | `... { reason: "wrong_task" }` *(or `payload_changed` when introduced)* |
| Unknown token | `... { reason: "unknown" }` |
| Format invariants | Token matches `^[a-z_]+_\d+_[a-f0-9]{16}$` |

Background-sweep eviction not tested in P0 (lazy eviction is enough).

---

## 10. Coverage targets — pragmatic

| Layer | Target | Enforcement |
|---|---|---|
| `domain/`, `coerce`, `translate`, `permissions`, `confirmations`, `errors` | **≥ 95%** | gating in CI |
| `tools/*` | **≥ 80%** | gating |
| `emp/client`, `auth/*` | **≥ 80%** | gating |
| `server.py`, `__main__.py`, `logging_setup.py` | informational | not gating |
| Overall | report only | not gating |

Coverage is a signal, not a target. We don't add tests just to hit a
percentage.

---

## 11. e2e tests (opt-in)

`tests/e2e/` runs only when `MCP_EMP_E2E=1` is set. Hits a real local
EMP + real KC dev. Marked `@pytest.mark.e2e`.

P0 e2e suite — 5 smoke tests:

1. `health_check` succeeds.
2. `list_task_types` returns at least one type.
3. `add_my_task` (dry_run) preview matches the type's defaults.
4. Full happy path: `add_my_task` → `get_task` → `complete_task` →
   verify in `list_my_tasks(scope="all")`.
5. `delete_task` two-step on a fresh `W_EDYCJI` task.

e2e tests create and immediately clean up their own data (or use a
test user with a disposable register).

---

## 12. CI shape (informational)

Single GitHub-Actions-style pipeline (or local `make test`):

```
ruff check src tests
mypy src
pytest tests/unit tests/integration tests/lint  -q
# e2e job is separate, manual trigger or nightly
```

Target wall time for the gating job: **under 10 seconds** on a warm
laptop.

---

## 13. What this doc fixes

| Question | Answer |
|---|---|
| What's the testing pyramid? | §2 |
| What tools do we use? | §3 |
| How do we avoid lying to ourselves about EMP shapes? | §4 — captured fixtures |
| What's mocked, what isn't? | §5 |
| What does every tool's test module look like? | §6 |
| How do we protect the locked-in architecture? | §7 — lint tests |
| How do we test the auth lifecycle? | §8 |
| How do we test the confirmation tokens? | §9 |
| Coverage policy? | §10 |
| When do we run e2e? | §11 |

---

## 14. Cascades

- **Doc 12 (runtime):** transport tests live at integration level; we
  mock the MCP client side.
- **Doc 13 (roadmap):** "P0 done" means unit + integration + lint tiers
  all green; e2e smoke run at least once manually.
- **Doc 14 (risks):** the EMP-shape risk is the single biggest one; §4
  (fixtures) is its mitigation.

# 08 — Error & Confirmation Model

How failures and destructive operations are communicated to the LLM and
handled internally. Locks the contract that tool 8 (`delete_task`)
introduced and expands it for every future tool.

---

## 1. Error envelope (canonical)

Defined in doc 07 §4; restated here so this doc is self-contained.

```jsonc
{
  "ok": false,
  "error": {
    "code": "INVALID_TRANSITION",         // stable, machine-readable, SCREAMING_SNAKE
    "message": "Task is not in W_EDYCJI; deletion is only allowed for drafts.",
    "details": {                          // optional, code-specific schema
      "current_status": "REALIZOWANE",
      "allowed_source_statuses": ["W_EDYCJI"]
    }
  }
}
```

**Hard rules:**
- `ok` is always `false` when `error` is present, never both.
- `code` is stable forever — never rename a code, only add new ones.
- `message` is English, ≤ 200 chars, no Polish unless quoting EMP.
- `details` is optional but **schema-stable per code** (§3).
- Tools **never raise** — every path returns an envelope.
- Internal exceptions caught at the tool boundary and mapped to
  `INTERNAL_ERROR` if nothing more specific fits.

---

## 2. Canonical error code catalog

Codes are grouped by family. Adding a new code requires updating this
table.

### 2.1 Connectivity & auth

| Code | When | Details schema | Retry? |
|---|---|---|---|
| `EMP_UNREACHABLE` | Network failure, timeout, DNS failure to EMP base URL | `{url, timeout_seconds}` | Caller may retry; we don't auto-retry |
| `EMP_5XX` | EMP returned 500–599 | `{status, emp_message}` | One internal retry with backoff, then surface |
| `AUTH_EXPIRED` | KC refresh failed and re-login failed | `{realm, last_attempt_at}` | No — needs human intervention |
| `AUTH_MISCONFIGURED` | Startup-time: bad client id/secret, unknown realm | `{realm, client_id}` | No — fail-fast at startup |

### 2.2 Lookup & validation (local, before EMP call)

| Code | When | Details schema |
|---|---|---|
| `VALIDATION_FAILED` | A tool parameter violates a rule (missing required, bad format, conditional rule) | `{field, rule, task_type_id?, task_type_name?}` |
| `TASK_TYPE_NOT_FOUND` | `task_type_id` not in cache and not in EMP | `{task_type_id}` |
| `TAG_NOT_FOUND` | One or more `tag_ids` unknown | `{unknown_tag_ids: int[]}` |
| `UNKNOWN_ENUM` | Caller passed a status / alias we don't recognise | `{field, value, allowed: string[]}` |

### 2.3 Authorization & state

| Code | When | Details schema |
|---|---|---|
| `TASK_NOT_FOUND` | EMP 404, **or** task exists but hidden from current user (indistinguishable on purpose — doc 06 tool 5) | `{task_id}` |
| `INVALID_TRANSITION` | Tool's status precondition not met | `{current_status, allowed_source_statuses: string[]}` |
| `FORBIDDEN` | EMP `AccessDeniedException` — caller lacks role/ownership | `{required: string?}` |

### 2.4 EMP-side rejection

| Code | When | Details schema |
|---|---|---|
| `EMP_REJECTED` | EMP returned 4xx that isn't one of the above (e.g. business rule we don't model locally) | `{status, emp_message, emp_errors?: object}` |
| `EMP_PARSE_ERROR` | EMP returned a 2xx but the payload doesn't fit our schema | `{path, expected, got}` |

### 2.5 Confirmation flow

| Code | When | Details schema |
|---|---|---|
| `CONFIRMATION_INVALID` | Token unknown, used, expired, or scoped to a different resource | `{reason: "unknown" \| "used" \| "expired" \| "wrong_task"}` |

> `CONFIRMATION_REQUIRED` is **reserved but unused** — the missing-token
> case returns `ok: true` with `requires_confirmation: true` instead, so
> the LLM sees a successful preview rather than an error.

### 2.6 Configuration & runtime

| Code | When | Details schema |
|---|---|---|
| `READ_ONLY_MODE` | Mutating tool called while E6 read-only flag is on | `{flag: "MCP_EMP_READ_ONLY"}` |
| `RATE_LIMITED` | Reserved for future use | `{retry_after_seconds}` |
| `INTERNAL_ERROR` | Catch-all for uncaught exceptions at tool boundary | `{exception_class?, request_id}` |

---

## 3. EMP → mcp-emp error mapping

Single table, applied at the EMP client layer.

| EMP signal | mcp-emp `code` | Notes |
|---|---|---|
| `httpx.ConnectError` / `httpx.ConnectTimeout` | `EMP_UNREACHABLE` | |
| `httpx.ReadTimeout` | `EMP_UNREACHABLE` | with `timeout_seconds` |
| HTTP 401 / 403 (after one refresh attempt) | `FORBIDDEN` if `AccessDeniedException` mentioned in body, else `AUTH_EXPIRED` | |
| HTTP 404 on `/rejestr/{id}` | `TASK_NOT_FOUND` | |
| HTTP 404 on dictionary lookup | `TASK_TYPE_NOT_FOUND` / `TAG_NOT_FOUND` | |
| HTTP 422 (Laravel validation) | `EMP_REJECTED` with `emp_errors` populated | |
| HTTP 400 mentioning `Status` in message | `INVALID_TRANSITION` if we can parse current vs allowed; else `EMP_REJECTED` | |
| HTTP 400 — `InvalidDataException` | `EMP_REJECTED` | |
| HTTP 5xx | `EMP_5XX` (after 1 retry) | |
| 2xx with unexpected payload | `EMP_PARSE_ERROR` | from `task_from_emp` etc. |

**Polish in EMP messages:** preserved verbatim in `details.emp_message`.
Our `message` field stays English with a short translation/summary.

---

## 4. Retry policy

Conservative; explicit; never retries mutations.

| Operation kind | EMP signal | Retry? |
|---|---|---|
| Read (`GET`) | network error / timeout | **1 retry** after 250ms backoff |
| Read | HTTP 5xx | **1 retry** after 500ms backoff |
| Read | HTTP 4xx | no retry |
| Mutation (`POST/PUT/DELETE`) | **any** | **no retry** — surface to LLM |
| Token refresh | KC 5xx | 1 retry; then surface as `AUTH_EXPIRED` |

**Why no retries on mutations?** Without an idempotency key (deferred,
doc 06 tool 6), retrying a `POST /rejestr/moje` would risk duplicate
tasks. The LLM is told to use `list_my_tasks` to verify if uncertain.

---

## 5. Authentication lifecycle (runtime)

Builds on Q1/Q3 from doc 05.

```
startup:
  load config (env / file)
  KC login with username + password
  if fail → exit non-zero with AUTH_MISCONFIGURED message to stderr

per-tool call:
  ensure_token():
    if access_token still valid (>30s left) → use it
    elif refresh_token still valid → KC refresh
    else → KC full re-login with stored username + password
    if all fail → return AUTH_EXPIRED envelope (do not retry)

on EMP 401:
  one transparent retry after refresh
  if still 401 → AUTH_EXPIRED envelope
```

**Storage:** in-memory only (Q3). Tokens never logged.
**Concurrency:** asyncio lock around refresh to prevent thundering-herd.
**Clock skew:** 30s safety margin on the "still valid" check.

---

## 6. Dry-run guarantees

For every mutating tool that supports `dry_run: true`:

| Guarantee | Specification |
|---|---|
| No EMP write call | No `POST/PUT/DELETE` to EMP — only `GET` for pre-flight reads |
| No cache mutation | Caches are read-only during dry-run |
| No confirmation token issued | Dry-run is *not* the same as preview — see §7 |
| Returns same validation errors as real run | Pre-flight is identical; only the final write is skipped |
| Returns `data.dry_run: true` and `data.<verb>: false` | LLM-visible signal that nothing happened |
| Idempotent | Calling N times returns N identical responses |

**Dry-run vs preview clarification:**
- **Dry-run** (`dry_run: true`) = "show me what would happen, don't commit".
  Available on `add_my_task`, `complete_task`, `delete_task`.
- **Preview** (omitting `confirmation_token`) = "I want a token to commit later".
  Only on destructive tools.

Both can be combined: `dry_run: true` on a destructive tool returns the
same preview but with a clear "no token issued" signal.

---

## 7. Confirmation-token lifecycle (full spec)

Formalises tool 8's contract.

### 7.1 Anatomy

```
Format:        <op>_<resource_id>_<8 hex chars>
Example:       del_1234_a3f9c10e
```

| Component | Spec |
|---|---|
| `op` | Short operation code: `del`, `bulk_del`, `reject`, `bulk_add`, … |
| `resource_id` | Numeric id, or `0` for batch ops where multiple ids apply (use `batch_id` field instead) |
| Random suffix | `secrets.token_hex(8)` — 64 bits of entropy |

### 7.2 In-memory record

```python
@dataclass
class TokenRecord:
    token: str
    op: str
    resource_id: int
    expected_payload_hash: str   # see §7.4
    issued_at: datetime
    expires_at: datetime
    used: bool = False
```

Stored in a `dict[str, TokenRecord]`, keyed by `token`. Eviction:
lazy — checked on lookup. Optional background sweep every 60s to bound
memory if many tokens are issued and never consumed.

### 7.3 Lifecycle states

```
[issued] ──(timeout 5m)──▶ [expired]
   │
   │ caller submits matching (op, resource_id, token)
   ▼
[validated] ──(commit succeeds)──▶ [used] (record kept 1m for "already used" detection)
                                       │
                                       ▼
                                   (evicted)
```

### 7.4 Anti-bait-and-switch (payload binding)

The preview returns a `confirmation_token` **bound** to a hash of the
operation's effective payload. On commit, the tool recomputes the
payload hash and rejects if it differs.

Why: prevents an LLM (or a buggy call chain) from issuing
`bulk_create_tasks(...)` for 2 tasks, then re-using the token to commit
12 tasks.

| Tool | Bound payload |
|---|---|
| `delete_task` | `{task_id}` |
| `reject_task` (future) | `{task_id, reason}` |
| `bulk_delete_tasks` (future) | sorted `[task_id, ...]` |
| `bulk_create_tasks` (future) | normalised list of drafts |

Hash algorithm: `hashlib.sha256(canonical_json.encode()).hexdigest()[:16]`
where `canonical_json` is `json.dumps(payload, sort_keys=True,
ensure_ascii=False, separators=(",", ":"))`.

Mismatch on commit → `CONFIRMATION_INVALID` with `reason: "wrong_task"`
(or a new reason `"payload_changed"`, TBD when first batch tool lands).

### 7.5 Single-use & TTL

- **Single-use:** committed tokens flip to `used`. Re-submitting →
  `CONFIRMATION_INVALID` with `reason: "used"`.
- **TTL:** 5 minutes from issuance. Expired → `reason: "expired"`.
- **Scoping:** mismatched `(op, resource_id)` → `reason: "wrong_task"`.
- **Unknown:** never-issued or evicted → `reason: "unknown"`.

### 7.6 Tools using the contract

| Tool | Op code | Notes |
|---|---|---|
| `delete_task` (P0) | `del` | Implemented in tool 8 |
| `reject_task` (P1) | `reject` | Adds reason text |
| `withdraw_task` (P1) | undecided — may skip token if reversible | TBD |
| `bulk_delete_tasks` (P3) | `bulk_del` | Multi-resource; payload bound |
| `bulk_create_tasks` (P3) | `bulk_add` | Payload bound to draft list |

**Reversible mutations do not get tokens** — `complete_task`, `start_task`,
`add_my_task`. They use `dry_run` only.

---

## 8. Read-only mode (E6)

Global kill-switch. When `MCP_EMP_READ_ONLY=true`:

- Read tools work unchanged.
- Every mutating tool short-circuits with:
  ```json
  { "ok": false,
    "error": {
      "code": "READ_ONLY_MODE",
      "message": "Mutations are disabled (MCP_EMP_READ_ONLY=true).",
      "details": { "flag": "MCP_EMP_READ_ONLY" }
    } }
  ```
- The flag is checked **before** pre-flight reads, so no EMP traffic is
  generated by a blocked mutation.
- Dry-run is **not** an exception: in read-only mode, even
  `add_my_task(dry_run=true)` is blocked. Rationale: keep the rule
  simple ("no mutation tool runs at all"); avoid edge-case confusion.

Open question deferred to doc 09: should READ_ONLY be settable per-session
via MCP, or only via env at startup? P0 answer: env only.

---

## 9. Logging & redaction

| Rule | Spec |
|---|---|
| **Never log:** access tokens, refresh tokens, KC password, client secret | Replace with `***` if encountered in any log path |
| **Always log:** request method + path, status code, duration, tool name, error code | At INFO for success, WARN for `ok:false`, ERROR for `INTERNAL_ERROR` |
| Polish content | Allowed in logs as-is (UTF-8); no escaping |
| Request IDs | Generate one per tool call (`uuid4().hex[:12]`); include in `INTERNAL_ERROR.details.request_id` |
| Body logging | Only at DEBUG level; redact `Authorization`, `password`, `client_secret` |
| Confirmation tokens | Logged in full (they're not secrets — they only work for 5 minutes against one resource and require auth) |

Default log level: `INFO`. Set via `MCP_EMP_LOG_LEVEL`.

---

## 10. Error UX in the tool description

Each tool's MCP description lists the **non-obvious** error codes it can
return, so the LLM can plan recovery. Example for `delete_task`:

> Common errors: `INVALID_TRANSITION` (only `W_EDYCJI` deletable),
> `CONFIRMATION_INVALID` (preview expired or token reused),
> `TASK_NOT_FOUND` (id unknown or hidden).

Universal errors (`AUTH_EXPIRED`, `EMP_UNREACHABLE`, `INTERNAL_ERROR`)
are documented in a single MCP **resource** the LLM can read once, not
repeated per tool — keeps descriptions tight.

---

## 11. What this doc fixes

| Question | Answer |
|---|---|
| Envelope shape | §1 |
| Full code list | §2 |
| EMP exception mapping | §3 |
| Retry behaviour | §4 |
| Token lifecycle on auth | §5 |
| Dry-run guarantees | §6 |
| Confirmation token full spec | §7 |
| Read-only mode | §8 |
| Logging rules | §9 |
| How LLM learns about errors | §10 |

---

## 12. Cascades

- **Doc 09 (config):** must expose `MCP_EMP_READ_ONLY`, `MCP_EMP_LOG_LEVEL`,
  and the KC creds referenced in §5.
- **Doc 10 (modules):** implies `errors.py` (codes), `auth/` (lifecycle
  §5), `confirmations.py` (TokenStore §7), `emp_client.py` (mapping §3).
- **Doc 11 (tests):** every code in §2 needs at least one test; token
  lifecycle (§7) has its own test module; redaction rules (§9) are
  asserted.

# 05 — Open Questions & Decisions

Decisions made during planning. Each entry: **question**, **decision**,
**rationale**, **implications** for later docs.

---

## Q1 — Auth flow

**Question:** Does mcp-emp authenticate against Keycloak itself, or
receive a pre-issued JWT from the host?

**Decision:** ✅ **mcp-emp logs into Keycloak directly with username + password.**

Uses Keycloak's **Resource Owner Password Credentials** grant against:
- realm: `eMP`
- client: `eMP-REST-API`
- token endpoint: `${KEYCLOAK_BASE_URL}/realms/eMP/protocol/openid-connect/token`

**Rationale:**
- mcp-emp runs locally per-user (see Q2) — credentials live on the user's
  own machine.
- No host integration needed; works the same under pi, Claude Desktop, and
  Ollama clients.
- Lets mcp-emp transparently refresh tokens without involving the host.

**Implications:**
- Need username + password (or client_secret) in config — see Q3 + doc 09.
- Need refresh-token handling in the auth module (doc 10).
- Tools should never expose the JWT in their output.
- Failed login = mcp-emp won't start (fail fast).

---

## Q2 — Single-user vs multi-user

**Question:** One instance per person, or shared service?

**Decision:** ✅ **Single-user.** One mcp-emp process per user, on the user's
own machine.

**Rationale:**
- Matches scenarios 1–3 — all are first-person ("my zadania", "my team").
- Vastly simpler: no session multiplexing, no per-request identity
  switching, no shared cache invalidation.
- Aligns with MCP's typical deployment model (one server per client).

**Implications:**
- Identity context (A3) is global to the process — resolved once at startup.
- Cache (E5) is process-local; no Redis / shared store needed.
- Concurrency model is simple: one user, sequential or low-parallelism
  tool calls.
- Out of scope: per-tenant config, audit logs, rate limiting per user.

---

## Q3 — Token storage

**Question:** Where do JWT and refresh token live at runtime?

**Decision:** ✅ **In-memory only.** Tokens are obtained at startup and
held in process memory; never persisted to disk, keyring, or env.

**Rationale:**
- Single-user + single-process (Q2) makes persistence unnecessary.
- Restart cost is low: one Keycloak login on boot.
- Removes a whole class of credential-leakage risks (no token files to
  read or sync).
- Username + password / client secret still need persistence — handled in
  doc 09.

**Implications:**
- Auth module holds: `access_token`, `refresh_token`, `expires_at` in memory.
- Refresh proactively before expiry; fall back to full re-login on refresh
  failure.
- On process exit: tokens vanish. No cleanup needed.
- Logs must redact token values (rule for doc 08).

---

## Q4 — Tool description language

**Question:** Polish, English, or bilingual tool names/descriptions?

**Decision:** ✅ **English only** for tool names, parameter names, and
descriptions.

**Rationale:**
- Maximises LLM tool-selection accuracy across providers (most are
  English-dominant).
- Keeps the MCP surface uniform and concise (no duplication).
- Polish stays where it belongs: in EMP data (status values like
  `W_EDYCJI`, field values, user-facing messages).

**Implications:**
- Tool names: `add_my_task`, `complete_task`, `list_my_tasks`, etc.
- Parameter names: English (`subject`, `task_type_id`, `deadline`).
- Field aliasing: mcp-emp **translates** Polish EMP fields ↔ English tool
  params (doc 07). E.g. `dotyczy` ↔ `subject`, `data_termin` ↔ `deadline`.
- Status values stay Polish in returned data (`W_EDYCJI`, `ZAKOŃCZONE`)
  because they're identifiers, not prose — but each tool's description
  documents what they mean.
- Error messages from EMP (often Polish) are translated to English in
  doc 08's error model, with original preserved in a `details` field.
- E3 in feature list ("PL ↔ EN aliasing") is therefore **inbound only**:
  we accept English from the LLM, never require Polish.

---

## Q5 — Target LLM hosts

**Question:** Which MCP clients must mcp-emp support?

**Decision:** ✅ **All major hosts** — pi, Claude Desktop, local Ollama,
and any standards-compliant MCP client.

**Rationale:**
- All speak the same MCP protocol; supporting "all" costs no more than
  supporting one, as long as we stick to standard MCP features.
- Avoids host-specific lock-in.

**Implications:**
- Stick to the **MCP standard**: tools, resources, prompts. No
  host-specific extensions.
- Support **both transports**: stdio (Claude Desktop, pi local) and
  HTTP+SSE (remote / web hosts). Decided properly in doc 12.
- Tool descriptions must be self-contained — no assumption about a
  particular system prompt or host UI.
- Token-budget conscious: smaller hosts (local Ollama) benefit from
  caching (E5) and trimmed payloads (Q6 + doc 07).
- No telemetry that phones home to a specific host vendor.

---

## Q6 — Payload size

**Question:** Are EMP responses small enough to return verbatim, or do we
need pre-summarisation / pagination?

**Decision:** ✅ **Assume small.** Return EMP responses largely as-is,
with light shaping (field rename, status enrichment).

**Rationale:**
- User's read of the codebase: stats endpoints return per-user / per-cycle
  aggregates, not raw events.
- Lists are scoped (`moje`, `moje-wszystkie`) so even "all" is one user's
  history, not the whole org.
- Pre-optimising for big payloads adds complexity we may never need.

**Implications:**
- Doc 07 (data shapes) does field renaming + minor enrichment only — no
  truncation, no summarisation.
- **Guard rails** (deferred, not implemented in P0):
  - Soft cap: if a response > ~50 KB serialised, log a warning.
  - Hard cap: if > ~200 KB, return an error suggesting a narrower filter.
  - Both thresholds revisited if we hit them in practice.
- No pagination layer on top of EMP — if EMP itself paginates, we expose
  its paging params; if it doesn't, we don't invent one.
- Caching (E5) is targeted at słowniki (rarely change), not at large
  result sets.

---

## Decision summary table

| # | Topic | Decision |
|---|---|---|
| Q1 | Auth | Keycloak Resource Owner Password Credentials, username + password |
| Q2 | Deployment | Single-user, single-process, local |
| Q3 | Token storage | In-memory only |
| Q4 | Tool language | English only (Polish preserved in data values) |
| Q5 | Hosts | All MCP-standard clients (pi, Claude, Ollama, …); stdio + SSE |
| Q6 | Payload size | Small; return as-is with light shaping; guard rails deferred |

---

## What these decisions unlock

- **Doc 06 — Tool surface:** can use English names + English params straight away.
- **Doc 07 — Data shapes:** field-rename layer only; no pagination/truncation logic.
- **Doc 08 — Error model:** EMP errors translated EN; tokens redacted in logs.
- **Doc 09 — Configuration:** username + password + Keycloak coords are the must-haves.
- **Doc 10 — Module layout:** auth module is simple (one in-memory `TokenHolder`).
- **Doc 12 — Runtime:** support both stdio and SSE transports.

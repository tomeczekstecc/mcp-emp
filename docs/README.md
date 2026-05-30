# mcp-emp — Planning Docs

Planning artifacts for the `mcp-emp` MCP server that bridges an AI agent to the
**EMP** (Elektroniczna Miara Pracy) Laravel backend.

> **Status:** planning only. No production code yet.

---

## Reading order

1. [`01-overview.md`](01-overview.md) — what the app is, the EMP backend, the stack
2. [`02-features.md`](02-features.md) — feature catalog (Areas A–E)
3. [`03-use-cases.md`](03-use-cases.md) — user use cases UC-1 … UC-12
4. [`04-prioritization.md`](04-prioritization.md) — P0 MVP → P3 roadmap tiers
5. [`05-open-questions.md`](05-open-questions.md) — decisions to make before building
6. [`06-tool-surface.md`](06-tool-surface.md) — MCP tool contract design *(pending)*
7. [`07-data-shapes.md`](07-data-shapes.md) — request/response shapes *(pending)*
8. [`08-error-model.md`](08-error-model.md) — errors, dry-runs, confirmations *(pending)*
9. [`09-configuration.md`](09-configuration.md) — config + secrets *(pending)*
10. [`10-module-layout.md`](10-module-layout.md) — Python module map *(pending)*
11. [`11-testing.md`](11-testing.md) — testing strategy *(pending)*
12. [`12-runtime.md`](12-runtime.md) — deployment, transport, runtime *(pending)*
13. [`13-roadmap.md`](13-roadmap.md) — milestones and sequencing *(pending)*
14. [`14-risks.md`](14-risks.md) — risks & unknowns *(pending)*

---

## Planning topics — status

| # | Topic | Status |
|---|---|---|
| 0 | Overview | ✅ |
| 1 | Features catalog | ✅ |
| 2 | Use cases | ✅ |
| 3 | Prioritization | ✅ |
| 4 | Open questions | ✅ |
| 5 | Tool surface | ✅ (P0 done; P1+ deferred) |
| 6 | Data shapes | ✅ |
| 7 | Error & confirmation model | ✅ |
| 8 | Configuration | ✅ |
| 9 | Module layout | ✅ |
| 10 | Testing strategy | ✅ |
| 11 | Runtime & deployment | ✅ |
| 12 | Roadmap & milestones | ✅ |
| 13 | Risks & unknowns | ✅ |

---

## Glossary (Polish ↔ English)

| Polish | English |
|---|---|
| zadanie / zadania | task / tasks |
| rejestr | task register (EMP domain name) |
| pracownik | employee |
| kierownik | manager |
| dyrektor | director |
| zarząd | board |
| zespół | team |
| cykl / nr_cyklu | work cycle / cycle number |
| dotyczy | subject / description |
| przekaż | hand over |
| przydziel | assign |
| realizuj | start work / in progress |
| zakończ | finish |
| odrzuć | reject |
| wycofaj | withdraw |
| usuń | delete |
| punkty | points (scoring) |
| waga | weight |
| słownik | dictionary / lookup table |

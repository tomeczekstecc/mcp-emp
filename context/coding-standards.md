# mcp-emp Coding Standards

## Python Language

- Target Python `>=3.12` (matches `pyproject.toml`).
- Use modern type hints: `list[str]`, `dict[str, int]`, `X | None` — not `List`, `Dict`, `Optional`.
- Add type hints to every function signature crossing a module boundary.
- Avoid `Any`; prefer specific types, `Protocol`, or `TypeVar`.
- Prefer `dataclasses` or **Pydantic models** for structured data; do not pass loose `dict[str, Any]` across layers.
- Use `from __future__ import annotations` only when needed for forward refs; on 3.12 it's rarely required.

## MCP Tools

- One tool = one verb. Name tools `verb_noun` (`list_employees`, `get_employee`, `create_ticket`).
- Tool docstrings are the LLM-facing spec. First line is a one-sentence summary. Follow with `Args:` and `Returns:` sections.
- Declare every parameter with a precise type hint. Use Pydantic models for nested inputs.
- Return JSON-serializable values: Pydantic models, dicts of primitives, or lists thereof. Never return ORM rows, `httpx.Response`, or raw `bytes` without a reason.
- Raise informative exceptions; the MCP runtime will translate them. Do not return strings like `"error: ..."` from a successful tool path.
- Keep tool functions thin: parse args → call domain client → map → return. Business logic belongs in the domain layer.

## Async

- All I/O is async. Use `httpx.AsyncClient`, not `httpx.Client`.
- Do not block the event loop with `time.sleep`, `requests`, or blocking file I/O — use `asyncio.sleep`, `httpx.AsyncClient`, and `anyio` / `aiofiles`.
- Share one `httpx.AsyncClient` per process (lifespan-managed), not one per call.

## HTTP / `httpx`

- Centralize base URL, timeouts, auth headers, and retry logic in `mcp_emp/core/http.py`.
- Always set explicit `timeout=` — never rely on defaults for production calls.
- Parse responses with Pydantic (`Model.model_validate(response.json())`), not by hand-walking dicts.
- Treat non-2xx responses as errors at the client layer; map them to domain errors before they reach tool handlers.
- Do not log request/response bodies that may contain secrets.

## Domain-Driven Organization

- Organize code by bounded context under `mcp_emp/domains/<domain>/`.
- Each domain owns: `contract.py`, `mapper.py`, `client.py`, `tools.py`.
- Keep cross-cutting infrastructure (`http`, `config`, `logging`) under `mcp_emp/core/`.
- Introduce `mcp_emp/shared/` only after a second real caller appears — never as a default landing zone.
- Avoid generic names like `utils`, `helpers`, `common` at the package level.

## Configuration

- Read configuration from environment variables via a single `Settings` object (Pydantic `BaseSettings` or equivalent).
- Validate config at startup; fail fast with a clear message on missing/invalid values.
- Never read `os.environ` directly inside tools or clients.
- Never commit secrets; `.env` is local-only.

## Errors

- Define domain-specific exception classes (`EmployeeNotFound`, `UpstreamUnavailable`) in `mcp_emp/domains/<domain>/errors.py` when the domain grows beyond trivial.
- Catch `httpx.HTTPError` at the client boundary; re-raise as a domain error.
- Never silently swallow an exception. If a fallback is intentional, log it and document why.

## Logging

- Use the standard `logging` module configured once in `mcp_emp/core/logging.py`.
- Log at module-level loggers: `logger = logging.getLogger(__name__)`.
- Log structured context (IDs, tool name) — not free-form sentences.
- `INFO` for normal lifecycle, `WARNING` for recoverable issues, `ERROR` for failures, `DEBUG` for tracing.

## Testing

- Use `pytest` + `pytest-asyncio` (or `anyio` mode).
- Mock `httpx` with `respx` or `httpx.MockTransport` — do not hit live upstream APIs in unit tests.
- Test tools at the MCP-facing function level: given args, assert the returned model.
- Keep tests next to the package they cover, under `tests/<domain>/test_*.py`.

## Tooling

- Use `uv` for everything: `uv sync`, `uv run`, `uv add <pkg>`.
- Use `ruff` for lint + format (`uv run ruff check`, `uv run ruff format`).
- Use `mypy` (strict on new code) once configured: `uv run mypy mcp_emp`.

## Code Quality

- Make the smallest change that fully solves the task.
- Do not refactor unrelated code without a clear payoff.
- Remove unused imports, dead branches, and abandoned scaffolding when you touch a file.
- Add brief comments only when the code would otherwise be hard to parse.
- **DRY:** extract shared logic only when the same code appears in two or more real callers; do not pre-abstract.
- **KISS:** prefer the simplest solution that fully works; avoid clever patterns, extra layers, or premature generalization.

## File Organization

- Package code lives under `mcp_emp/` (create the package as the project grows past `main.py`).
- Domain code lives under `mcp_emp/domains/<domain>/`.
- Infrastructure lives under `mcp_emp/core/`.
- Tests live under `tests/` mirroring the package structure.
- Integration notes live under `docs/`.

## Verification

- Use `uv run ruff check` and `uv run ruff format --check` after normal code changes.
- Use `uv run pytest` when touching domain logic, clients, or tool signatures.
- Use the MCP Inspector (or any MCP client) to smoke-test schema changes to tools.
- If a change is documentation-only, a manual verification pass is enough.

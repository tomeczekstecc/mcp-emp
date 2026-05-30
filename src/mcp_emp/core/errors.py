"""Application error classes — all tools raise these; decorators convert them.

The 17-code vocabulary maps to machine-readable strings the LLM can branch on.
See docs/08-error-model.md and ADR-0001.
"""

from __future__ import annotations


class EmpError(Exception):
    """Base class for all mcp-emp application errors.

    Attributes:
        code:     Stable string identifier (e.g. "TASK_NOT_FOUND").
        message:  English human-readable description.
        details:  Structured extra context (task_id, token, Polish original, …).
    """

    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, object] = details or {}


# ── Auth ────────────────────────────────────────────────────────────────────

class AuthMisconfigured(EmpError):
    """KC realm, client, or credentials are wrong (startup fatal)."""

    code = "AUTH_MISCONFIGURED"


class AuthExpired(EmpError):
    """Token could not be refreshed; user must restart."""

    code = "AUTH_EXPIRED"


# ── EMP connectivity ─────────────────────────────────────────────────────────

class EmpUnreachable(EmpError):
    """EMP API is not responding."""

    code = "EMP_UNREACHABLE"


class EmpParseError(EmpError):
    """EMP returned a shape we could not parse."""

    code = "EMP_PARSE_ERROR"


class EmpRejected(EmpError):
    """EMP rejected the request (4xx other than 401/404)."""

    code = "EMP_REJECTED"


# ── Resource ─────────────────────────────────────────────────────────────────

class TaskNotFound(EmpError):
    """Task does not exist or the caller cannot access it."""

    code = "TASK_NOT_FOUND"

    def __init__(self, task_id: int) -> None:
        super().__init__(
            message=f"Task {task_id} not found.",
            details={"task_id": task_id},
        )


class InvalidTransition(EmpError):
    """The requested status transition is not allowed."""

    code = "INVALID_TRANSITION"

    def __init__(self, task_id: int, current: str, attempted: str) -> None:
        super().__init__(
            message=(
                f"Task {task_id} cannot transition from {current!r} "
                f"via operation {attempted!r}."
            ),
            details={
                "task_id": task_id,
                "current_status": current,
                "attempted_operation": attempted,
            },
        )


# ── Validation ───────────────────────────────────────────────────────────────

class ValidationFailed(EmpError):
    """Pre-flight validation failed; the EMP call was not made."""

    code = "VALIDATION_FAILED"


# ── Confirmation ─────────────────────────────────────────────────────────────

class ConfirmationRequired(EmpError):
    """Destructive operation requires a confirmation token.

    details keys: token, expires_at (ISO 8601), preview (dict).
    """

    code = "CONFIRMATION_REQUIRED"


class ConfirmationInvalid(EmpError):
    """The provided confirmation token is invalid, expired, or already used."""

    code = "CONFIRMATION_INVALID"


# ── Mode guards ───────────────────────────────────────────────────────────────

class ReadOnlyMode(EmpError):
    """The server is running in read-only mode; mutation refused."""

    code = "READ_ONLY"

    def __init__(self, operation: str) -> None:
        super().__init__(
            message=(
                f"Operation '{operation}' is not allowed in read-only mode. "
                "Set MCP_EMP_READ_ONLY=false to enable writes."
            ),
            details={"operation": operation},
        )

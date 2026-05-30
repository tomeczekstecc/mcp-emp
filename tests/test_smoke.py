"""Smoke test — basic package imports succeed."""


def test_core_errors_importable() -> None:
    from mcp_emp.core.errors import EmpError, ReadOnlyMode, TaskNotFound  # noqa: F401


def test_core_modes_importable() -> None:
    from mcp_emp.core.modes import mutating, readable  # noqa: F401


def test_domains_importable() -> None:
    from mcp_emp.domains.rejestr.contract import Task  # noqa: F401
    from mcp_emp.domains.rejestr.status import Status, resolve_status  # noqa: F401
    from mcp_emp.domains.slowniki.contract import Tag, TaskType  # noqa: F401


def test_status_alias_map() -> None:
    from mcp_emp.domains.rejestr.status import Status, resolve_status

    assert resolve_status("completed") == Status.ZAKONCZONE
    assert resolve_status("ZAKOŃCZONE") == Status.ZAKONCZONE
    assert resolve_status("draft") == Status.W_EDYCJI
    assert resolve_status("unknown_value") is None

"""Import-direction lint test.

Rules (from ADR-0002 and ddd-patterns.md):
- core must never import from domains
- slowniki must never import from rejestr
- rejestr may import from slowniki (pre-flight reads cached słowniki)
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).parent.parent.parent / "src" / "mcp_emp"


def _imports_in(path: Path) -> list[str]:
    """Return all dotted module names imported by *path*."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def _py_files(under: Path) -> list[Path]:
    return list(under.rglob("*.py"))


def test_core_does_not_import_domains() -> None:
    """core/ modules must never import from mcp_emp.domains.*"""
    core_dir = SRC / "core"
    violations: list[str] = []
    for py in _py_files(core_dir):
        for imp in _imports_in(py):
            if "mcp_emp.domains" in imp:
                violations.append(f"{py.relative_to(SRC)}: imports {imp!r}")
    assert not violations, "core imports from domains:\n" + "\n".join(violations)


def test_slowniki_does_not_import_rejestr() -> None:
    """slowniki/ must never import from mcp_emp.domains.rejestr.*"""
    slowniki_dir = SRC / "domains" / "slowniki"
    violations: list[str] = []
    for py in _py_files(slowniki_dir):
        for imp in _imports_in(py):
            if "mcp_emp.domains.rejestr" in imp:
                violations.append(f"{py.relative_to(SRC)}: imports {imp!r}")
    assert not violations, "slowniki imports from rejestr:\n" + "\n".join(violations)

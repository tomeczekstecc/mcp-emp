"""Rejestr contract — Payload (EMP wire shapes) and Model (MCP-facing) types.

All types are stubs until M2 captures live EMP fixtures and locks the shapes.
"""

from __future__ import annotations

from pydantic import BaseModel


class RejestrPayload(BaseModel):
    """Raw EMP rejestr response — shape TBD from captured fixtures (M2)."""

    id: int


class Task(BaseModel):
    """MCP-facing task model — fields added as fixtures are captured (M2)."""

    id: int

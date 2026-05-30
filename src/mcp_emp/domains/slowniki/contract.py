"""Słowniki contract — Payload and Model types for reference data.

Shapes confirmed from captured EMP fixtures in M2.
"""

from __future__ import annotations

from pydantic import BaseModel


class TaskTypePayload(BaseModel):
    """Raw EMP task-type entry — shape confirmed in M2."""

    id: int
    nazwa: str


class TaskType(BaseModel):
    """MCP-facing task type."""

    id: int
    name: str
    requires_time: bool = False
    requires_quantity: bool = False
    is_active: bool = True


class TagPayload(BaseModel):
    """Raw EMP tag entry — shape confirmed in M2."""

    id: int
    nazwa: str


class Tag(BaseModel):
    """MCP-facing tag."""

    id: int
    name: str
    is_active: bool = True

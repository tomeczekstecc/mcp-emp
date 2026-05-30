"""Confirmation token store — in-memory, TTL, single-use, payload-hash bound.

See docs/08-error-model.md §7 and ADR-0001 for the full token contract.
Implemented in M6.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time as _time

_store: dict[str, _TokenEntry] = {}
_lock = asyncio.Lock()

TOKEN_TTL = 300  # 5 minutes


class _TokenEntry:
    def __init__(self, op: str, resource_id: int, payload_hash: str) -> None:
        self.op = op
        self.resource_id = resource_id
        self.payload_hash = payload_hash
        self.expires_at = _time.time() + TOKEN_TTL
        self.used = False


def _payload_hash(payload: dict[str, object]) -> str:
    """Return a sha256[:16] hex digest of the canonical JSON of *payload*."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


async def issue(op: str, resource_id: int, payload: dict[str, object]) -> str:
    """Issue and store a new confirmation token; return the token string."""
    async with _lock:
        token = f"{op}_{resource_id}_{secrets.token_hex(4)}"
        _store[token] = _TokenEntry(op, resource_id, _payload_hash(payload))
        return token


async def consume(
    token: str,
    op: str,
    resource_id: int,
    payload: dict[str, object],
) -> None:
    """Validate and consume *token*.

    Raises ConfirmationInvalid with a reason on any failure.
    """
    from mcp_emp.core.errors import ConfirmationInvalid  # noqa: PLC0415

    async with _lock:
        entry = _store.get(token)
        if entry is None:
            raise ConfirmationInvalid("Token not found.", {"reason": "unknown"})
        if entry.used:
            raise ConfirmationInvalid("Token already used.", {"reason": "used"})
        if _time.time() > entry.expires_at:
            del _store[token]
            raise ConfirmationInvalid("Token expired.", {"reason": "expired"})
        if entry.op != op or entry.resource_id != resource_id:
            raise ConfirmationInvalid("Token scope mismatch.", {"reason": "scope"})
        if entry.payload_hash != _payload_hash(payload):
            raise ConfirmationInvalid("Payload hash mismatch.", {"reason": "hash"})
        entry.used = True
        del _store[token]

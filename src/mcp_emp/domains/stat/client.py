"""Stat async HTTP client."""

from __future__ import annotations

from mcp_emp.core.auth import get_auth
from mcp_emp.core.errors import EmpRejected
from mcp_emp.core.http import get_client
from mcp_emp.domains.stat.contract import (
    CycleStats,
    CycleStatsPayload,
    DailyStats,
    DailyStatsPayload,
)
from mcp_emp.domains.stat.mapper import map_cycle_stats, map_daily_stats


async def _bearer() -> dict[str, str]:
    token = await get_auth().get_token()
    return {"Authorization": f"Bearer {token}"}


async def fetch_cycle_stats(scope: str = "") -> CycleStats:
    """Fetch cycle point summaries.

    scope: "" (own), "kierownik", "dyrektor", "zarzad"
    """
    path = f"/rejestr/{scope}/stat/cykle" if scope else "/rejestr/stat/cykle"
    r = await get_client().get(path, headers=await _bearer())
    if r.status_code != 200:
        raise EmpRejected(f"EMP {r.status_code} on {path}",
                          {"status_code": r.status_code})
    return map_cycle_stats(CycleStatsPayload.model_validate(r.json()))


async def fetch_daily_stats(scope: str = "") -> DailyStats:
    """Fetch today's completed tasks."""
    path = f"/rejestr/{scope}/stat/dzienny" if scope else "/rejestr/stat/dzienny"
    r = await get_client().get(path, headers=await _bearer())
    if r.status_code != 200:
        raise EmpRejected(f"EMP {r.status_code} on {path}",
                          {"status_code": r.status_code})
    return map_daily_stats(DailyStatsPayload.model_validate(r.json()))

"""Tests for stat mapper."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_emp.domains.stat.contract import CycleStatsPayload, DailyStatsPayload
from mcp_emp.domains.stat.mapper import map_cycle_stats, map_daily_stats

FIXTURES = Path(__file__).parent


def test_cycle_stats_from_fixture() -> None:
    raw = json.loads((FIXTURES / "cykle.json").read_text(encoding="utf-8"))
    stats = map_cycle_stats(CycleStatsPayload.model_validate(raw))
    assert len(stats.cycles) > 0
    first = stats.cycles[0]
    assert isinstance(first.cycle, int)
    assert first.cycle > 0


def test_daily_stats_from_fixture() -> None:
    raw = json.loads((FIXTURES / "dzienny.json").read_text(encoding="utf-8"))
    stats = map_daily_stats(DailyStatsPayload.model_validate(raw))
    assert stats.total_tasks > 0
    assert stats.total_points >= 0
    assert stats.date  # today's date
    assert all(isinstance(t.tags, list) for t in stats.tasks)

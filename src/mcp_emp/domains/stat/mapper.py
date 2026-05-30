"""Stat mapper — Payload → Model."""

from __future__ import annotations

from datetime import date

from mcp_emp.domains.stat.contract import (
    CyclePoints,
    CycleStats,
    CycleStatsPayload,
    DailyStats,
    DailyStatsPayload,
    DailyTask,
    DailyTaskPayload,
    TeamCycleStats,
    TeamCycleStatsPayload,
)


def map_cycle_stats(p: CycleStatsPayload) -> CycleStats:
    return CycleStats(
        cycles=[
            CyclePoints(
                cycle=c.nr_cyklu,
                points_default=c.suma_domyslne,
                points_manager=c.suma_przelozony,
                points_employee=c.suma_pracownik,
            )
            for c in p.cykle_zaspol_punkty
        ]
    )


def map_daily_task(p: DailyTaskPayload) -> DailyTask:
    return DailyTask(
        id=p.id,
        task_type=p.slownik_typ_zadania_nazwa,
        subject=p.dotyczy,
        started_at=p.data_rozpoczecia,
        completed_at=p.data_zakonczenia,
        points=p.punkty,
        points_weighted=p.punkty_wagi,
        quantity=p.ilosc,
        time=p.czas,
        sod_number=p.nr_sprawy_sod,
        tags=p.tags if p.tags else [],
    )


def map_daily_stats(p: DailyStatsPayload) -> DailyStats:
    tasks = [map_daily_task(t) for t in p.moje]
    total = sum(t.points or 0 for t in tasks)
    return DailyStats(
        date=date.today().isoformat(),
        tasks=tasks,
        total_points=total,
        total_tasks=len(tasks),
    )


def map_team_cycle_stats(p: TeamCycleStatsPayload) -> TeamCycleStats:
    from mcp_emp.domains.stat.contract import TeamCycleStats  # noqa: PLC0415
    return TeamCycleStats(
        cycles=[
            CyclePoints(
                cycle=c.nr_cyklu,
                points_default=c.suma_domyslne,
                points_manager=c.suma_przelozony,
                points_employee=c.suma_pracownik,
            )
            for c in p.cykle_zaspol_punkty
        ],
        employee_points=[dict(r) for r in p.cykle_pracownicy_punkty_kier],
        task_counts=[dict(r) for r in p.cykle_liczba],
        team_task_counts=[dict(r) for r in p.cykle_liczba_zespol],
        tag_breakdown=[dict(r) for r in p.cykle_tagi],
    )

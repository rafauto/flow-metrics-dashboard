"""Shared fixtures: a tiny board whose metrics were calculated by hand."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from flow_metrics.workflow import load_workflow

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def day(n: int, hour: int = 0) -> pd.Timestamp:
    """Day 1 is Monday 2026-03-02."""
    return pd.Timestamp("2026-03-01") + pd.Timedelta(days=n, hours=hour)


def transitions_from(rows: list[tuple]) -> pd.DataFrame:
    """Rows: (item_id, item_type, created_day, from_status, to_status, changed_day)."""
    return pd.DataFrame(
        [
            {
                "item_id": item_id,
                "item_type": item_type,
                "created_at": day(created),
                "from_status": from_status,
                "to_status": to_status,
                "changed_at": day(changed),
            }
            for item_id, item_type, created, from_status, to_status, changed in rows
        ]
    )


@pytest.fixture
def workflow():
    return load_workflow()


@pytest.fixture
def small_board() -> pd.DataFrame:
    """
    A: created d1, start d3, blocked d5-d6, done d8 -> lead 7, cycle 5, active 4, waiting 1
    B: created d2, start d4, still in progress at d10 -> age 6
    C: created d1, start d2, done d4, reopened d6 -> not done, in progress
    D: created d1, done d2 without being started -> lead 1, no cycle time
    E: created d9, still in backlog
    as_of = d10
    """
    return transitions_from(
        [
            ("A", "Story", 1, None, "To Do", 1),
            ("A", "Story", 1, "To Do", "In Progress", 3),
            ("A", "Story", 1, "In Progress", "Blocked", 5),
            ("A", "Story", 1, "Blocked", "In Progress", 6),
            ("A", "Story", 1, "In Progress", "Done", 8),
            ("B", "Bug", 2, None, "To Do", 2),
            ("B", "Bug", 2, "To Do", "In Progress", 4),
            ("C", "Story", 1, None, "To Do", 1),
            ("C", "Story", 1, "To Do", "In Progress", 2),
            ("C", "Story", 1, "In Progress", "Done", 4),
            ("C", "Story", 1, "Done", "In Progress", 6),
            ("D", "Task", 1, None, "To Do", 1),
            ("D", "Task", 1, "To Do", "Done", 2),
            ("E", "Task", 9, None, "To Do", 9),
            ("E", "Task", 9, "To Do", "To Do", 10),
        ]
    )

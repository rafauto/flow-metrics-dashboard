"""Unit tests for the metric definitions, checked against hand-calculated values."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from flow_metrics.metrics import (
    analyze,
    average_weekly_throughput,
    overall_flow_efficiency,
    percentiles,
    throughput_weekly,
)
from tests.conftest import day


@pytest.fixture
def report(small_board, workflow):
    return analyze(small_board, workflow, as_of=day(10))


def item(report, item_id: str) -> pd.Series:
    return report.items.set_index("item_id").loc[item_id]


def test_lead_and_cycle_time_of_a_finished_item(report):
    a = item(report, "A")
    assert a["lead_time_days"] == 7
    assert a["cycle_time_days"] == 5


def test_active_and_waiting_time_split(report):
    a = item(report, "A")
    assert a["active_days"] == 4
    assert a["waiting_days"] == 1
    assert a["flow_efficiency"] == pytest.approx(0.8)


def test_item_finished_without_starting_has_lead_time_but_no_cycle_time(report):
    d = item(report, "D")
    assert d["lead_time_days"] == 1
    assert math.isnan(d["cycle_time_days"])


def test_reopened_item_is_not_done(report):
    """Regression: an item moved back from Done must count as work in progress."""
    c = item(report, "C")
    assert pd.isna(c["done_at"])
    assert c["current_category"] == "active"
    assert "C" in set(report.aging_wip["item_id"])


def test_current_wip_and_aging(report):
    aging = report.aging_wip.set_index("item_id")["age_days"]
    assert set(aging.index) == {"B", "C"}
    assert aging["B"] == 6
    assert aging["C"] == 8  # first started on day 2
    assert report.summary.current_wip == 2


def test_summary_counts(report):
    assert report.summary.items_total == 5
    assert report.summary.items_done == 2


def test_daily_wip_counts_items_at_end_of_day(report):
    wip = report.wip.set_index("date")["wip"]
    # End of day 3: A (started d3) and C (started d2) are in progress.
    assert wip[day(3)] == 2
    # End of day 4: A, B in progress; C finished on day 4.
    assert wip[day(4)] == 2
    # End of day 6: A (back in progress), B, C (reopened).
    assert wip[day(6)] == 3


def test_cumulative_flow_accounts_for_every_created_item(report):
    cfd = report.cfd.set_index("date")
    totals = cfd[["backlog", "active", "waiting", "done"]].sum(axis=1)
    assert totals[day(1)] == 3  # A, C, D
    assert totals[day(10)] == 5
    assert cfd.loc[day(5), "waiting"] == 1  # A blocked


def test_percentiles_use_observed_values():
    values = pd.Series(range(1, 11), dtype=float)
    assert percentiles(values) == {50: 6.0, 85: 9.0, 95: 10.0}


def test_percentiles_of_empty_series_are_nan():
    assert all(math.isnan(v) for v in percentiles(pd.Series([], dtype=float)).values())


def test_throughput_includes_empty_weeks_and_flags_partial_week():
    items = pd.DataFrame({"done_at": [day(1), day(2), day(16)]})  # weeks of d1 and d15
    weekly = throughput_weekly(items, as_of=day(17))
    assert weekly["items_done"].tolist() == [2, 0, 1]
    assert weekly["is_partial_week"].tolist() == [False, False, True]
    assert average_weekly_throughput(weekly) == 1.0


def test_overall_flow_efficiency_is_weighted_by_time():
    items = pd.DataFrame(
        {"cycle_time_days": [1.0, 9.0], "active_days": [1.0, 3.0], "waiting_days": [0.0, 6.0]}
    )
    assert overall_flow_efficiency(items) == pytest.approx(0.4)


def test_default_as_of_is_latest_timestamp(small_board, workflow):
    assert analyze(small_board, workflow).summary.as_of == day(10)

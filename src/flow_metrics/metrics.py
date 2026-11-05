"""Flow metrics computed from intervals and per-item facts. All functions are pure."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from flow_metrics.timeline import DAY, build_intervals, build_items, default_as_of
from flow_metrics.workflow import IN_PROGRESS, Category, Workflow

PERCENTILES = (50, 85, 95)
IN_PROGRESS_VALUES = [c.value for c in IN_PROGRESS]
# Bottom-to-top order of the cumulative flow diagram.
CATEGORY_ORDER = [
    Category.DONE.value,
    Category.WAITING.value,
    Category.ACTIVE.value,
    Category.BACKLOG.value,
]


@dataclass(frozen=True)
class FlowSummary:
    items_total: int
    items_done: int
    lead_time_percentiles: dict[int, float]
    cycle_time_percentiles: dict[int, float]
    throughput_per_week: float
    current_wip: int
    flow_efficiency: float
    as_of: pd.Timestamp


@dataclass(frozen=True)
class FlowReport:
    items: pd.DataFrame
    intervals: pd.DataFrame
    throughput: pd.DataFrame
    wip: pd.DataFrame
    cfd: pd.DataFrame
    aging_wip: pd.DataFrame
    summary: FlowSummary


def percentiles(values: pd.Series, levels: tuple[int, ...] = PERCENTILES) -> dict[int, float]:
    """'85% of items took X days or less'. Uses observed values (no interpolation)."""
    clean = values.dropna()
    if clean.empty:
        return {level: float("nan") for level in levels}
    return {level: float(clean.quantile(level / 100, interpolation="higher")) for level in levels}


def throughput_weekly(items: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Items finished per week (weeks start on Monday). Weeks with zero items are included."""
    done = items["done_at"].dropna()
    columns = ["week_start", "items_done", "is_partial_week"]
    if done.empty:
        return pd.DataFrame(columns=columns)
    weeks = _week_start(done)
    all_weeks = pd.date_range(weeks.min(), _week_start(pd.Series([as_of])).iloc[0], freq="7D")
    counts = weeks.value_counts().reindex(all_weeks, fill_value=0).sort_index()
    out = counts.rename_axis("week_start").reset_index(name="items_done")
    out["is_partial_week"] = out["week_start"] + 7 * DAY > as_of
    return out[columns]


def average_weekly_throughput(throughput: pd.DataFrame) -> float:
    """Mean of complete weeks only, so the current, unfinished week does not drag it down."""
    complete = throughput.loc[~throughput["is_partial_week"].astype(bool), "items_done"]
    return float(complete.mean()) if not complete.empty else float("nan")


def daily_snapshots(intervals: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Number of items in each category at the end of every day (the input for WIP and CFD)."""
    if intervals.empty:
        return pd.DataFrame(columns=["date", *CATEGORY_ORDER])
    days = pd.date_range(intervals["start"].min().normalize(), as_of.normalize(), freq="D")
    starts = intervals["start"].to_numpy()
    ends = intervals["end"].fillna(pd.Timestamp.max).to_numpy()
    categories = intervals["category"].to_numpy()
    rows = []
    for day in days:
        # The state just before midnight: a change at exactly 00:00 belongs to the next day.
        instant = min(day + DAY, as_of).to_datetime64()
        current = categories[(starts < instant) & (ends >= instant)]
        counts = pd.Series(current).value_counts()
        rows.append({"date": day, **{c: int(counts.get(c, 0)) for c in CATEGORY_ORDER}})
    return pd.DataFrame(rows)


def wip_daily(snapshots: pd.DataFrame) -> pd.DataFrame:
    """Work in progress per day: items started but not finished (active + waiting)."""
    out = snapshots[["date"]].copy()
    out["wip"] = snapshots[IN_PROGRESS_VALUES].sum(axis=1).astype(int)
    return out


def aging_wip(items: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Items in progress now and how many days since they started, oldest first."""
    wip = items[items["current_category"].isin(IN_PROGRESS_VALUES)].copy()
    wip["age_days"] = (as_of - wip["started_at"]) / DAY
    columns = ["item_id", "item_type", "current_status", "current_category", "age_days"]
    return wip.sort_values("age_days", ascending=False)[columns].reset_index(drop=True)


def overall_flow_efficiency(items: pd.DataFrame) -> float:
    """Total active time / total started time, over finished items (weighted by duration)."""
    done = items[items["cycle_time_days"].notna()]
    active, waiting = done["active_days"].sum(), done["waiting_days"].sum()
    return float(active / (active + waiting)) if active + waiting > 0 else float("nan")


def analyze(
    transitions: pd.DataFrame, workflow: Workflow, as_of: pd.Timestamp | None = None
) -> FlowReport:
    """Run the whole pipeline: transitions -> intervals -> items -> metrics."""
    as_of = as_of if as_of is not None else default_as_of(transitions)
    intervals = build_intervals(transitions, workflow)
    items = build_items(intervals, as_of)
    throughput = throughput_weekly(items, as_of)
    snapshots = daily_snapshots(intervals, as_of)
    aging = aging_wip(items, as_of)
    summary = FlowSummary(
        items_total=len(items),
        items_done=int(items["done_at"].notna().sum()),
        lead_time_percentiles=percentiles(items["lead_time_days"]),
        cycle_time_percentiles=percentiles(items["cycle_time_days"]),
        throughput_per_week=average_weekly_throughput(throughput),
        current_wip=len(aging),
        flow_efficiency=overall_flow_efficiency(items),
        as_of=as_of,
    )
    return FlowReport(
        items=items,
        intervals=intervals,
        throughput=throughput,
        wip=wip_daily(snapshots),
        cfd=snapshots,
        aging_wip=aging,
        summary=summary,
    )


def _week_start(timestamps: pd.Series) -> pd.Series:
    days = timestamps.dt.normalize()
    return days - pd.to_timedelta(days.dt.weekday, unit="D")

"""Turn status transitions into time intervals and per-item facts.

An interval is a period an item spent in one status. Every metric is computed from intervals.
"""

from __future__ import annotations

import pandas as pd

from flow_metrics.workflow import IN_PROGRESS, Category, Workflow

DAY = pd.Timedelta(days=1)

INTERVAL_COLUMNS = ["item_id", "item_type", "status", "category", "start", "end"]
ITEM_COLUMNS = [
    "item_id",
    "item_type",
    "current_status",
    "current_category",
    "created_at",
    "started_at",
    "done_at",
    "lead_time_days",
    "cycle_time_days",
    "active_days",
    "waiting_days",
    "flow_efficiency",
]


def default_as_of(transitions: pd.DataFrame) -> pd.Timestamp:
    """The latest timestamp in the data. Using it (not 'now') keeps results reproducible."""
    return max(transitions["changed_at"].max(), transitions["created_at"].max())


def build_intervals(transitions: pd.DataFrame, workflow: Workflow) -> pd.DataFrame:
    """One row per (item, status) period. The last interval of each item is open (end = NaT)."""
    workflow.require_known(_statuses(transitions))
    rows: list[dict] = []
    for item_id, group in transitions.groupby("item_id", sort=False):
        rows.extend(_item_intervals(item_id, group, workflow))
    intervals = pd.DataFrame(rows, columns=INTERVAL_COLUMNS)
    intervals["start"] = pd.to_datetime(intervals["start"])
    intervals["end"] = pd.to_datetime(intervals["end"])
    return intervals


def build_items(intervals: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Per-item facts: when it was created, started and finished, and how long it took."""
    rows = [_item_facts(group, as_of) for _, group in intervals.groupby("item_id", sort=False)]
    items = pd.DataFrame(rows, columns=ITEM_COLUMNS)
    for column in ("created_at", "started_at", "done_at"):
        items[column] = pd.to_datetime(items[column])
    for column in ITEM_COLUMNS[7:]:
        items[column] = pd.to_numeric(items[column])
    return items


def _statuses(transitions: pd.DataFrame) -> set[str]:
    return set(transitions["to_status"].dropna()) | set(transitions["from_status"].dropna())


def _item_intervals(item_id: str, group: pd.DataFrame, workflow: Workflow) -> list[dict]:
    group = group.sort_values("changed_at", kind="stable")
    item_type = group["item_type"].iloc[0]
    created_at = min(group["created_at"].min(), group["changed_at"].min())
    first = group.iloc[0]

    # (status, start) pairs; the item is in `status` from `start` until the next pair.
    periods: list[tuple[str, pd.Timestamp]] = []
    if pd.notna(first["from_status"]) and first["changed_at"] > created_at:
        periods.append((first["from_status"], created_at))
    periods.extend(zip(group["to_status"], group["changed_at"], strict=True))

    rows = []
    for index, (status, start) in enumerate(periods):
        end = periods[index + 1][1] if index + 1 < len(periods) else pd.NaT
        if pd.notna(end) and end <= start:
            continue  # zero-length period (two changes at the same instant)
        rows.append(
            {
                "item_id": item_id,
                "item_type": item_type,
                "status": status,
                "category": workflow.category_of(status).value,
                "start": start,
                "end": end,
            }
        )
    return rows


def _item_facts(group: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    group = group.sort_values("start")
    created_at = group["start"].iloc[0]
    last = group.iloc[-1]
    started = group.loc[group["category"].isin([c.value for c in IN_PROGRESS]), "start"]
    started_at = started.iloc[0] if not started.empty else pd.NaT
    done_at = _done_at(group)

    end_of_work = done_at if pd.notna(done_at) else as_of
    active = _days_in(group, Category.ACTIVE, started_at, end_of_work)
    waiting = _days_in(group, Category.WAITING, started_at, end_of_work)
    is_done = pd.notna(done_at)
    has_cycle = is_done and pd.notna(started_at)
    return {
        "item_id": last["item_id"],
        "item_type": last["item_type"],
        "current_status": last["status"],
        "current_category": last["category"],
        "created_at": created_at,
        "started_at": started_at,
        "done_at": done_at,
        "lead_time_days": (done_at - created_at) / DAY if is_done else float("nan"),
        "cycle_time_days": (done_at - started_at) / DAY if has_cycle else float("nan"),
        "active_days": active,
        "waiting_days": waiting,
        "flow_efficiency": active / (active + waiting)
        if has_cycle and active + waiting > 0
        else float("nan"),
    }


def _done_at(group: pd.DataFrame) -> pd.Timestamp:
    """Start of the trailing run of 'done' intervals; NaT if the item is not done now."""
    done_at = pd.NaT
    for _, row in group.iloc[::-1].iterrows():
        if row["category"] != Category.DONE.value:
            break
        done_at = row["start"]
    return done_at


def _days_in(
    group: pd.DataFrame, category: Category, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    if pd.isna(start):
        return 0.0
    rows = group[group["category"] == category.value]
    if rows.empty:
        return 0.0
    clipped_start = rows["start"].clip(lower=start)
    clipped_end = rows["end"].fillna(end).clip(upper=end)
    return float(((clipped_end - clipped_start).clip(lower=pd.Timedelta(0)) / DAY).sum())

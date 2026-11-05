"""Fictional sample data: a software team's board over about four months.

Uses random.Random with a fixed seed, so the same seed always produces the same files.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

AS_OF = datetime(2026, 10, 30, 18, 0)
HISTORY_WEEKS = 18

ITEM_TYPES = (("Story", 0.55), ("Bug", 0.25), ("Task", 0.20))
# Mean days spent in each step for a Story; Bugs and Tasks are faster.
MEAN_DAYS = {
    "To Do": 6.0,
    "In Progress": 2.5,
    "Blocked": 3.0,
    "Waiting for Review": 1.2,
    "In Review": 0.6,
    "Ready for Deploy": 1.5,
}
SPEED = {"Story": 1.0, "Bug": 0.6, "Task": 0.7}
BLOCKED_CHANCE = 0.15
REWORK_CHANCE = 0.15

AZURE_STATES = {
    "To Do": "New",
    "In Progress": "Active",
    "Blocked": "On Hold",
    "Waiting for Review": "Ready for Review",
    "In Review": "Code Review",
    "Ready for Deploy": "Ready for Deploy",
    "Done": "Closed",
}
AZURE_TYPES = {"Story": "User Story", "Bug": "Bug", "Task": "Task"}

FILE_NAMES = {
    "canonical": "sample_transitions.csv",
    "jira": "sample_jira_export.csv",
    "azure": "sample_azure_devops_export.csv",
}


@dataclass(frozen=True)
class SampleConfig:
    seed: int = 42
    n_items: int = 140
    as_of: datetime = AS_OF
    history_weeks: int = HISTORY_WEEKS


def generate_transitions(config: SampleConfig | None = None) -> pd.DataFrame:
    """Canonical transitions for a fictional team, cut off at config.as_of."""
    config = config or SampleConfig()
    rng = random.Random(config.seed)
    start = config.as_of - timedelta(weeks=config.history_weeks)
    span_minutes = int((config.as_of - start).total_seconds() // 60)

    rows = []
    for number in range(1, config.n_items + 1):
        item_type = rng.choices([t for t, _ in ITEM_TYPES], [w for _, w in ITEM_TYPES])[0]
        created = start + timedelta(minutes=rng.randrange(span_minutes))
        created = created.replace(second=0, microsecond=0)
        item_id = f"FLOW-{100 + number}"
        rows.extend(_item_rows(rng, item_id, item_type, created, config.as_of))
    return pd.DataFrame(rows).sort_values(["item_id", "changed_at"]).reset_index(drop=True)


def to_jira_export(transitions: pd.DataFrame) -> pd.DataFrame:
    """Jira-style status history: one row per change, issues without changes get one blank row."""
    current = transitions.groupby("item_id")["to_status"].last()
    changes = transitions[transitions["from_status"].notna()]
    unchanged = transitions[~transitions["item_id"].isin(changes["item_id"])]
    unchanged = unchanged.assign(from_status=None, to_status=None, changed_at=None)
    rows = pd.concat([changes, unchanged]).sort_values(["item_id", "created_at"], kind="stable")
    return pd.DataFrame(
        {
            "Issue key": rows["item_id"],
            "Issue Type": rows["item_type"],
            "Status": rows["item_id"].map(current),
            "Created": _fmt(rows["created_at"]),
            "From Status": rows["from_status"],
            "To Status": rows["to_status"],
            "Status Changed": _fmt(rows["changed_at"]),
        }
    ).reset_index(drop=True)


def to_azure_export(transitions: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Azure DevOps-style revisions, including revisions that only edit other fields."""
    rng = random.Random(seed)
    rows = []
    for item_id, group in transitions.groupby("item_id", sort=True):
        work_item_id = 1000 + int(str(item_id).split("-")[1])
        changes = list(group.itertuples(index=False))
        for index, change in enumerate(changes):
            state = AZURE_STATES[change.to_status]
            rows.append((work_item_id, change, state, change.changed_at))
            next_change = changes[index + 1].changed_at if index + 1 < len(changes) else None
            if next_change is not None and rng.random() < 0.3:
                midpoint = change.changed_at + (next_change - change.changed_at) / 2
                rows.append((work_item_id, change, state, midpoint))  # e.g. a title edit
    return pd.DataFrame(
        {
            "ID": [r[0] for r in rows],
            "Work Item Type": [AZURE_TYPES[r[1].item_type] for r in rows],
            "State": [r[2] for r in rows],
            "Created Date": _iso([r[1].created_at for r in rows]),
            "Changed Date": _iso([r[3] for r in rows]),
        }
    )


def write_samples(output_dir: Path, config: SampleConfig | None = None) -> dict[str, Path]:
    """Write the three sample files and return their paths by format."""
    config = config or SampleConfig()
    output_dir.mkdir(parents=True, exist_ok=True)
    transitions = generate_transitions(config)
    frames = {
        "canonical": transitions.assign(
            created_at=_fmt(transitions["created_at"]), changed_at=_fmt(transitions["changed_at"])
        ),
        "jira": to_jira_export(transitions),
        "azure": to_azure_export(transitions, config.seed),
    }
    paths = {}
    for key, frame in frames.items():
        path = output_dir / FILE_NAMES[key]
        frame.to_csv(path, index=False)
        paths[key] = path
    return paths


def _item_rows(
    rng: random.Random, item_id: str, item_type: str, created: datetime, as_of: datetime
) -> list[dict]:
    path = ["In Progress"]
    if rng.random() < BLOCKED_CHANCE:
        path += ["Blocked", "In Progress"]
    path += ["Waiting for Review", "In Review"]
    if rng.random() < REWORK_CHANCE:
        path += ["In Progress", "Waiting for Review", "In Review"]
    path += ["Ready for Deploy", "Done"]

    base = {"item_id": item_id, "item_type": item_type, "created_at": created}
    rows = [{**base, "from_status": None, "to_status": "To Do", "changed_at": created}]
    status, moment = "To Do", created
    for next_status in path:
        moment = moment + _duration(rng, status, item_type)
        if moment > as_of:
            break
        rows.append({**base, "from_status": status, "to_status": next_status, "changed_at": moment})
        status = next_status
    return rows


def _duration(rng: random.Random, status: str, item_type: str) -> timedelta:
    mean = MEAN_DAYS[status] * SPEED[item_type]
    days = rng.expovariate(1 / mean) + 0.05
    return timedelta(minutes=round(days * 24 * 60))


def _fmt(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values).dt.strftime("%Y-%m-%d %H:%M")


def _iso(values: list) -> list[str]:
    return [pd.Timestamp(v).strftime("%Y-%m-%dT%H:%M:%SZ") for v in values]

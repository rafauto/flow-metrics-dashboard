"""Jira-style status history export: one row per status change, plus the current status.

Expected columns: Issue key, Issue Type, Status, Created, From Status, To Status, Status Changed.
Issues that never changed status have one row with the transition columns empty.
"""

from __future__ import annotations

import pandas as pd

from flow_metrics.adapters.base import clean_text, finalize, parse_datetimes, select_columns


class JiraAdapter:
    name = "Jira (status history)"
    required_columns = (
        "Issue key",
        "Issue Type",
        "Status",
        "Created",
        "From Status",
        "To Status",
        "Status Changed",
    )

    def to_transitions(self, raw: pd.DataFrame) -> pd.DataFrame:
        df = select_columns(raw, self.required_columns)
        rows = pd.DataFrame(
            {
                "item_id": clean_text(df["Issue key"]),
                "item_type": clean_text(df["Issue Type"]),
                "status": clean_text(df["Status"]),
                "created_at": parse_datetimes(df["Created"], "Created"),
                "from_status": clean_text(df["From Status"]),
                "to_status": clean_text(df["To Status"]),
                "changed_at": parse_datetimes(
                    df["Status Changed"], "Status Changed", allow_empty=True
                ),
            }
        )
        changes = rows[rows["changed_at"].notna()]
        creation = self._creation_rows(rows, changes)
        return finalize(pd.concat([creation, changes], ignore_index=True))

    @staticmethod
    def _creation_rows(rows: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
        """One row per issue with the status it was created in."""
        first_change = changes.sort_values("changed_at").groupby("item_id").head(1)
        initial = first_change.set_index("item_id")["from_status"]
        issues = rows.drop_duplicates("item_id").set_index("item_id")
        # Issues without changes were created in their current status.
        to_status = initial.reindex(issues.index).fillna(issues["status"])
        return pd.DataFrame(
            {
                "item_id": issues.index,
                "item_type": issues["item_type"].to_numpy(),
                "created_at": issues["created_at"].to_numpy(),
                "from_status": pd.NA,
                "to_status": to_status.to_numpy(),
                "changed_at": issues["created_at"].to_numpy(),
            }
        )

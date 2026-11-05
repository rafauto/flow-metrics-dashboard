"""Azure DevOps-style revisions export: one row per work item revision.

Expected columns: ID, Work Item Type, State, Created Date, Changed Date.
Revisions often change fields other than State, so consecutive rows with the same state are
collapsed and only real state changes become transitions.
"""

from __future__ import annotations

import pandas as pd

from flow_metrics.adapters.base import clean_text, finalize, parse_datetimes, select_columns


class AzureDevOpsAdapter:
    name = "Azure DevOps (revisions)"
    required_columns = ("ID", "Work Item Type", "State", "Created Date", "Changed Date")

    def to_transitions(self, raw: pd.DataFrame) -> pd.DataFrame:
        df = select_columns(raw, self.required_columns)
        revisions = pd.DataFrame(
            {
                "item_id": clean_text(df["ID"]),
                "item_type": clean_text(df["Work Item Type"]),
                "state": clean_text(df["State"]),
                "created_at": parse_datetimes(df["Created Date"], "Created Date"),
                "changed_at": parse_datetimes(df["Changed Date"], "Changed Date"),
            }
        ).sort_values(["item_id", "changed_at"], kind="stable")

        previous = revisions.groupby("item_id")["state"].shift()
        is_first = previous.isna()
        changed = is_first | (revisions["state"] != previous)
        kept = revisions[changed].copy()
        kept["from_status"] = previous[changed]
        # The first revision records the state the item was created in.
        kept.loc[is_first[changed], "changed_at"] = kept.loc[is_first[changed], "created_at"]
        kept = kept.rename(columns={"state": "to_status"})
        return finalize(kept)

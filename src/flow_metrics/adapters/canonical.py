"""The canonical format: item_id, item_type, created_at, from_status, to_status, changed_at."""

from __future__ import annotations

import pandas as pd

from flow_metrics.adapters.base import (
    TRANSITION_COLUMNS,
    clean_text,
    finalize,
    parse_datetimes,
    select_columns,
)


class CanonicalAdapter:
    name = "Canonical transitions"
    required_columns = tuple(TRANSITION_COLUMNS)

    def to_transitions(self, raw: pd.DataFrame) -> pd.DataFrame:
        df = select_columns(raw, self.required_columns)
        out = pd.DataFrame(
            {
                "item_id": clean_text(df["item_id"]),
                "item_type": clean_text(df["item_type"]),
                "created_at": parse_datetimes(df["created_at"], "created_at"),
                "from_status": clean_text(df["from_status"]),
                "to_status": clean_text(df["to_status"]),
                "changed_at": parse_datetimes(df["changed_at"], "changed_at"),
            }
        )
        return finalize(out)

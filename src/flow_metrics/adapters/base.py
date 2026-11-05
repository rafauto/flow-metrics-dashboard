"""The canonical transitions format and the adapter interface every export format implements."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from flow_metrics.errors import DataValidationError

# One row per status change. A row with an empty from_status marks the status an item was
# created in (changed_at == created_at). Item titles are deliberately not part of the format.
TRANSITION_COLUMNS = [
    "item_id",
    "item_type",
    "created_at",
    "from_status",
    "to_status",
    "changed_at",
]


class ExportAdapter(Protocol):
    """Converts one export format into the canonical transitions table."""

    name: str
    required_columns: tuple[str, ...]

    def to_transitions(self, raw: pd.DataFrame) -> pd.DataFrame: ...


def normalize_header(name: str) -> str:
    return " ".join(str(name).split()).casefold()


def select_columns(raw: pd.DataFrame, wanted: tuple[str, ...]) -> pd.DataFrame:
    """Pick the wanted columns (ignoring case and spaces) and rename them to the wanted names."""
    lookup = {normalize_header(c): c for c in raw.columns}
    missing = [w for w in wanted if normalize_header(w) not in lookup]
    if missing:
        raise DataValidationError("Missing required columns: " + ", ".join(missing) + ".")
    return raw[[lookup[normalize_header(w)] for w in wanted]].set_axis(list(wanted), axis=1)


def has_columns(raw: pd.DataFrame, wanted: tuple[str, ...]) -> bool:
    present = {normalize_header(c) for c in raw.columns}
    return all(normalize_header(w) in present for w in wanted)


def parse_datetimes(values: pd.Series, column: str, *, allow_empty: bool = False) -> pd.Series:
    """Parse dates, converting time zones to naive UTC.

    ISO 8601 (2026-03-15 14:30) is recommended; ambiguous dates like 01/07/2026 are read
    month-first, as pandas does by default.
    """
    text = values.astype("string").str.strip()
    empty = text.isna() | (text == "")
    parsed = pd.to_datetime(text.where(~empty), errors="coerce", utc=True, format="mixed")
    bad = parsed.isna() & ~empty
    if bad.any():
        examples = ", ".join(repr(v) for v in text[bad].head(3))
        raise DataValidationError(
            f"Column '{column}' has {int(bad.sum())} value(s) that are not valid dates "
            f"(for example {examples}). Use a format like 2026-03-15 14:30."
        )
    if empty.any() and not allow_empty:
        raise DataValidationError(f"Column '{column}' has {int(empty.sum())} empty value(s).")
    return parsed.dt.tz_convert(None)


def clean_text(values: pd.Series) -> pd.Series:
    text = values.astype("string").str.strip()
    return text.mask(text == "")


def finalize(transitions: pd.DataFrame) -> pd.DataFrame:
    """Order, de-duplicate and type-check a canonical transitions table."""
    if transitions.empty:
        raise DataValidationError("The file has no cards to analyze.")
    if transitions["item_id"].isna().any():
        raise DataValidationError("Some rows have an empty item id.")
    if transitions["to_status"].isna().any():
        raise DataValidationError("Some status changes have an empty target status.")
    out = transitions[TRANSITION_COLUMNS].copy()
    out["item_type"] = out["item_type"].fillna("Unknown")
    out = out.drop_duplicates().sort_values(["item_id", "changed_at"], kind="stable")
    return out.reset_index(drop=True)

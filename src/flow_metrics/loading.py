"""Read and validate an uploaded CSV before any metric is computed."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd

from flow_metrics.adapters import to_transitions
from flow_metrics.config import Settings
from flow_metrics.errors import DataValidationError


def read_csv_bytes(data: bytes, filename: str, settings: Settings) -> pd.DataFrame:
    """Validate type, size and shape, then parse the CSV with every column as text.

    The delimiter is detected, so files saved by Excel with ';' also work.
    """
    if Path(filename).suffix.lower() != ".csv":
        raise DataValidationError("Please upload a .csv file.")
    if len(data) == 0:
        raise DataValidationError("The file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise DataValidationError(
            f"The file is larger than {settings.max_upload_mb} MB. "
            "Export a shorter period or fewer projects."
        )
    try:
        raw = pd.read_csv(
            io.StringIO(_decode(data)), dtype=str, keep_default_na=False, sep=None, engine="python"
        )
    except (pd.errors.ParserError, csv.Error) as exc:
        raise DataValidationError(f"The file could not be read as CSV: {exc}") from exc
    if raw.empty:
        raise DataValidationError("The file has a header but no rows.")
    if len(raw) > settings.max_rows:
        raise DataValidationError(
            f"The file has {len(raw):,} rows; the limit is {settings.max_rows:,}."
        )
    return raw


def load_transitions_file(path: Path, settings: Settings) -> tuple[pd.DataFrame, str]:
    """Read a CSV from disk and convert it to canonical transitions."""
    raw = read_csv_bytes(path.read_bytes(), path.name, settings)
    return to_transitions(raw)


def _decode(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Common for files saved by Excel on Windows.
        return data.decode("cp1252", errors="replace")

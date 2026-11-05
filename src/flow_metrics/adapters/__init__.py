"""Export format adapters. Add a new format by implementing ExportAdapter and listing it here."""

from __future__ import annotations

import pandas as pd

from flow_metrics.adapters.azure_devops import AzureDevOpsAdapter
from flow_metrics.adapters.base import TRANSITION_COLUMNS, ExportAdapter, has_columns
from flow_metrics.adapters.canonical import CanonicalAdapter
from flow_metrics.adapters.jira import JiraAdapter
from flow_metrics.errors import DataValidationError

ADAPTERS: tuple[ExportAdapter, ...] = (CanonicalAdapter(), JiraAdapter(), AzureDevOpsAdapter())


def detect_adapter(raw: pd.DataFrame) -> ExportAdapter:
    for adapter in ADAPTERS:
        if has_columns(raw, adapter.required_columns):
            return adapter
    expected = "\n".join(f"- {a.name}: {', '.join(a.required_columns)}" for a in ADAPTERS)
    raise DataValidationError(
        "Could not recognize the export format. The file needs one of these column sets:\n"
        + expected
    )


def to_transitions(raw: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Detect the format and return (canonical transitions, format name)."""
    adapter = detect_adapter(raw)
    return adapter.to_transitions(raw), adapter.name


__all__ = ["ADAPTERS", "TRANSITION_COLUMNS", "ExportAdapter", "detect_adapter", "to_transitions"]

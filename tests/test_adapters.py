"""Unit tests for format detection and the export adapters."""

from __future__ import annotations

import pandas as pd
import pytest

from flow_metrics.adapters import detect_adapter, to_transitions
from flow_metrics.adapters.azure_devops import AzureDevOpsAdapter
from flow_metrics.adapters.jira import JiraAdapter
from flow_metrics.errors import DataValidationError

JIRA = pd.DataFrame(
    {
        "Issue key": ["T-1", "T-1", "T-2"],
        "Issue Type": ["Story", "Story", "Bug"],
        "Status": ["Done", "Done", "To Do"],
        "Created": ["2026-03-02 09:00", "2026-03-02 09:00", "2026-03-03 10:00"],
        "From Status": ["To Do", "In Progress", ""],
        "To Status": ["In Progress", "Done", ""],
        "Status Changed": ["2026-03-03 09:00", "2026-03-05 09:00", ""],
    }
)

AZURE = pd.DataFrame(
    {
        "ID": ["7", "7", "7", "7"],
        "Work Item Type": ["User Story"] * 4,
        "State": ["New", "Active", "Active", "Closed"],
        "Created Date": ["2026-03-02T09:00:00Z"] * 4,
        "Changed Date": [
            "2026-03-02T09:00:00Z",
            "2026-03-03T09:00:00Z",
            "2026-03-04T09:00:00Z",  # field edit only: same state
            "2026-03-05T09:00:00Z",
        ],
    }
)


def test_detects_each_format():
    assert isinstance(detect_adapter(JIRA), JiraAdapter)
    assert isinstance(detect_adapter(AZURE), AzureDevOpsAdapter)


def test_header_matching_ignores_case_and_spaces():
    renamed = JIRA.rename(columns={"Issue key": " issue KEY ", "Status Changed": "status changed"})
    assert isinstance(detect_adapter(renamed), JiraAdapter)


def test_unknown_format_lists_expected_columns():
    with pytest.raises(DataValidationError, match="Jira"):
        detect_adapter(pd.DataFrame({"foo": ["1"]}))


def test_jira_adds_creation_row_and_keeps_unchanged_issues():
    transitions, name = to_transitions(JIRA)
    assert name.startswith("Jira")
    t1 = transitions[transitions["item_id"] == "T-1"]
    assert t1["to_status"].tolist() == ["To Do", "In Progress", "Done"]
    assert pd.isna(t1["from_status"].iloc[0])
    t2 = transitions[transitions["item_id"] == "T-2"]
    assert t2["to_status"].tolist() == ["To Do"]


def test_azure_collapses_revisions_without_state_change():
    transitions, _ = to_transitions(AZURE)
    assert transitions["to_status"].tolist() == ["New", "Active", "Closed"]
    assert transitions["from_status"].tolist()[1:] == ["New", "Active"]


def test_time_zones_are_converted_to_utc():
    shifted = AZURE.assign(**{"Changed Date": AZURE["Changed Date"].str.replace("Z", "-03:00")})
    transitions, _ = to_transitions(shifted)
    assert transitions["changed_at"].iloc[1] == pd.Timestamp("2026-03-03 12:00")


def test_invalid_dates_are_reported_with_examples():
    broken = JIRA.assign(Created=["not a date", "2026-03-02 09:00", "2026-03-03 10:00"])
    with pytest.raises(DataValidationError, match="'Created'.*not a date"):
        to_transitions(broken)


def test_empty_item_id_is_rejected():
    broken = JIRA.assign(**{"Issue key": ["", "T-1", "T-2"]})
    with pytest.raises(DataValidationError, match="empty item id"):
        to_transitions(broken)

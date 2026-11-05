"""Unit tests for the status mapping, settings and CSV validation."""

from __future__ import annotations

import pytest

from flow_metrics.config import Settings, load_settings
from flow_metrics.errors import DataValidationError
from flow_metrics.loading import read_csv_bytes
from flow_metrics.workflow import Category, Workflow, load_workflow


def test_default_workflow_matches_ignoring_case_and_spaces(workflow):
    assert workflow.category_of("in  progress") is Category.ACTIVE
    assert workflow.category_of("BLOCKED") is Category.WAITING
    assert workflow.category_of("Mystery") is None


def test_overrides_map_custom_statuses(workflow):
    custom = workflow.with_overrides({"Mystery": Category.DONE})
    assert custom.category_of("mystery") is Category.DONE


def test_unknown_statuses_are_reported_by_name():
    with pytest.raises(DataValidationError, match="'Parked'"):
        Workflow.from_dict({"active": ["Doing"]}).require_known(["Doing", "Parked"])


def test_invalid_category_in_workflow_file(tmp_path):
    path = tmp_path / "workflow.yaml"
    path.write_text("ongoing:\n  - Doing\n")
    with pytest.raises(DataValidationError, match="ongoing"):
        load_workflow(path)


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv("FLOW_METRICS_MAX_UPLOAD_MB", "2")
    assert load_settings().max_upload_bytes == 2 * 1024 * 1024
    monkeypatch.setenv("FLOW_METRICS_MAX_UPLOAD_MB", "lots")
    with pytest.raises(ValueError, match="whole number"):
        load_settings()


@pytest.mark.parametrize(
    ("data", "filename", "message"),
    [
        (b"a,b\n1,2\n", "export.xlsx", r"\.csv"),
        (b"", "export.csv", "empty"),
        (b"a,b\n", "export.csv", "no rows"),
    ],
)
def test_rejects_invalid_files(data, filename, message):
    with pytest.raises(DataValidationError, match=message):
        read_csv_bytes(data, filename, Settings())


def test_rejects_files_over_the_size_limit():
    data = b"a,b\n" + b"1,2\n" * 300_000
    with pytest.raises(DataValidationError, match="larger than 1 MB"):
        read_csv_bytes(data, "export.csv", Settings(max_upload_mb=1))


def test_rejects_too_many_rows():
    with pytest.raises(DataValidationError, match="limit is 2"):
        read_csv_bytes(b"a\n1\n2\n3\n", "export.csv", Settings(max_rows=2))


def test_reads_semicolon_files_saved_by_excel():
    raw = read_csv_bytes("ID;State\n1;Ação\n".encode("cp1252"), "export.csv", Settings())
    assert raw.columns.tolist() == ["ID", "State"]
    assert raw["State"].iloc[0] == "Ação"

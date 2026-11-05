"""End-to-end tests: sample files -> adapters -> metrics -> CLI output."""

from __future__ import annotations

import pandas as pd
import pytest

from flow_metrics.cli import main
from flow_metrics.config import Settings
from flow_metrics.loading import load_transitions_file
from flow_metrics.metrics import analyze
from flow_metrics.sample_data import FILE_NAMES, SampleConfig, generate_transitions, write_samples
from tests.conftest import EXAMPLES


def test_sample_data_is_deterministic():
    first = generate_transitions(SampleConfig(seed=7, n_items=20))
    second = generate_transitions(SampleConfig(seed=7, n_items=20))
    pd.testing.assert_frame_equal(first, second)


def test_committed_examples_match_the_generator(tmp_path):
    """The files in examples/ must be reproducible with `flow-metrics sample`."""
    paths = write_samples(tmp_path)
    for key, path in paths.items():
        assert path.read_text() == (EXAMPLES / FILE_NAMES[key]).read_text(), key


def test_all_formats_produce_the_same_metrics(workflow):
    summaries = []
    for name in FILE_NAMES.values():
        transitions, _ = load_transitions_file(EXAMPLES / name, Settings())
        summaries.append(analyze(transitions, workflow).summary)
    assert summaries[0] == summaries[1] == summaries[2]


def test_cli_summary(capsys):
    assert main(["summary", str(EXAMPLES / "sample_jira_export.csv")]) == 0
    output = capsys.readouterr().out
    assert "Jira (status history)" in output
    assert "Cycle time p50/p85" in output


def test_cli_exports_per_item_metrics(tmp_path):
    target = tmp_path / "items.csv"
    args = ["summary", str(EXAMPLES / "sample_transitions.csv"), "--export", str(target)]
    assert main(args) == 0
    assert "cycle_time_days" in pd.read_csv(target).columns


def test_cli_reports_bad_files_without_traceback(tmp_path, caplog):
    bad = tmp_path / "bad.csv"
    bad.write_text("foo,bar\n1,2\n")
    assert main(["summary", str(bad)]) == 1
    assert "Could not recognize the export format" in caplog.text


@pytest.mark.parametrize("missing", ["missing.csv"])
def test_cli_missing_file(tmp_path, missing):
    assert main(["summary", str(tmp_path / missing)]) == 1

"""Smoke tests for the charts and the Streamlit app. They need the [app] extra installed."""

from __future__ import annotations

import pytest

from flow_metrics.config import Settings
from flow_metrics.loading import load_transitions_file
from flow_metrics.metrics import analyze
from tests.conftest import EXAMPLES, ROOT


@pytest.fixture(scope="module")
def report():
    from flow_metrics.workflow import load_workflow

    transitions, _ = load_transitions_file(EXAMPLES / "sample_jira_export.csv", Settings())
    return analyze(transitions, load_workflow())


def test_every_chart_builds(report):
    pytest.importorskip("plotly")
    from flow_metrics import charts

    s = report.summary
    figures = [
        charts.cycle_time_scatter(report.items, s.cycle_time_percentiles),
        charts.lead_time_histogram(report.items, s.lead_time_percentiles),
        charts.throughput_bars(report.throughput, s.throughput_per_week),
        charts.wip_line(report.wip),
        charts.cumulative_flow(report.cfd),
        charts.aging_wip_strip(report.aging_wip, s.cycle_time_percentiles),
    ]
    assert all(len(fig.data) > 0 for fig in figures)


def test_app_runs_end_to_end_in_demo_mode():
    pytest.importorskip("streamlit")
    pytest.importorskip("plotly")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert not app.error
    labels = [metric.label for metric in app.metric]
    assert labels == [
        "Lead time (85%)",
        "Cycle time (85%)",
        "Throughput / week",
        "WIP now",
        "Flow efficiency",
    ]


def test_app_asks_for_a_file_in_upload_mode():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value("Upload a CSV").run()
    assert not app.exception
    assert any("Upload a CSV" in info.value for info in app.info)

"""Streamlit UI. Only presentation lives here; every calculation is in the flow_metrics package."""

from __future__ import annotations

import logging
import math
import sys
from pathlib import Path

ROOT = Path(__file__).parent
# Lets the app run on Streamlit Community Cloud without installing the package (see ADR 0003).
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from flow_metrics import charts  # noqa: E402
from flow_metrics.adapters import to_transitions  # noqa: E402
from flow_metrics.config import load_settings  # noqa: E402
from flow_metrics.errors import DataValidationError  # noqa: E402
from flow_metrics.loading import read_csv_bytes  # noqa: E402
from flow_metrics.metrics import FlowReport, analyze  # noqa: E402
from flow_metrics.workflow import Category, Workflow, load_workflow  # noqa: E402

DEMO_FILE = ROOT / "examples" / "sample_jira_export.csv"
SAMPLE_FILES = {
    "Jira sample": ROOT / "examples" / "sample_jira_export.csv",
    "Azure DevOps sample": ROOT / "examples" / "sample_azure_devops_export.csv",
    "Canonical sample": ROOT / "examples" / "sample_transitions.csv",
}
CATEGORIES = [c.value for c in Category]

settings = load_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("flow_metrics.app")


@st.cache_data(show_spinner=False)
def parse_csv(data: bytes, filename: str) -> tuple[pd.DataFrame, str]:
    raw = read_csv_bytes(data, filename, settings)
    return to_transitions(raw)


def main() -> None:
    st.set_page_config(page_title="Flow Metrics Dashboard", page_icon="📊", layout="wide")
    st.title("📊 Flow Metrics Dashboard")
    st.caption(
        "Lead time, cycle time, throughput, WIP and flow efficiency from a Jira or "
        "Azure DevOps card export."
    )
    try:
        data = choose_data()
        if data is None:
            st.info("Upload a CSV in the sidebar, or switch to the demo data.")
            return
        transitions, source_format, is_demo = data
        workflow = map_statuses(transitions, load_workflow(settings.workflow_file))
        transitions = filter_item_types(transitions)
        report = analyze(transitions, workflow)
    except DataValidationError as exc:
        st.error(str(exc))
        return
    except Exception:  # last line of defense: log the details, show a friendly message
        logger.exception("Unexpected error while computing metrics")
        st.error("Something went wrong while reading this file. Check the format and try again.")
        return

    if is_demo:
        st.info("You are looking at fictional demo data. Upload your own export in the sidebar.")
    st.caption(
        f"Format: **{source_format}** · Data as of **{report.summary.as_of:%Y-%m-%d %H:%M}** "
        "(latest timestamp in the file)"
    )
    show_kpis(report)
    show_tabs(report)


def choose_data() -> tuple[pd.DataFrame, str, bool] | None:
    """Return (transitions, format name, is_demo), or None while waiting for an upload."""
    st.sidebar.header("Data")
    source = st.sidebar.radio("Source", ["Demo data", "Upload a CSV"], horizontal=True)
    if source == "Demo data":
        transitions, source_format = parse_csv(DEMO_FILE.read_bytes(), DEMO_FILE.name)
        return transitions, source_format, True

    upload = st.sidebar.file_uploader(
        f"Card export (.csv, up to {settings.max_upload_mb} MB)", type=["csv"]
    )
    with st.sidebar.expander("Accepted formats and samples"):
        st.markdown(
            "- **Jira status history**: Issue key, Issue Type, Status, Created, From Status, "
            "To Status, Status Changed\n"
            "- **Azure DevOps revisions**: ID, Work Item Type, State, Created Date, Changed Date\n"
            "- **Canonical**: item_id, item_type, created_at, from_status, to_status, changed_at"
        )
        for label, path in SAMPLE_FILES.items():
            st.download_button(label, path.read_bytes(), path.name, "text/csv", key=label)
    st.sidebar.caption(
        "Files are processed in memory and never stored. Only the columns above are used; "
        "remove titles and people's names before uploading."
    )
    if upload is None:
        return None
    transitions, source_format = parse_csv(upload.getvalue(), upload.name)
    return transitions, source_format, False


def map_statuses(transitions: pd.DataFrame, workflow: Workflow) -> Workflow:
    statuses = sorted(
        set(transitions["to_status"].dropna()) | set(transitions["from_status"].dropna())
    )
    unknown = set(workflow.unknown_statuses(statuses))
    with st.sidebar.expander("Status mapping", expanded=bool(unknown)):
        if unknown:
            st.warning("Some statuses are new to the app. Check their category below.")
        st.caption("Backlog = not started · Active = being worked on · Waiting = started but idle")
        overrides = {}
        for status in statuses:
            current = workflow.category_of(status) or Category.BACKLOG
            choice = st.selectbox(
                status, CATEGORIES, index=CATEGORIES.index(current.value), key=f"map-{status}"
            )
            overrides[status] = Category(choice)
    return workflow.with_overrides(overrides)


def filter_item_types(transitions: pd.DataFrame) -> pd.DataFrame:
    types = sorted(transitions["item_type"].unique())
    selected = st.sidebar.multiselect("Item types", types, default=types)
    if not selected:
        raise DataValidationError("Select at least one item type.")
    return transitions[transitions["item_type"].isin(selected)]


def show_kpis(report: FlowReport) -> None:
    s = report.summary
    columns = st.columns(5)
    columns[0].metric(
        "Lead time (85%)",
        _days(s.lead_time_percentiles[85]),
        help="85% of finished items took this long or less from creation to done.",
    )
    columns[1].metric(
        "Cycle time (85%)",
        _days(s.cycle_time_percentiles[85]),
        help="85% of finished items took this long or less from start to done.",
    )
    columns[2].metric(
        "Throughput / week",
        _number(s.throughput_per_week),
        help="Average items finished per complete week.",
    )
    columns[3].metric("WIP now", s.current_wip, help="Items started and not yet finished.")
    columns[4].metric(
        "Flow efficiency",
        "n/a" if math.isnan(s.flow_efficiency) else f"{s.flow_efficiency:.0%}",
        help="Share of the started time that items were actively worked on.",
    )


def show_tabs(report: FlowReport) -> None:
    s = report.summary
    tabs = st.tabs(["Cycle & lead time", "Throughput", "WIP & flow", "Aging WIP", "Items", "Help"])
    with tabs[0]:
        if s.items_done == 0:
            st.info("No finished items yet.")
        else:
            st.plotly_chart(charts.cycle_time_scatter(report.items, s.cycle_time_percentiles))
            st.plotly_chart(charts.lead_time_histogram(report.items, s.lead_time_percentiles))
    with tabs[1]:
        if report.throughput.empty:
            st.info("No finished items yet.")
        else:
            st.plotly_chart(charts.throughput_bars(report.throughput, s.throughput_per_week))
    with tabs[2]:
        st.plotly_chart(charts.wip_line(report.wip))
        st.plotly_chart(charts.cumulative_flow(report.cfd))
    with tabs[3]:
        if report.aging_wip.empty:
            st.info("Nothing in progress right now.")
        else:
            st.plotly_chart(charts.aging_wip_strip(report.aging_wip, s.cycle_time_percentiles))
            st.caption("Items above the p85 line are older than 85% of finished items.")
    with tabs[4]:
        st.dataframe(report.items, hide_index=True)
        st.download_button(
            "Download per-item metrics (CSV)",
            report.items.to_csv(index=False).encode("utf-8"),
            "flow_metrics_items.csv",
            "text/csv",
        )
    with tabs[5]:
        st.markdown(HELP_TEXT)


def _days(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{value:.1f} days"


def _number(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{value:.1f}"


HELP_TEXT = """
**Lead time**: creation → done. What the customer feels.

**Cycle time**: first move to *active* or *waiting* (the commitment point) → done.
What the team controls.

**Throughput**: items finished per calendar week (Monday to Sunday).
The current week is shown in grey and left out of the average.

**WIP**: items started and not finished, counted at the end of each day.

**Flow efficiency**: active time ÷ (active + waiting time) between start and done,
summed over finished items. Values around 15–40% are often cited as typical in knowledge work.

**Percentiles**: p85 = 85% of items took this long or less. Percentiles are used instead
of averages because flow data is skewed: a few slow items distort the mean.

Durations are calendar days, including weekends. See `docs/metrics.md` in the repository.
"""


main()

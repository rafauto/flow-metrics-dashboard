"""Plotly figures for the dashboard. Each function takes a metrics table and returns a figure."""

from __future__ import annotations

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from flow_metrics.metrics import CATEGORY_ORDER, PERCENTILES

CATEGORY_COLORS = {
    "backlog": "#CED4DA",
    "active": "#3B5BDB",
    "waiting": "#F59F00",
    "done": "#2F9E44",
}
PERCENTILE_DASH = {50: "dot", 85: "dash", 95: "longdash"}
LAYOUT = {"margin": {"l": 10, "r": 10, "t": 40, "b": 10}, "legend_title_text": ""}


def cycle_time_scatter(items: pd.DataFrame, percentiles: dict[int, float]) -> go.Figure:
    done = items.dropna(subset=["cycle_time_days"])
    fig = px.scatter(
        done,
        x="done_at",
        y="cycle_time_days",
        color="item_type",
        hover_data={"item_id": True, "cycle_time_days": ":.1f"},
        labels={"done_at": "Finished on", "cycle_time_days": "Cycle time (days)"},
        title="Cycle time per finished item",
    )
    _add_percentile_lines(fig, percentiles)
    return fig.update_layout(**LAYOUT)


def lead_time_histogram(items: pd.DataFrame, percentiles: dict[int, float]) -> go.Figure:
    done = items.dropna(subset=["lead_time_days"])
    fig = px.histogram(
        done,
        x="lead_time_days",
        nbins=20,
        labels={"lead_time_days": "Lead time (days)"},
        title="Lead time distribution",
    )
    fig.update_yaxes(title_text="Items")
    _add_percentile_lines(fig, percentiles, vertical=True)
    return fig.update_layout(**LAYOUT)


def throughput_bars(throughput: pd.DataFrame, average: float) -> go.Figure:
    data = throughput.assign(
        week=lambda d: d["is_partial_week"].map({True: "Current week (partial)", False: "Week"})
    )
    fig = px.bar(
        data,
        x="week_start",
        y="items_done",
        color="week",
        color_discrete_map={"Week": "#3B5BDB", "Current week (partial)": "#ADB5BD"},
        labels={"week_start": "Week starting", "items_done": "Items finished"},
        title="Throughput per week",
    )
    if not math.isnan(average):
        fig.add_hline(
            y=average, line_dash="dash", annotation_text=f"avg {average:.1f}", line_color="#495057"
        )
    return fig.update_layout(**LAYOUT)


def wip_line(wip: pd.DataFrame) -> go.Figure:
    fig = px.line(
        wip,
        x="date",
        y="wip",
        labels={"date": "Date", "wip": "Items in progress"},
        title="Work in progress per day",
    )
    fig.update_traces(line_shape="hv", line_color="#3B5BDB")
    return fig.update_layout(**LAYOUT)


def cumulative_flow(cfd: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for category in CATEGORY_ORDER:
        fig.add_trace(
            go.Scatter(
                x=cfd["date"],
                y=cfd[category],
                name=category.capitalize(),
                mode="lines",
                stackgroup="flow",
                line={"width": 0.5, "color": CATEGORY_COLORS[category]},
            )
        )
    fig.update_layout(
        title="Cumulative flow diagram", xaxis_title="Date", yaxis_title="Items", **LAYOUT
    )
    return fig


def aging_wip_strip(aging: pd.DataFrame, cycle_percentiles: dict[int, float]) -> go.Figure:
    fig = px.strip(
        aging,
        x="current_status",
        y="age_days",
        color="item_type",
        hover_data={"item_id": True, "age_days": ":.1f"},
        labels={"current_status": "Current status", "age_days": "Age since start (days)"},
        title="Aging work in progress",
    )
    _add_percentile_lines(fig, cycle_percentiles)
    return fig.update_layout(**LAYOUT)


def _add_percentile_lines(
    fig: go.Figure, values: dict[int, float], *, vertical: bool = False
) -> None:
    for level in PERCENTILES:
        value = values.get(level, float("nan"))
        if math.isnan(value):
            continue
        style = {
            "line_dash": PERCENTILE_DASH[level],
            "line_color": "#868E96",
            "annotation_text": f"p{level} {value:.1f}d",
        }
        if vertical:
            fig.add_vline(x=value, **style)
        else:
            fig.add_hline(y=value, **style)

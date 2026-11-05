"""Command line: generate sample data and print a flow summary for an export file."""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

from flow_metrics.config import load_settings
from flow_metrics.errors import DataValidationError
from flow_metrics.loading import load_transitions_file
from flow_metrics.metrics import FlowSummary, analyze
from flow_metrics.sample_data import SampleConfig, write_samples
from flow_metrics.workflow import load_workflow

logger = logging.getLogger("flow_metrics")


def format_summary(summary: FlowSummary, source_format: str) -> str:
    def days(value: float) -> str:
        return "n/a" if math.isnan(value) else f"{value:.1f} days"

    lead, cycle = summary.lead_time_percentiles, summary.cycle_time_percentiles
    efficiency = "n/a" if math.isnan(summary.flow_efficiency) else f"{summary.flow_efficiency:.0%}"
    throughput = (
        "n/a" if math.isnan(summary.throughput_per_week) else f"{summary.throughput_per_week:.1f}"
    )
    lines = [
        f"Format detected:    {source_format}",
        f"Data as of:         {summary.as_of:%Y-%m-%d %H:%M}",
        f"Items:              {summary.items_total} ({summary.items_done} done)",
        f"Lead time  p50/p85: {days(lead[50])} / {days(lead[85])}",
        f"Cycle time p50/p85: {days(cycle[50])} / {days(cycle[85])} (p95 {days(cycle[95])})",
        f"Throughput:         {throughput} items per week (complete weeks)",
        f"WIP now:            {summary.current_wip} items",
        f"Flow efficiency:    {efficiency}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    settings = load_settings()
    logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s: %(message)s")
    try:
        if args.command == "sample":
            paths = write_samples(args.output_dir, SampleConfig(seed=args.seed))
            for path in paths.values():
                print(f"Wrote {path}")
            return 0
        workflow = load_workflow(args.workflow or settings.workflow_file)
        transitions, source_format = load_transitions_file(args.file, settings)
        report = analyze(transitions, workflow)
        print(format_summary(report.summary, source_format))
        if args.export:
            report.items.to_csv(args.export, index=False)
            print(f"Per-item metrics written to {args.export}")
        return 0
    except (DataValidationError, FileNotFoundError) as exc:
        logger.error("%s", exc)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flow-metrics", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    sample = commands.add_parser("sample", help="write fictional sample exports")
    sample.add_argument("--output-dir", type=Path, default=Path("examples"))
    sample.add_argument("--seed", type=int, default=42)

    summary = commands.add_parser("summary", help="print flow metrics for an export CSV")
    summary.add_argument("file", type=Path)
    summary.add_argument("--workflow", type=Path, help="custom status-to-category YAML")
    summary.add_argument("--export", type=Path, help="write per-item metrics to this CSV")
    return parser


if __name__ == "__main__":
    sys.exit(main())

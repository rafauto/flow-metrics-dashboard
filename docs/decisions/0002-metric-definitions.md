# ADR 0002: Metric definitions

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

Flow metrics have several reasonable definitions, and tools rarely say which one they use. Small choices (calendar vs. business days, which status starts the clock) change the numbers. To be trustworthy, the dashboard must state its rules and apply them consistently.

## Decision

| Topic | Rule |
|---|---|
| Categories | Each status maps to backlog, active, waiting or done (`workflow.py`). |
| Commitment point | First move into *active* or *waiting*. |
| Finish point | Start of the trailing run of *done* statuses. A reopened item is not done. |
| Lead time | Finish − creation, in calendar days (fractional). |
| Cycle time | Finish − commitment point. Undefined if the item was never started. |
| Percentiles | `quantile(..., interpolation="higher")`: always an observed value. |
| Throughput | Items finished per Monday-to-Sunday week, empty weeks included. The average uses complete weeks only. |
| WIP | Items in *active* or *waiting* just before midnight each day. |
| Flow efficiency | Σ active time ÷ Σ (active + waiting time) over finished items, between start and finish. |
| "Now" (`as_of`) | The latest timestamp in the data, not the system clock. |

## Consequences

- Results are reproducible: the same file always gives the same numbers, which makes tests and screenshots stable.
- Calendar days overstate durations for teams that do not work weekends; a business-day option is on the roadmap.
- Weighting flow efficiency by time means long items count more, which reflects where time was actually spent but differs from the average of per-item ratios. Both are available: the per-item value is in the items table.
- Items that skip *active* entirely (straight from To Do to Done) are excluded from cycle time instead of being counted as zero.

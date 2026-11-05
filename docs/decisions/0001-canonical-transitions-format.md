# ADR 0001: One canonical transitions format with adapters per tool

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

Flow metrics need the history of status changes, not just the current status. Jira and Azure DevOps expose that history in different shapes: Jira as a changelog (one row per change, with *from* and *to*), Azure DevOps as revisions (a full snapshot of the work item each time any field changes). A plain CSV export from either tool only has the current status.

## Decision

All metrics are computed from one **canonical transitions table**:

`item_id, item_type, created_at, from_status, to_status, changed_at`

A row with an empty `from_status` records the status the item was created in. Each supported export has a small **adapter** that converts it to this table (`src/flow_metrics/adapters/`). The format is detected from the column names. Titles, descriptions and people are deliberately left out of the format.

## Consequences

- Supporting a new tool (Linear, Trello, GitHub Projects) means writing one adapter and its tests; the metrics do not change.
- A test checks that the Jira, Azure DevOps and canonical samples give identical results, which guards the adapters against drift.
- Users must export the status history, which takes an extra step in both tools. The README explains how.
- Leaving out titles and names limits what the UI can show, but keeps personal and confidential data out of the app.

## Alternatives considered

- **Call the Jira and Azure DevOps APIs directly.** Gives the history without manual exports, but needs credentials, secrets handling and rate-limit logic, and makes a public demo much harder. Kept on the roadmap.
- **Compute metrics from the current status and created/resolved dates only.** Works with the default export, but cannot produce cycle time, WIP history or flow efficiency, which are the point of the project.

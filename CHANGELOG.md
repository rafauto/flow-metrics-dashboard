# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-05

### Added

- Streamlit dashboard with demo mode and CSV upload.
- Adapters for Jira status history, Azure DevOps revisions and a canonical transitions format, with automatic detection.
- Status mapping (backlog, active, waiting, done) with defaults and sidebar overrides.
- Lead time, cycle time (p50/p85/p95), weekly throughput, daily WIP, cumulative flow, aging WIP and flow efficiency.
- Item type filter and per-item CSV download.
- `flow-metrics` CLI with `summary` and `sample` commands.
- Fictional sample data in three formats.
- Tests (unit, integration, Streamlit smoke test), GitHub Actions CI on Python 3.10 and 3.12, Dependabot.

[Unreleased]: https://github.com/rafauto/flow-metrics-dashboard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rafauto/flow-metrics-dashboard/releases/tag/v0.1.0

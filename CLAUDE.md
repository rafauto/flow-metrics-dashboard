# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

Streamlit dashboard that computes flow metrics (lead time, cycle time, throughput, WIP, flow efficiency) from Jira or Azure DevOps exports. Author: Rafaela Uto. Everything in the repository is in English.

## Commands

```bash
pip install -e ".[dev]"     # install with app and dev extras
streamlit run app.py        # run the app (demo data by default)
ruff check . && ruff format --check .
pytest                      # all tests, offline, ~5 s
flow-metrics sample         # regenerate examples/ (commit the result)
```

## Architecture

- `app.py`: UI only. No calculations here.
- `src/flow_metrics/adapters/`: one adapter per export format → canonical transitions (`item_id, item_type, created_at, from_status, to_status, changed_at`).
- `timeline.py` → intervals and per-item facts; `metrics.py` → all metrics; `charts.py` → Plotly figures.
- The package never imports Streamlit.

## Rules

- Metric definitions are in `docs/decisions/0002-metric-definitions.md`. Changing one requires updating the ADR, `docs/metrics.md` and a hand-calculated test in `tests/test_metrics.py`.
- New export formats: add an adapter, register it in `adapters/__init__.py`, add a test.
- Only fictional data. Never add employer, client or personal data, or company names.
- Ruff: line length 100, rules E, F, W, I, UP, B. Python 3.10 compatible (no `StrEnum`, no `datetime.UTC`).
- Conventional Commits in English. Keep `requirements.txt` in sync with `pyproject.toml`.
- Update the README architecture diagram and `docs/architecture.mmd` when the structure changes.

# ADR 0003: Streamlit and Plotly, deployed without installing the package

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

The project needs a shareable demo that opens with one click, runs on free hosting and is quick to build. The calculation logic must stay testable without the UI.

## Decision

- **UI:** Streamlit, hosted on Streamlit Community Cloud from the `main` branch.
- **Charts:** Plotly, for hover details and zoom on scatter plots and the CFD.
- **Layering:** all logic lives in the `flow_metrics` package (`src/`), which never imports Streamlit. `app.py` only reads inputs and displays results.
- **Deploy:** Streamlit Community Cloud installs `requirements.txt`. Instead of installing the package there, `app.py` adds `src/` to `sys.path`. Local development installs the package with `pip install -e ".[dev]"` from `pyproject.toml`.

## Consequences

- One click to a working demo, no servers to maintain and no secrets to manage.
- `requirements.txt` duplicates the minimum versions in `pyproject.toml`; a comment in both places reminds contributors to keep them in sync.
- The `sys.path` line in `app.py` is a small deviation from a pure package setup, accepted to avoid build steps on the hosting platform.
- Streamlit reruns the script on every interaction; parsing is cached with `st.cache_data` to keep the app responsive.

## Alternatives considered

- **Dash or a FastAPI + React front end:** more control, but much more code for the same result.
- **Static HTML report from the CLI:** no hosting needed, but no upload or interactive status mapping.

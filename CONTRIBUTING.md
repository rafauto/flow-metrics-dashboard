# Contributing

Thanks for your interest in improving Flow Metrics Dashboard.

## Guiding principles

- **Transparent definitions.** Every metric follows a written rule ([docs/metrics.md](docs/metrics.md), [ADR 0002](docs/decisions/0002-metric-definitions.md)). Changing a rule needs an ADR update and a test with hand-calculated values.
- **Logic outside the UI.** Calculations live in `src/flow_metrics/` and never import Streamlit. `app.py` only displays.
- **Simple first.** Prefer the smallest change that solves the problem; no layers "for the future".
- **Privacy by design.** The app needs no titles, descriptions or names, and stores nothing.
- **Fictional data only** in the repository.

## ⚠️ Privacy

Never paste real data, personal data, company names or API keys in issues, pull requests or test files. If you need to show a problem with an export, reproduce it with the sample files or with made-up rows.

## Reporting bugs and suggesting features

Open an issue using the templates. For bugs, include the steps, what you expected, what happened and a small fictional CSV that reproduces it.

## Development setup

```bash
git clone https://github.com/rafauto/flow-metrics-dashboard.git
cd flow-metrics-dashboard
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
streamlit run app.py
```

## Before opening a pull request

```bash
ruff check .
ruff format .
pytest
```

All three must pass; CI runs them on Python 3.10 and 3.12. Bug fixes need a regression test that fails without the fix. If you change the sample generator, regenerate the files with `flow-metrics sample` and commit them.

## Pull requests

1. Create a branch from `main` (`feat/date-filter`, `fix/azure-dates`).
2. Keep commits small, one logical change each.
3. Open a pull request, fill in the template and link the issue (`Closes #12`).
4. Pull requests are merged only with a green CI.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) in English:

`feat:` new feature · `fix:` bug fix · `docs:` documentation · `test:` tests · `ci:` CI · `chore:` maintenance · `style:` formatting · `refactor:` code change without behavior change

Example: `feat: add date range filter`

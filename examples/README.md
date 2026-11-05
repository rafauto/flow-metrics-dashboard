# Examples

All files here are **fictional**. They describe an invented team over 18 weeks and were generated with:

```bash
flow-metrics sample --output-dir examples --seed 42
```

| File | Format |
|---|---|
| `sample_jira_export.csv` | Jira status history (one row per status change) |
| `sample_azure_devops_export.csv` | Azure DevOps revisions (one row per revision, including edits that do not change the state) |
| `sample_transitions.csv` | Canonical transitions format |
| `workflow.yaml` | Example of a custom status mapping |

The three CSV files hold the same board and produce the same metrics.

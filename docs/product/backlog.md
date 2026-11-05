# Backlog

User stories with acceptance criteria, ready to become GitHub issues. Suggested labels: `story`, `mvp` or `roadmap`, and `feedback` for items that come from validation sessions.

## Done in v0.1.0

### 1. Explore with demo data `mvp`
As an agile specialist, I want to open the app and see metrics right away, so that I understand what it does before exporting anything.
- Given I open the app, when it loads, then demo data is selected and all five KPIs and charts are shown.
- Given demo data is shown, then a notice says the data is fictional.

### 2. Upload a Jira or Azure DevOps export `mvp`
As an agile specialist, I want to upload my tool's export, so that I see my own team's metrics.
- Given a Jira status history or Azure DevOps revisions CSV, when I upload it, then the format is detected and named on screen.
- Given a file with unknown columns, then I see which column sets are accepted.
- Given a file larger than the limit, not a CSV or with invalid dates, then I see a message that says how to fix it.

### 3. Map statuses to categories `mvp`
As an agile specialist, I want to say which statuses mean active, waiting or done, so that the metrics match how my team works.
- Given my statuses, when the file loads, then each one gets a default category and statuses unknown to the app are flagged.
- When I change a category, then every metric is recalculated.

### 4. See lead time and cycle time percentiles `mvp`
As an agile specialist, I want the 50th, 85th and 95th percentiles of lead and cycle time, so that I can answer "when will it be done?" with a confidence level.
- Given finished items, then the KPI shows the 85th percentile and the scatter plot shows p50, p85 and p95 lines.
- Given an item finished without being started, then it has a lead time but is left out of cycle time.

### 5. See throughput per week `mvp`
- Given finished items, then each week shows the number of items finished, including weeks with zero.
- The current incomplete week is marked and left out of the average.

### 6. See WIP, CFD and aging WIP `mvp`
- Given the data, then a daily WIP chart and a cumulative flow diagram are shown.
- Given items in progress, then each one is plotted by status and age, with the p85 cycle time as a reference line.
- Given a reopened item, then it counts as work in progress.

### 7. See flow efficiency `mvp`
- Given finished items, then flow efficiency = active time ÷ (active + waiting time), shown as a percentage.

### 8. Filter by item type and download results `mvp`
- When I deselect an item type, then every metric excludes it.
- When I click download, then I get a CSV with the computed values per item.

### 9. Get the summary from the command line `mvp`
- Given a CSV path, when I run `flow-metrics summary`, then the same metrics are printed; invalid files exit with code 1 and a clear message.

## Roadmap

### 10. Filter by date range `roadmap`
As an agile specialist, I want to limit the analysis to a period, so that I can compare before and after a process change.
- When I select a date range, then only items finished in that range count for lead time, cycle time and throughput.

### 11. Forecast with Monte Carlo `roadmap`
As a product owner, I want to know how many items we will likely finish by a date, so that I can set expectations without estimates.
- Given weekly throughput history, when I enter a date, then I see the number of items with 50%, 85% and 95% confidence.
- When I enter a number of items, then I see the likely finish dates with the same confidence levels.

### 12. Business days option `roadmap`
- When I enable business days, then weekends are excluded from every duration.

### 13. Day-first dates `roadmap`
- Given dates like 15/03/2026, when I select "day first", then they are parsed correctly.

# Product brief

## Problem

Agile coaches and scrum masters cannot answer "when will it be done?" with data, because the history needed to calculate flow metrics is locked inside Jira or Azure DevOps, hidden behind plugins or calculated with rules nobody can inspect.

## Target user

**Primary persona: the agile specialist.** Works with one to four teams of 5–10 people that use Jira or Azure DevOps. Runs retrospectives and service delivery reviews, and is asked by managers for delivery forecasts. Comfortable exporting a CSV; not a programmer. Wants numbers they can explain and defend.

**Secondary:** product owners and delivery managers who need a quick read on a team's flow before a planning meeting.

## Success criterion

From opening the app to reading the five metrics for their own export in **under 1 minute**, with no configuration beyond confirming the status mapping.

## MVP hypothesis

We believe that **a dashboard that reads a plain card export and applies documented definitions** solves **the lack of trustworthy flow metrics** for **agile specialists**; we will know when **a practitioner can answer "within how many days do we finish 85% of our items?" on their own, without help, in the first session**.

## MVP scope (v0.1.0)

In: upload or demo data, three export formats, status mapping, lead time, cycle time, throughput, WIP, flow efficiency, CFD, aging WIP, item type filter, per-item download, CLI.

Out (roadmap): Monte Carlo forecasts, date range filter, business days, API integrations, saved configurations, multi-team comparison, report export.

## Validation plan

Run a 30-minute session with at least one agile practitioner before expanding the scope:

1. Give them the demo link and the task: "find within how many days this team finishes 85% of its items". Observe without helping; time it.
2. Ask them to explain the CFD and the aging WIP chart in their own words.
3. Ask: which of these numbers would you take to your next retrospective? What is missing? What did you not trust?
4. If they can, have them try an anonymized export from a personal or sandbox project.

Record the findings as issues labelled `feedback` and reprioritize the backlog.

## Delivery cycles

| Cycle | Goal | Ends with |
|---|---|---|
| 1 | Core metrics from the sample data, tests and CI | v0.1.0 demo online |
| 2 | Validation session; fix what blocked the user | feedback issues closed |
| 3 | Top roadmap item from feedback (likely date filter or forecast), polish | v1.0.0 release |

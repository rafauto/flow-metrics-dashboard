# Flow metrics guide

This guide explains what each metric means, how this project calculates it and how to read the charts. The exact rules are also in [ADR 0002](decisions/0002-metric-definitions.md) and are checked by `tests/test_metrics.py`.

## The building blocks

Every card moves through statuses. Each status belongs to one **category**:

| Category | Meaning | Examples |
|---|---|---|
| backlog | not started yet | To Do, New, Backlog |
| active | someone is working on it | In Progress, In Review, Testing |
| waiting | started, but idle (queued or blocked) | Blocked, Ready for QA, Ready for Deploy |
| done | finished | Done, Closed, Resolved |

The first move into *active* or *waiting* is the **commitment point**: the moment the team started the work. The start of the final run of *done* statuses is the **finish point**. A card that leaves *done* (reopened) is work in progress again.

## Lead time

**Creation → finish.** What the requester experiences, including time in the backlog.

## Cycle time

**Commitment point → finish.** What the team controls. It is the basis for the simplest forecast: "85% of our items are finished within X days of starting."

Read the **cycle time scatter** from left to right: each dot is a finished item. The dashed lines are percentiles. Dots far above the p95 line are worth a conversation: what made them slow?

## Why percentiles and not averages

Flow data is skewed: most items are quick and a few take very long. One 40-day item moves the average a lot but barely moves the median. Percentiles also give a direct statement of confidence: p85 = "85% of items took this long or less".

This project reports observed values (no interpolation), so every percentile is the duration of a real item.

## Throughput

**Items finished per week** (Monday to Sunday). Weeks with zero items are shown, because they are information too. The current week is incomplete, so it is greyed out and left out of the average.

## WIP (work in progress)

**Items past the commitment point and not finished**, counted at the end of each day. High WIP usually means longer cycle times: work waits for attention.

**Little's Law** connects the three numbers for a stable system:

```
average cycle time ≈ average WIP ÷ average throughput
```

With the sample data: average WIP 6.6 items ÷ (7.4 items / 7 days) ≈ 6.2 days, in line with the observed mean cycle time of 6.2 days. When the two drift apart, the system is not stable (WIP is growing or items are aging).

## Aging WIP

**How long each in-progress item has been running.** Cycle time only covers items that already finished; aging WIP shows the ones at risk now. An item older than the p85 cycle time is already slower than 85% of past items: a good candidate for the next stand-up.

## Cumulative flow diagram (CFD)

A stacked area chart with the number of items in each category per day. Read it like this:

- The **vertical distance** of the *active* + *waiting* bands is the WIP.
- The **horizontal distance** between the top of a band and the *done* band roughly shows how long items take.
- Bands that **widen** mean work enters faster than it leaves.
- A *done* band that **flattens** means nothing is being finished.

## Flow efficiency

**Active time ÷ (active time + waiting time)** between start and finish, summed over finished items. It answers: of the time an item was "in progress", how much of it was someone actually working on it?

Values around 15–40% are often cited as typical for knowledge work; low numbers point to queues and hand-offs rather than slow people. The number depends heavily on how statuses are mapped: if a team has no waiting statuses, flow efficiency will look like 100%.

## Further reading

- Daniel S. Vacanti, *Actionable Agile Metrics for Predictability*
- The Kanban Guide (kanbanguides.org)

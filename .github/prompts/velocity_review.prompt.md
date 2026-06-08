---
mode: agent
agent: scrum-master-metrics
description: Review sprint velocity data and forecast next sprint capacity.
---

# Velocity Review

Analyze the sprint velocity data below and provide a trend assessment and forecast.

## Input

```
{{velocity_data}}
```

*(provide sprint-by-sprint story point data: committed vs. completed. Can be a table, bullet list, or screenshot description)*

---

## What to do

1. Calculate rolling average velocity (use last 3–5 sprints)
2. Identify the trend: stable, improving, or declining
3. Flag any anomalies (big drops, big spikes) and note possible causes
4. Forecast capacity for next sprint with a realistic range
5. Give one concrete recommendation based on the trend

## Output Format

---
**Velocity Review**
**Sprints Analyzed:** [N]

### Sprint Data

| Sprint | Committed | Completed | Delta |
|--------|-----------|-----------|-------|
| S-N    | ...       | ...       | ...   |

### Velocity Metrics
- **Rolling Average (last 3–5 sprints):** X story points
- **Trend:** Stable / Improving / Declining
- **Completion Rate:** X% average

### Anomalies
- [Sprint N was notably lower/higher — likely cause: ...]

### Forecast: Next Sprint
- **Recommended Commitment:** X ± Y story points
- **Confidence:** High / Medium / Low — [brief reason]

### Recommendation
[One specific action based on what the data shows — not generic advice]

---

> Note: forecast confidence drops significantly with fewer than 3 sprints of data.

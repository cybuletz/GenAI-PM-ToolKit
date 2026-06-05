---
mode: agent
agent: scrum-master-health-tracker
description: Evaluate team morale, workload balance, and sustainability signals from retrospective notes, feedback, or observations.
---

# Team Health Check

Evaluate team health based on the input below.

## Input

```
{{health_input}}
```

*(paste retro feedback, standup tone observations, team survey results, or describe what you're noticing. Can include screenshots of mood boards or anonymous feedback tools)*

---

## What to do

1. Identify signals across four areas: workload, morale, collaboration, clarity
2. Assign an overall health status: Healthy / Watch / At Risk
3. Note the most concerning signal and why
4. Suggest 1–2 practical things the SM or PM can do

## Output Format

---
**Team Health Assessment**
**Sprint / Period:** [if provided]

### Signal Summary

| Area | Status | Key Observations |
|------|--------|------------------|
| Workload | Healthy / Watch / At Risk | [what you observed] |
| Morale | Healthy / Watch / At Risk | [what you observed] |
| Collaboration | Healthy / Watch / At Risk | [what you observed] |
| Clarity | Healthy / Watch / At Risk | [what you observed] |

### Overall Health: **Healthy / Watch / At Risk**

### Most Concerning Signal
[Describe the signal and what it might mean if left unaddressed]

### Recommended Actions
1. [Specific action for SM/PM]
2. [Optional second action]

### What to Watch Next Sprint
[What to pay attention to that would confirm or disprove the current read]

---

> Health assessments are based on observable signals, not diagnoses. Treat conclusions as hypotheses to explore, not facts.

---
mode: agent
agent: stakeholder-communicator-reporter
description: Generate a structured sprint status report for stakeholders from sprint data, email updates, or screenshots.
---

# Sprint Status Report

Generate a stakeholder-ready status report from the input below.

## Input

```
{{sprint_data}}
```

*(paste sprint summary, completed items, velocity data, open blockers. Can be raw notes, an email, or a description of a screenshot)*

---

## What to do

1. Open with the overall status in one line
2. Summarize what was delivered in plain language (no jargon)
3. Connect delivery to business value where possible
4. Highlight the most important risk or open issue (if any)
5. State what's coming next

## Output Format

---
**Project Status Report**
**Period:** Sprint [N] / Week of [date]
**Status:** 🟢 On Track / 🟡 At Risk / 🔴 Needs Attention

### Delivered This Sprint
- [Feature or outcome]: [what this means for the user/business]
- [Feature or outcome]: ...

### In Progress
- [Item]: expected completion [timeframe]

### Open Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| ...  | ...    | ...        |

### Next Sprint Focus
[2–3 sentences on what's planned next and why it matters]

### Decisions Needed (if any)
- [Decision]: needed by [date]

---

> Keep the report under one page. Translate all technical items into user or business outcomes.

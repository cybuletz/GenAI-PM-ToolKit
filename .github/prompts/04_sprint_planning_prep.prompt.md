---
mode: agent
agent: scrum-master-facilitator
description: Generate a sprint planning checklist and agenda based on team context and upcoming sprint.
---

# Sprint Planning Preparation

Prepare for the upcoming sprint planning session.

## Input

```
{{planning_context}}
```

*(include: sprint number, team size, velocity, backlog items being considered, any known risks or capacity changes)*

---

## What to do

1. Generate a planning meeting agenda with realistic time allocations
2. Create a pre-planning checklist — things to confirm before the meeting
3. Flag any risks to the sprint goal based on the provided context
4. Suggest which backlog items to discuss first based on dependencies or risk

## Output Format

---
**Sprint Planning Prep: Sprint [N]**

### Pre-Planning Checklist
- [ ] Backlog groomed and estimated?
- [ ] Sprint goal draft ready?
- [ ] Team availability confirmed?
- [ ] Open impediments from last sprint addressed?
- [ ] Dependencies with other teams identified?
- [ ] Definition of Done reviewed recently?

### Suggested Agenda

| Time | Topic | Owner | Notes |
|------|-------|-------|-------|
| 0:00 | Sprint goal alignment | SM / PM | 5 min |
| 0:05 | Capacity confirmation | Team | 10 min |
| 0:15 | Backlog walkthrough | PO / PM | 30 min |
| 0:45 | Story breakdown & estimation | Team | 30 min |
| 1:15 | Dependency / risk check | SM | 10 min |
| 1:25 | Sprint commitment | Team | 5 min |

### Flagged Risks Going Into Planning
- [Risk based on input context]

### Recommended Story Priority
1. [Story/theme] — reason: [dependency / high value / risk]
2. [Story/theme] — reason: ...

---

> Adjust time slots based on actual team size and velocity. Larger teams may need more estimation time.

---
mode: agent
agent: scrum-master-metrics
description: Assess team capacity for an upcoming sprint considering leaves, part-time availability, and known constraints.
---

# Capacity Planning

Calculate available capacity for the upcoming sprint.

## Input

```
{{capacity_input}}
```

*(list team members, working days in sprint, any leaves, part-time days, or other constraints. Can be free text, a table, or a screenshot)*

---

## What to do

1. Calculate total available person-days
2. Apply a realistic capacity buffer (suggest 10–15% for meetings, interruptions, etc.)
3. Convert to an estimated story point range based on team velocity (if provided)
4. Flag any single points of failure (key person with reduced availability)
5. Suggest whether the sprint plan should be adjusted

## Output Format

---
**Capacity Plan: Sprint [N]**
**Sprint Dates:** [if provided]

### Team Availability

| Team Member | Role | Working Days | Leaves | Available Days | Notes |
|-------------|------|-------------|--------|----------------|-------|
| ...         | ...  | ...         | ...    | ...            | ...   |

### Capacity Summary
- **Total Available Person-Days:** X
- **After 15% Buffer:** X days
- **Estimated Usable Story Points:** X–Y (based on [velocity source])

### Flags
- [Name is the only person who can do X, and they're at 60% this sprint]

### Recommendation
[Should the team adjust their commitment target? By how much? Any stories to defer?]

---

---
mode: agent
agent: scrum-master-facilitator
description: Analyze daily standup updates from any format and surface blockers, team status, and velocity signals.
---

# Standup Analysis

Analyze the following standup update and produce a structured daily status report.

## Input

```
{{standup_input}}
```

*(paste standup notes, Slack messages, email, or describe a screenshot above)*

---

## What to do

1. Parse each person's update and extract: what's done, what's in progress, any blockers
2. Look for **implied** blockers too — things like "waiting for", "need sign-off", "can't start until"
3. Assess whether the sprint looks on track based on what's reported
4. Flag anything that needs action today

## Output Format

---
**Sprint Status:** [ON TRACK / AT RISK / BEHIND] — [one sentence why]

**Date:** [if known] | **Days Remaining:** [if known]

### Team Status

| Person | Done | In Progress | Blocker | Notes |
|--------|------|-------------|---------|-------|
| ...    | ...  | ...         | Yes/No  | ...   |

### Blockers

**Needs action today:**
- [Blocker description] — Owner: [Name] — Blocked since: [if known]

**Monitor:**
- [Blocker description] — Owner: [Name]

### Emerging Risks
- [Risk description and why it matters]

### Recommended Actions
1. [Action] — Owner: [Name] — By: [When]

---

> If any key information is missing (e.g., sprint days remaining, story points), note it and work with what's available.

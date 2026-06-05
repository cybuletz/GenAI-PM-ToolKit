---
mode: agent
agent: scrum-master-facilitator
description: Log, classify, and assign a blocker. Works from a free-text description, email, or screenshot.
---

# Impediment Log Entry

Create a structured impediment log entry from the description below.

## Input

```
{{impediment_description}}
```

*(paste the blocker description, email about the issue, or describe what you see in a screenshot)*

---

## What to do

1. Extract the core issue
2. Classify it: **Technical / Process / Resource / External / Dependency**
3. Assess impact on current sprint — high/medium/low
4. Suggest a resolution path
5. Determine if this needs escalation (blocked 2+ days, or affects multiple people)

## Output Format

---
**Impediment ID:** IMP-[date]-[sequence]
**Reported:** [today's date]
**Status:** Open

**Summary:** [one-line description]

**Type:** Technical / Process / Resource / External / Dependency

**Impact:** High / Medium / Low
**Affected Team Members:** [names or count]
**Sprint Impact:** [will this prevent sprint goal? yes/no/risk]

**Details:**
[2–3 sentences explaining the impediment clearly]

**Suggested Resolution:**
- [Step 1]
- [Step 2]

**Owner:** [suggest based on type — e.g., tech lead for technical, SM for process]
**Target Resolution:** [suggest a deadline]

**Escalate?** Yes / No — [reason if yes]

---

> If the description is vague, note what additional information would help resolve the impediment faster.

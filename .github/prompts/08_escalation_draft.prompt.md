---
mode: agent
agent: stakeholder-communicator-risk
description: Draft a professional escalation message for a blocker, risk, or unresolved dependency that needs senior attention.
---

# Escalation Draft

Draft a professional escalation based on the situation below.

## Input

```
{{escalation_context}}
```

*(describe what needs escalating, what you've already tried, who needs to act, and what the impact is if it stays unresolved)*

---

## What to do

1. State the situation clearly and factually
2. Say what you've already tried to resolve it
3. Explain the specific impact if it stays unresolved
4. Ask clearly for what you need (a decision, a resource, an action)
5. Include a timeline for when you need a response

## Output Format

---
**Escalation**
**Subject:** [Project Name] — [Issue Title] Requires Your Input
**To:** [Role or name of escalation target]
**Date:** [Date]

**Situation:**
[2–3 sentences: what the issue is and how long it's been unresolved]

**What We've Tried:**
[Brief list of steps already taken]

**Impact if Unresolved:**
[What happens to the project if this isn't addressed — timeline, team, deliverables]

**What We Need:**
[A specific ask — a decision, a resource, access, unblock from a third party]

**Needed By:** [Date]

Thank you for your support,
[PM Name]

---

> Keep the tone professional and factual. An escalation is a request for help, not an accusation.

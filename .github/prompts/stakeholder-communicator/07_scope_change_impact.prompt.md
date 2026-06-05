---
mode: agent
agent: stakeholder-communicator-risk
description: Assess and communicate the impact of a scope change request on timeline, effort, and tradeoffs.
---

# Scope Change Impact Assessment

Assess the impact of the scope change described below.

## Input

```
{{change_request}}
```

*(describe what's being requested, when it came in, what's currently planned, and any constraints)*

---

## What to do

1. Summarize what's being asked for
2. Estimate the impact on timeline and effort (use ranges if exact is impossible)
3. Identify what tradeoffs are involved (what gets pushed or cut if this is accepted)
4. Offer 2–3 options for the stakeholder to choose from
5. Give a clear recommendation but leave the decision to the stakeholder

## Output Format

---
**Scope Change Assessment**
**Requested Change:** [brief title]
**Received:** [date]
**Current Sprint/Phase:** [if relevant]

**What's Being Asked:**
[2–3 sentences summarizing the request in plain language]

**Impact Analysis:**
- Timeline: [+X days / no impact / unclear until scoped]
- Effort: [estimated additional days/points]
- Quality risk: [if any]
- Dependencies affected: [if any]

**Options:**

| Option | Timeline Impact | Tradeoff |
|--------|----------------|----------|
| Accept now, extend deadline | +X days | [what slips] |
| Accept now, drop lower priority item | 0 days | [what gets cut] |
| Defer to next release | 0 days | [customer impact] |

**Recommendation:**
[Your suggestion with brief reasoning — the decision stays with the stakeholder]

---

---
mode: agent
agent: stakeholder-communicator-risk
description: Draft a stakeholder-facing risk communication with impact, options, and any decisions needed.
---

# Risk Communication

Draft a clear risk communication for stakeholders based on the input below.

## Input

```
{{risk_description}}
```

*(describe the risk, what could go wrong, probability, what you've already done about it, and whether you need a decision from stakeholders)*

---

## What to do

1. Summarize the risk in plain, business-relevant terms
2. State the potential impact (timeline, scope, budget, or user experience)
3. Describe the mitigation already in place or being considered
4. If a stakeholder decision is needed, say so clearly — and by when
5. Keep the tone factual and calm

## Output Format

---
**Risk Notice**
**Project:** [Project Name]
**Date:** [Date]
**Risk Level:** High / Medium / Low

**Summary:**
[One sentence on what the risk is]

**Potential Impact:**
[What could happen if this risk materializes — in business terms]

**Probability:** High / Medium / Low — [brief reasoning]

**Current Mitigation:**
[What's already being done or planned]

**Options:**
1. [Option A]: [tradeoff]
2. [Option B]: [tradeoff]

**Decision Needed?** Yes / No
[If yes: what decision and by when]

---

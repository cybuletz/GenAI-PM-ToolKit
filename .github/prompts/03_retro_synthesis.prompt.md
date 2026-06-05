---
mode: agent
agent: scrum-master-facilitator
description: Synthesize retrospective notes or feedback into themes and actionable improvements.
---

# Retrospective Synthesis

Turn the following retrospective input into a structured summary with clear action items.

## Input

```
{{retro_input}}
```

*(paste team feedback, retro board export, email notes, or describe what's in a screenshot)*

---

## What to do

1. Group feedback into themes (not just "went well / improve" — find the real patterns)
2. For each theme: summarize what the team is actually saying
3. Identify root causes where visible
4. Distill into a max of **3 action items** — prioritized, not just listed
5. Note any recurring issues from previous sprints if mentioned

## Output Format

---
**Sprint Retro Summary**
**Sprint:** [if provided] | **Team:** [if provided]

### What Went Well
- [Theme]: [What the team said / what this tells us]

### What Needs Improvement
- [Theme]: [What the team said / underlying issue]

### Patterns / Recurring Issues
- [Issue]: [Why it keeps coming up if identifiable]

### Action Items (max 3, prioritized)

| # | Action | Owner | By When | Expected Outcome |
|---|--------|-------|---------|------------------|
| 1 | ...    | ...   | ...     | ...              |
| 2 | ...    | ...   | ...     | ...              |
| 3 | ...    | ...   | ...     | ...              |

### Note for Next Sprint
[One sentence to carry into next sprint planning or standup context]

---

> Limit to 3 action items even if there are more suggestions. Ask the PM/team to pick the top 3 if the list is long.

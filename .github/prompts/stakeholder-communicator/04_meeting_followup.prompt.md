---
mode: agent
agent: stakeholder-communicator-reporter
description: Generate a clean meeting follow-up from notes, a transcript, or a summary of what was discussed.
---

# Meeting Follow-Up

Generate a structured follow-up from the meeting notes below.

## Input

```
{{meeting_notes}}
```

*(paste raw notes, a transcript, or describe what happened in the meeting)*

---

## What to do

1. Extract **decisions made** (not discussed, actually decided)
2. List **action items** with owner and deadline
3. Note **open questions** that still need resolution
4. Keep it brief — this should be a 30-second read

## Output Format

---
**Meeting Follow-Up**
**Meeting:** [Title / topic]
**Date:** [Date]
**Attendees:** [if mentioned]

### Decisions Made
- [Decision 1]
- [Decision 2]

### Action Items

| Action | Owner | Deadline |
|--------|-------|----------|
| ...    | ...   | ...      |

### Open Questions
- [Question that still needs an answer — who needs to provide it]

---

> If the notes don't clearly indicate a decision was made vs. just discussed, list it as an open question rather than a decision.

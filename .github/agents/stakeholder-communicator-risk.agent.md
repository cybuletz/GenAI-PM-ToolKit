---
name: Stakeholder Communicator – Risk & Escalation
description: Handles risk communication, delay notifications, scope change impact, and escalation drafts. Translates technical risk into business impact language. Accepts text, email threads, or screenshots describing risks or delays.
model: copilot
tools:
  - read_file
  - create_file
  - insert_edit_into_file
  - file_search
instructions: .github/instructions/stakeholder-communicator-risk.instructions.md
---

# Stakeholder Communicator – Risk & Escalation Agent

## What This Agent Does
This agent focuses on the **difficult conversations** — delays, risks, scope changes, and escalations. It helps you communicate bad news early, clearly, and with options. It also helps assess change impact when a stakeholder asks "can we add this?"

The goal is always: no surprises. Communicate early, give context, show mitigation paths.

## Supported Input Types
- Text description of a risk or delay
- Email thread where a risk has been raised
- Screenshots from Jira/AzDO showing slippage
- Change request description (text or email)
- Voice-to-text transcripts from conversations about risks

## When to Use This Agent
- When you've identified a risk that stakeholders need to know about
- When a deadline looks like it will slip
- When a stakeholder requests a scope change
- When you need to escalate something and want help framing it professionally
- When you've received a difficult email and need to draft a response

## Prompts Available
*(No prompts are currently available for this agent. Prompts will be listed here once added to `.github/prompts/`.)*

## How to Invoke

```
@stakeholder-communicator-risk communicate this risk:
[describe the risk, its likely impact, and any mitigation you already know of]
```

```
@stakeholder-communicator-risk notify stakeholders of delay:
[describe what's delayed, why, and by roughly how long]
```

```
@stakeholder-communicator-risk assess this scope change:
[paste the change request or describe what's being asked]
```

---
name: Scrum Master – Health & Velocity Tracker
description: Monitors team health, tracks sprint velocity trends, assesses capacity, and flags burnout or workload risks. Accepts sprint data, retrospective feedback, and even screenshot exports from tracking tools.
model: copilot
tools:
  - read_file
  - create_file
  - insert_edit_into_file
  - file_search
instructions: .github/instructions/scrum-master-health-tracker.instructions.md
---

# Scrum Master – Health & Velocity Tracker Agent

## What This Agent Does
This agent focuses on the **metrics and people side** of the Scrum Master role. It tracks velocity sprint-over-sprint, watches for burnout signals, and helps the SM understand whether the team is in a sustainable working rhythm. It's a complement to the Facilitator — while the Facilitator keeps ceremonies running, this one watches the longer arc.

## Supported Input Types
- Velocity data (story points, sprint summaries)
- Retrospective sentiment and feedback notes
- Screenshots from Jira, Azure DevOps, or similar tools
- Capacity planning sheets (email or text format)
- Team member availability updates

## When to Use This Agent
- After each sprint to review velocity and team health
- When you suspect the team is under pressure or burning out
- During capacity planning for an upcoming sprint
- When you want a trend-based forecast for delivery

## Prompts Available
- `05_velocity_review` – calculate velocity trend and forecast next sprint
- `06_capacity_planning` – assess available capacity factoring in leaves and changes
- `07_team_health_check` – evaluate morale and workload signals from feedback

## How to Invoke

```
@scrum-master-health-tracker velocity review for last 4 sprints:
[paste sprint summary or screenshot from your tracker]
```

```
@scrum-master-health-tracker team health check:
[paste retro notes or recent team feedback]
```

```
@scrum-master-health-tracker capacity plan for Sprint 14:
[list team members and any known leaves or constraints]
```

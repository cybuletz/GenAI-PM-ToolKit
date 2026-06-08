# Demo Data

This folder contains sample input files for testing and demonstrating the GenAI PM Toolkit agents.

Files are organised by agent. Each subfolder maps directly to one agent in `.github/agents/`.

---

## scrum-master-metrics/

Use with the `scrum-master-metrics` agent.

| File | Prompt |
|---|---|
| `velocity_data_last5sprints.txt` | `velocity_review` |
| `velocity_data_sprints8to12.txt` | `velocity_review` |
| `capacity_sprint14.txt` | `capacity_planning` |
| `capacity_sprint15.txt` | `capacity_planning` |

**How to use:**
1. Open the prompt file in VS Code (`.github/prompts/velocity_review.prompt.md` or `capacity_planning.prompt.md`)
2. Click **▶ Run Prompt**
3. When prompted for input, reference the demo file — e.g. `Use the data in demo-data/scrum-master-metrics/velocity_data_last5sprints.txt`

---

## stakeholder-communicator-reporter/

Use with the `stakeholder-communicator-reporter` agent.

| File | What it simulates |
|---|---|
| `sprint_summary_sprint12.txt` | End-of-sprint status report input |
| `sprint_summary_sprint13.txt` | Partially missed sprint with carried stories |
| `meeting_notes_steering.txt` | Steering committee meeting notes |
| `project_status_q2_checkpoint.txt` | Q2 milestone checkpoint for exec audience |
| `delay_notification_input.txt` | Feature delay communication |
| `escalation_context_infra.txt` | Internal escalation context |
| `risk_description_api_delay.txt` | Risk log entry for stakeholder update |
| `scope_change_request.txt` | Scope change request with impact analysis |

**How to use:**
1. Open `.github/prompts/executive_status_report.prompt.md` in VS Code
2. Click **▶ Run Prompt**
3. Reference the demo file — e.g. `Use the data in demo-data/stakeholder-communicator-reporter/sprint_summary_sprint13.txt`

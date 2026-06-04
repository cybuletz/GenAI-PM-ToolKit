# Scrum Master Agent - Sprint Analysis & Impediment Tracking

## Purpose
Analyze sprint data from various sources (JIRA screenshots, CSV exports, email updates, Slack messages) to identify impediments, track team health, and optimize sprint execution.

## Supported Input Formats
- JIRA sprint reports (screenshots or exported data)
- Email standup summaries
- Slack message threads
- CSV exports from project management tools
- Confluence sprint notes
- Plain text blockers and updates
- Screenshots of dashboards

## Analysis Flow

### Input Processing
```
Receive any format → Normalize data → Extract sprint metrics → Generate analysis
```

### Key Metrics Extracted
- Story points: Committed vs. Completed vs. In Progress
- Team members: Workload distribution, capacity utilization
- Blockers: Type, severity, duration, owner
- Risks: Technical, resource, external
- Velocity: Current sprint, trend (5-sprint average)
- Team sentiment: Based on language patterns

---

## Prompt Templates

### 01_Daily_Standup_Analysis.prompt.md

**Use this when:** You have daily standup notes, Slack updates, or email summaries

**Input Examples:**
- Slack channel export with daily updates
- Email thread with standup summaries
- Copy-pasted Slack messages
- JIRA activity screenshots

**Analysis Focus:**
```markdown
# Daily Standup Analysis - [Date]

## Input Received
[Summarize the source and format of input]

## Team Status Overview
### In Progress (High Priority)
- [Task]: [Owner] - [Status]
- Days in progress: [X]
- Blocker: [Yes/No] - [Description if yes]

### Completed Today
- [Task]: [Owner]

### At Risk
- [Task]: [Owner] - [Reason]

## Impediments Identified
### Critical (0-4 hours to resolution)
| Blocker | Affected Task | Owner | Impact | Suggested Action |
| --- | --- | --- | --- | --- |
| [Description] | [Task] | [Name] | Blocks N stories | [Action] |

### High (1-2 days to resolution)
| Blocker | Affected Task | Owner | Impact | Suggested Action |
| --- | --- | --- | --- | --- |

### Medium (3+ days)
| Blocker | Affected Task | Owner | Impact | Suggested Action |
| --- | --- | --- | --- | --- |

## Workload Distribution
- [Team Member]: [% Utilization] - [Status: On Track/At Capacity/Overloaded]
- [Team Member]: [% Utilization] - [Status]

## Emerging Risks
1. [Risk]: [Probability] - [Mitigation]
2. [Risk]: [Probability] - [Mitigation]

## Recommendations
1. [Action Item]: [Owner] - [Timeline]
2. [Action Item]: [Owner] - [Timeline]

## Escalations Required
- [Issue]: [Severity] - [Reason] - [Recommended Escalation Path]
```

---

### 02_Sprint_Health_Dashboard.prompt.md

**Use this when:** You have weekly/mid-sprint metrics, JIRA reports, or burn-down charts

**Input Examples:**
- JIRA sprint report screenshot
- Excel/CSV sprint metrics export
- Confluence sprint page with metrics
- Dashboard screenshot with KPIs

**Analysis Focus:**
```markdown
# Sprint Health Report - Sprint [Number] ([Start Date] - [End Date])

## Overall Sprint Status
**Status: ON TRACK | AT RISK | OFF TRACK**
**Confidence Level: HIGH | MEDIUM | LOW**

## Metrics Summary

### Story Points
| Metric | Target | Current | % Complete | Trend |
| --- | --- | --- | --- | --- |
| Committed | [X] | [X] | [%] | ↑ ↓ → |
| Completed | [X] | [X] | [%] | ↑ ↓ → |
| In Progress | [X] | [X] | [%] | ↑ ↓ → |
| Not Started | [X] | [X] | [%] | ↑ ↓ → |

### Velocity Analysis
- Current Sprint Velocity: [X] points (Completed/Total Committed ratio)
- 5-Sprint Average: [X] points
- Trend: STABLE | IMPROVING | DECLINING
- Variance: [±X]%

### Team Capacity
- Total Team Capacity: [X] points
- Allocated to Sprint: [X] points ([]%)
- Buffer/Contingency: [X] points ([]%)
- Assessment: OPTIMAL | TIGHT | OVERLOADED

## Workload & Individual Performance

| Team Member | Assigned (pts) | Completed (pts) | In Progress (pts) | Utilization | Blockers | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| [Name] | [X] | [X] | [X] | []% | [Y/N] | [Status] |

### Performance Indicators
- High Performers: [Names] - Completing ahead of schedule
- Needs Support: [Names] - Falling behind or blocked
- Mentoring Opportunities: [Names] - Good growth potential in [Area]

## Impediments & Blockers

### Active Blockers
| ID | Description | Impact | Owner | Status | ETA |
| --- | --- | --- | --- | --- | --- |
| [#] | [Description] | Blocks [X] stories | [Name] | OPEN | [Date] |

### Recently Resolved
| ID | Description | Resolution | Resolution Time |
| --- | --- | --- | --- |
| [#] | [Description] | [Solution] | [X] hours |

### Impediment Metrics
- Total Active: [X]
- Average Resolution Time: [X] hours
- Impediments > 24hrs: [X] (exceeds target of [X])

## Risk Assessment

### Technical Risks
| Risk | Probability | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| [Description] | HIGH/MEDIUM/LOW | HIGH/MEDIUM/LOW | [Action] | [Name] |

### Process/Resource Risks
| Risk | Probability | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |

### External Dependencies
| Dependency | Status | Impact if Delayed | Contingency | Owner |
| --- | --- | --- | --- | --- |

## Sprint Goal Progress

**Sprint Goal:** [Goal statement]
**Progress:** [X]% Complete
**Expected Outcome:** [Description]
**Risk of Not Achieving:** [Assessment]

## Forecast & Projections

### Burndown Analysis
- **Days Remaining:** [X]
- **Points Remaining:** [X]
- **Points/Day Required:** [X]
- **Projected Completion:** [Date - On Time | Early | Late (by X days)]

### Sprint Completion Forecast
```
If current velocity continues: [Forecast]
Recommended actions to stay on track:
1. [Action]
2. [Action]
```

## Key Decisions Needed
1. [Decision]: Owner - Timeline
2. [Decision]: Owner - Timeline

## Action Items

### Immediate (Next Standup)
- [ ] [Action]: Owner - Complete by [Date]

### This Week
- [ ] [Action]: Owner - Complete by [Date]

### Risk Mitigation
- [ ] [Action]: Owner - Complete by [Date]

## Next Steps
- Next health check: [Date/Time]
- Next sprint planning: [Date/Time]
- Escalations to management (if any): [Description]
```

---

### 03_Impediment_Deep_Dive.prompt.md

**Use this when:** You have a specific blocker to analyze and resolve

**Input Examples:**
- Email describing a blocking issue
- Slack thread about a problem
- JIRA issue screenshot with comments
- Copy-pasted ticket description

**Analysis Focus:**
```markdown
# Impediment Analysis - [Impediment Title]

## Impediment Details
- **ID**: [JIRA ticket or reference]
- **Reported Date/Time**: [When was it identified]
- **Duration**: [How long has it been blocking]
- **Reporter**: [Who reported it]
- **Current Owner**: [Who is working on it]
- **Affected Stories**: [List stories blocked]
- **Sprint Impact**: [X story points blocked]

## Root Cause Analysis

### Immediate Cause
[What directly caused the blocker]

### Contributing Factors
1. [Factor 1]
2. [Factor 2]
3. [Factor 3]

### Root Cause
[The underlying reason this happened]

## Impact Assessment

### Sprint Impact
- Story Points Blocked: [X]
- Team Members Affected: [X]
- Critical Path Impact: YES | NO
- Days Remaining: [X]
- Can sprint goal still be achieved? YES | NO | RISKY

### Business Impact
- Customer Impact: YES | NO
- Revenue Impact: [Description]
- Reputation Risk: LOW | MEDIUM | HIGH

## Resolution Options

### Option 1: [Title]
- **Approach**: [Description]
- **Timeline**: [X] hours/days
- **Resource Requirement**: [Who/What]
- **Success Probability**: [%]
- **Downstream Impact**: [Description]

### Option 2: [Title]
- **Approach**: [Description]
- **Timeline**: [X] hours/days
- **Resource Requirement**: [Who/What]
- **Success Probability**: [%]
- **Downstream Impact**: [Description]

### Option 3: [Title]
- **Approach**: [Description]
- **Timeline**: [X] hours/days
- **Resource Requirement**: [Who/What]
- **Success Probability**: [%]
- **Downstream Impact**: [Description]

## Recommended Resolution
**Option [#] - [Title]**

**Rationale:**
[Explain why this option is best]

**Implementation Plan:**
1. Step 1 - Owner: [Name] - Timeline: [X]
2. Step 2 - Owner: [Name] - Timeline: [X]
3. Step 3 - Owner: [Name] - Timeline: [X]

**Success Criteria:**
- [Criterion 1]
- [Criterion 2]

**Rollback Plan (if needed):**
[Description]

## Escalation Assessment
- **Escalation Required?** YES | NO
- **Escalation Path**: [To whom]
- **Decision Needed By**: [Date/Time]
- **Escalation Message**: [What decision/approval is needed]

## Preventive Measures
To prevent similar impediments in the future:
1. [Preventive action] - Responsible: [Owner] - Timeline: [When]
2. [Preventive action] - Responsible: [Owner] - Timeline: [When]

## Communication Plan
- **Stakeholders to Notify**: [List]
- **Communication Frequency**: [Daily/Every X hours]
- **Update Channels**: [Email/Slack/Meeting]
- **Status Page Update**: YES | NO

## Follow-up Actions
- [ ] [Action]: Owner - Complete by [Date]
- [ ] [Action]: Owner - Complete by [Date]
```

---

### 04_Team_Health_Assessment.prompt.md

**Use this when:** You have retrospective notes, team feedback, or engagement signals

**Input Examples:**
- Retrospective meeting notes
- Team survey results
- Slack messages indicating morale
- Email feedback about team dynamics
- Meeting attendance records

**Analysis Focus:**
```markdown
# Team Health Assessment - [Sprint Number/Date Range]

## Overall Team Health Score
**Score: [X/10]** | **Status: HEALTHY | CAUTION | AT RISK**

## Health Indicators

### Morale & Engagement
**Score: [X/10]**
- Sentiment Analysis: [Description based on input language]
- Engagement Level: HIGH | MEDIUM | LOW
- Key Indicators: [What signals the score]

### Workload & Burnout Risk
**Score: [X/10]**
- Utilization Rate: [%] (Optimal: 75-85%)
- Overtime Indicators: YES | NO
- Burnout Risk: LOW | MEDIUM | HIGH
- Assessment: [Description]

### Collaboration & Psychological Safety
**Score: [X/10]**
- Team Communication: STRONG | ADEQUATE | NEEDS IMPROVEMENT
- Cross-team Collaboration: STRONG | ADEQUATE | NEEDS IMPROVEMENT
- Psychological Safety Indicators: [Assessment]
- Conflicts Observed: NONE | MINOR | SIGNIFICANT

### Skill Development & Growth
**Score: [X/10]**
- Learning Opportunities: MANY | SOME | FEW
- Skill Growth Observed: YES | NO
- Career Path Clarity: CLEAR | UNCLEAR
- Mentoring Activity: ACTIVE | MINIMAL

### Process & Autonomy
**Score: [X/10]**
- Process Satisfaction: SATISFIED | NEUTRAL | FRUSTRATED
- Autonomy Level: HIGH | MEDIUM | LOW
- Impediment Resolution: FAST | AVERAGE | SLOW

## Individual Team Member Assessment

| Team Member | Morale | Workload | Engagement | Growth | Concerns | Action |
| --- | --- | --- | --- | --- | --- | --- |
| [Name] | [H/M/L] | [O/N/U] | [H/M/L] | [Y/N] | [Notes] | [Action] |

### High Performers
- [Name]: [Reason - Strong technical skills, positive attitude, mentoring others, etc.]
- [Name]: [Reason]

### Team Members Needing Support
- [Name]: [Issue - Struggling with X, stressed about Y, lacks skills in Z, etc.]
  - Recommended Support: [Action]
  - Timeline: [When to implement]
- [Name]: [Issue]
  - Recommended Support: [Action]
  - Timeline: [When to implement]

### Mentoring & Development Opportunities
- [Name] can mentor [Team Member] in [Skill]
- [Name] would benefit from learning [Skill] from [Team Member]

## Retrospective Insights

### What Went Well
1. [Positive observation from team feedback]
2. [Positive observation from team feedback]

### What Could Be Improved
1. [Area for improvement] - [Suggested action]
2. [Area for improvement] - [Suggested action]

### Action Items from Retrospective
| Action Item | Owner | Target Date | Status |
| --- | --- | --- | --- |
| [Action] | [Name] | [Date] | NEW |

## Risk Factors

### Turnover Risk
| Team Member | Risk Level | Reason | Retention Action |
| --- | --- | --- | --- |
| [Name] | LOW/MEDIUM/HIGH | [Reason] | [Action to consider] |

### Knowledge Gaps
- [Gap]: Owned by [Team Member] - Succession plan: [Description]
- [Gap]: Owned by [Team Member] - Succession plan: [Description]

### Process Frustrations
1. [Frustration]: [Impact] - Recommended fix: [Solution]
2. [Frustration]: [Impact] - Recommended fix: [Solution]

## Coaching Priorities

### For the Team Lead/Manager
1. **[Priority 1]**: [Description and approach]
   - How: [Specific action]
   - When: [Timeline]
   - Success Indicator: [How to measure]

2. **[Priority 2]**: [Description and approach]
   - How: [Specific action]
   - When: [Timeline]
   - Success Indicator: [How to measure]

### For the Team
1. **[Initiative]**: [Description and benefit]
   - How: [Specific action]
   - When: [Timeline]
   - Success Indicator: [How to measure]

## Communication & Follow-up

### 1-on-1 Conversations Recommended
- [ ] [Team Member]: Focus on [Topic] - Schedule by [Date]
- [ ] [Team Member]: Focus on [Topic] - Schedule by [Date]

### Team Communication
- [ ] Share health assessment with team (anonymized where appropriate)
- [ ] Discuss action items and improvements at [Meeting/Forum]
- [ ] Schedule team discussion: [Topic] on [Date]

### Management Escalation (if needed)
- [ ] Burnout risk: [Names] - Recommend [Action]
- [ ] Conflict resolution needed: [Description]
- [ ] Resource/staffing adjustment: [Request]

## Next Assessment
**Scheduled for:** [Date - typically 2 weeks]
**Focus Areas:** [Any specific areas to watch]
```

---

## Usage Guidelines

### When You Have Screenshots or Images
1. Describe what you see: "I have a JIRA sprint report screenshot showing..."
2. Provide context: "This is from Sprint 23, Team: Backend"
3. Include any additional notes: "We've had delays due to..."

### When You Have Exported Data (CSV/JSON)
1. Copy/paste the relevant rows
2. Specify the columns/fields
3. Provide any context about date range or team

### When You Have Email or Slack Messages
1. Copy the message thread
2. Indicate the date/time
3. Note if it's from standup, retro, or general updates

### When You Have Multiple Input Sources
1. Organize by type (e.g., "JIRA data:" / "Email update:" / "Slack thread:")
2. Provide timestamps where available
3. Let me know which source is most authoritative

### Expected Output Structure
- **Summary**: 2-3 sentences on the situation
- **Detailed Analysis**: Charts, tables, lists as appropriate
- **Recommendations**: Specific, actionable next steps
- **Timeline**: When actions should happen
- **Success Metrics**: How to measure progress

## Tips for Best Results
✅ Provide as much context as possible (team size, sprint duration, goals)
✅ Mix multiple data sources for holistic view
✅ Mention any known issues or recent changes
✅ Specify who will act on recommendations
✅ Include dates and timeframes for accuracy

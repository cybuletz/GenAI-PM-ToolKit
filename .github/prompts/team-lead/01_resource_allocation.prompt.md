# Team Lead Agent - Resource & Technical Planning

## Purpose
Analyze team capacity, technical estimates, skill gaps, and architectural decisions from various sources to optimize resource allocation and technical execution.

## Supported Input Formats
- JIRA sprint planning data or screenshots
- Team capacity spreadsheets
- Technical architecture documents
- Email with staffing questions
- Code review feedback summaries
- Incident reports
- Performance metrics and dashboards
- Survey results on team morale

## Analysis Flow

### Input Processing
```
Receive any format → Extract team/technical data → Analyze capacity and capabilities → Generate optimization plan
```

### Key Data Extracted
- Team member skills and availability
- Technical complexity and risk factors
- Estimation accuracy and trends
- Workload balance and utilization
- Code quality metrics
- Incident patterns and prevention opportunities
- Skill gaps and development needs

---

## Prompt Template: 01_Resource_Allocation

**Use this when:** You need to allocate team members to work

**Input Examples:**
- List of stories/tasks with estimates
- Team members available
- Previous sprint performance data
- Email with capacity constraints
- Skill requirements and team skills matrix

**Key Analysis:**
- Workload distribution and balance
- Skill-to-task matching
- Capacity utilization optimization
- Context-switching impact
- Development opportunity identification
- Bottleneck identification

---

## Prompt Template: 02_Technical_Estimation

**Use this when:** You have technical work to estimate

**Input Examples:**
- Feature/task description
- Technical architecture document
- Similar past work references
- Code review findings
- Email with technical questions

**Key Analysis:**
- Complexity scoring
- Risk identification
- Effort estimation with confidence level
- Dependency mapping
- Technical debt implications
- Feasibility assessment

---

## Prompt Template: 03_Code_Quality_Assessment

**Use this when:** You have code review feedback or quality metrics

**Input Examples:**
- Code review comments
- Test coverage reports
- Static analysis results
- Performance metrics
- Incident post-mortems

**Key Analysis:**
- Quality trend analysis
- Defect pattern identification
- Standards compliance check
- Training needs assessment
- Improvement recommendations

---

## Prompt Template: 04_Incident_Analysis

**Use this when:** You have an incident or production issue to analyze

**Input Examples:**
- Incident report email
- Slack thread about outage
- Post-mortem notes
- Error logs or screenshots
- Timeline of events

**Key Analysis:**
- Root cause analysis
- Impact assessment
- Prevention recommendations
- Response process improvement
- Knowledge sharing needs

# Product Manager Agent - Backlog & Roadmap Analysis

## Purpose
Analyze customer feedback, backlog items, competitive landscape, and market data from various sources to drive prioritization and roadmap decisions.

## Supported Input Formats
- JIRA backlog exports or screenshots
- Customer support tickets (Zendesk, Intercom, email)
- Feature request emails or Slack messages
- Survey results and customer feedback
- Competitive analysis documents
- Sales pipeline and customer data
- Usage analytics dashboards
- Market research reports
- Copy-pasted customer comments

## Analysis Flow

### Input Processing
```
Receive any format → Extract insights → Categorize feedback → Calculate priorities → Generate roadmap impact
```

### Key Data Extracted
- Customer pain points and feature requests
- Value proposition alignment
- Market opportunity size
- Competitive positioning
- Adoption potential and ROI
- Customer sentiment and urgency
- Business impact and revenue potential

---

## Prompt Templates

### 01_Backlog_Prioritization.prompt.md

**Use this when:** You have a list of features/stories to prioritize

**Input Examples:**
- JIRA backlog export (CSV or screenshot)
- Email with feature requests list
- Slack thread with customer requests
- Copy-pasted spreadsheet with feature ideas
- Mixed format: some from sales, some from support, some from team ideas

**Analysis Focus:**
```markdown
# Backlog Prioritization Analysis

## Input Summary
**Total Items Analyzed**: [X] features/stories
**Data Sources**: [List sources used]
**Analysis Date**: [Date]
**Time Horizon**: [Sprint | Quarter | Half-Year]

## Prioritization Framework

### Value-to-Effort Matrix

```
High Value |  ■ Quick Wins    | ■ Major Projects
           |  (Do First)      | (Plan Carefully)
           |                  |
Low Effort |                  | High Effort
           |  ■ Low Value     | ■ Research Needed
Low Value  |  (Nice to Have)  | (Avoid)
```

## Prioritized Backlog (Ranked 1-N)

### Tier 1: Immediate Priority (Next Sprint/2 Weeks)

| Rank | Feature/Story | Value Score | Effort (pts) | Value:Effort | Strategic Alignment | Customer Demand | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [Title] | 9/10 | 5 | 1.8 | HIGH | URGENT | ✅ DO FIRST |
| 2 | [Title] | 8/10 | 8 | 1.0 | HIGH | HIGH | ✅ DO FIRST |

**Rationale for Tier 1:**
- [Feature 1]: [Why this is critical - customer impact, revenue, strategic]
- [Feature 2]: [Why this is critical - customer impact, revenue, strategic]

### Tier 2: High Priority (Current Sprint/Month)

| Rank | Feature/Story | Value Score | Effort (pts) | Value:Effort | Strategic Alignment | Customer Demand | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | [Title] | 7/10 | 13 | 0.5 | HIGH | MEDIUM | ✅ PLAN FOR SPRINT |
| 4 | [Title] | 7/10 | 5 | 1.4 | MEDIUM | HIGH | ✅ PLAN FOR SPRINT |

**Rationale for Tier 2:**
- [Feature 1]: [Why this matters - strategic importance, customer asks]
- [Feature 2]: [Why this matters - strategic importance, customer asks]

### Tier 3: Medium Priority (Next Quarter)

| Rank | Feature/Story | Value Score | Effort (pts) | Value:Effort | Strategic Alignment | Customer Demand | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | [Title] | 6/10 | 21 | 0.3 | MEDIUM | MEDIUM | 📋 BACKLOG |
| 6 | [Title] | 6/10 | 8 | 0.75 | MEDIUM | LOW | 📋 BACKLOG |

**Rationale for Tier 3:**
- [Feature 1]: [Why this is useful but not urgent]
- [Feature 2]: [Why this is useful but not urgent]

### Tier 4: Low Priority (Future/Revisit)

| Rank | Feature/Story | Value Score | Effort (pts) | Value:Effort | Strategic Alignment | Customer Demand | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7+ | [Title] | 3-5/10 | 13+ | <0.3 | LOW | LOW | ⏸️ DEFER |

**Rationale for Tier 4:**
- [Feature]: [Why this can be deferred - low demand, high effort, low strategic value]

## Scoring Methodology

### Value Scoring (1-10)
- **9-10**: Critical for business strategy, high customer demand, major revenue impact
- **7-8**: Important for customer satisfaction, medium revenue/strategic impact
- **5-6**: Nice to have, some customer demand, minimal strategic impact
- **1-4**: Low priority, low demand, low strategic value

### Value Drivers Considered
- **Customer Impact**: How many customers want this? How much does it matter to them?
- **Revenue Impact**: Direct revenue generation or upsell potential?
- **Strategic Alignment**: Does this advance our roadmap/OKRs?
- **Market Positioning**: Does this help vs. competitors or open new markets?
- **Retention Risk**: Is this needed to retain customers?

### Effort Estimation
- Compare to similar past features
- Account for dependencies and integrations
- Flag technical unknowns
- Story point estimate [X] points ±Y

## Strategic Alignment Analysis

### Aligned with Q[Quarter] OKRs
```
OKR: [Key Result]
  → Supporting Features: [Features that directly support this OKR]
  
OKR: [Key Result]
  → Supporting Features: [Features that directly support this OKR]
```

### Not Yet Aligned
```
[Feature]: Consider aligning with OKR: [Suggested OKR]
```

## Customer Feedback Summary

### Top Customer Requests (Frequency)
1. [Feature]: Requested by [X] customers
   - Urgency: URGENT | HIGH | MEDIUM | LOW
   - Retention Impact: CRITICAL | HIGH | MEDIUM
   - Customers Requesting: [Names/Companies]

2. [Feature]: Requested by [X] customers
   - Urgency: URGENT | HIGH | MEDIUM | LOW
   - Retention Impact: CRITICAL | HIGH | MEDIUM
   - Customers Requesting: [Names/Companies]

### Customer Pain Points Addressed
- [Tier 1 Feature]: Solves pain point [X] for [Y customers/company type]
- [Tier 2 Feature]: Solves pain point [X] for [Y customers/company type]

### Features with Low/No Customer Demand
- [Feature]: [Number] customer requests vs. [effort] - Recommend: DEFER
- [Feature]: [Number] customer requests vs. [effort] - Recommend: DEFER

## ROI & Impact Analysis

| Feature | Est. Effort (hrs) | Time to Market (weeks) | Adoption Forecast | Revenue Potential | ROI Ranking |
| --- | --- | --- | --- | --- | --- |
| [Tier 1 Feature] | 40 | 2 | 70% of user base | $X | 1 |
| [Tier 1 Feature] | 60 | 3 | 50% of user base | $Y | 2 |

### Revenue Impact Estimates (Next 12 Months)
- **Tier 1 Features**: $X in incremental revenue
- **Tier 2 Features**: $Y in incremental revenue
- **Tier 3 Features**: $Z in incremental revenue
- **Total Addressable Opportunity**: $[Total]

### Risk of Not Addressing
- **Churn Risk**: If we don't prioritize [Feature], we risk losing [X] customers
- **Competitive Risk**: Competitors have [Feature], we're falling behind in [Area]
- **Market Risk**: Market window closing on [Opportunity] - need to move fast

## Dependencies & Prerequisites

### External Dependencies
| Feature | Dependency | Status | Impact | Workaround |
| --- | --- | --- | --- | --- |
| [Feature] | [External system/API] | Available Q[X] | Can proceed without | [Approach] |
| [Feature] | [Third-party service] | BLOCKED | Blocks implementation | Waiting for [Partner] |

### Internal Dependencies
| Feature | Dependency | Current Owner | Priority | Timeline |
| --- | --- | --- | --- | --- |
| [Tier 1 Feature] | [Infrastructure work] | [Team] | MUST HAVE | Complete by [Date] |
| [Tier 2 Feature] | [API development] | [Team] | NICE TO HAVE | Complete by [Date] |

## Recommendations

### Immediate Actions (This Sprint)
1. **Start Development**: [Tier 1 Feature #1] and [Tier 1 Feature #2]
   - Owner: [PM/Team Lead]
   - Expected Delivery: [Date]
   - Success Metric: [Deployment + X% adoption in 2 weeks]

2. **Plan for Next Sprint**: [Tier 2 Features] - requires dependency X
   - Owner: [PM/Team Lead]
   - Timing: Start after [Dependency] is resolved
   - Estimated Duration: [Y weeks]

### Strategic Decisions Needed
1. **[Question]**: Should we build [Feature X] even though effort is high?
   - Decision Needed By: [Date]
   - Recommended Approach: [Recommendation]
   - Decision Owner: [Name]

2. **[Question]**: Do we break down [Complex Feature] into phases?
   - Decision Needed By: [Date]
   - Option A: Build full feature ([X weeks])
   - Option B: MVP first, then iterate ([X+Y weeks] total)
   - Recommended: [Your recommendation]

## Communication Plan

### Customer Communications
- [ ] Announce priorities in customer newsletter
- [ ] Post feature roadmap update to customer portal
- [ ] Schedule customer calls for top requesting [Feature]

### Sales Enablement
- [ ] Update sales deck with new priorities
- [ ] Brief sales team on when top-requested features ship
- [ ] Prepare response for ["When will you have X?"]

### Team Kickoff
- [ ] Present prioritization to engineering team
- [ ] Discuss trade-offs and sequencing
- [ ] Confirm capacity and timeline alignment

## Next Review
**Scheduled for**: [Date - typically 2 weeks or after sprint]
**Trigger Re-prioritization if**: [Condition - major customer churn, market shift, etc.]
```

---

### 02_Customer_Feedback_Synthesis.prompt.md

**Use this when:** You have customer feedback from multiple sources to analyze

**Input Examples:**
- Support ticket exports (text format)
- Email thread with customer complaints/suggestions
- Survey results (raw data)
- Slack messages from sales team
- Feature request compilation from customers
- NPS feedback comments
- Customer meeting notes

**Analysis Focus:**
```markdown
# Customer Feedback Analysis Report

## Feedback Collection Summary
**Period**: [Date Range]
**Total Feedback Items**: [X]
**Sources**: [List sources - email, support, survey, Slack, meetings, etc.]
**Coverage**: [X] unique customers / [X]% of customer base

## Feedback Categorization

### By Theme/Feature Area

#### [Feature Area 1]: [X] mentions

**Volume**: [X] customers requesting this
**Sentiment**: POSITIVE | MIXED | NEGATIVE
**Urgency**: CRITICAL | HIGH | MEDIUM | LOW

**Sample Feedback**:
- "[Quote from customer feedback]" - Customer Type: [Enterprise | SMB | Startup]
- "[Quote from customer feedback]" - Customer Type: [Enterprise | SMB | Startup]

**Analysis**:
- [Key insight about this request]
- [Connection to business impact]
- [Recommended action]

**Recommendation**: 
- Priority Rank: [1-10]
- Suggested Timeline: [When to address]
- Estimated Impact: [X companies | $Y revenue | Z% churn reduction]

---

#### [Feature Area 2]: [X] mentions

**Volume**: [X] customers requesting this
**Sentiment**: POSITIVE | MIXED | NEGATIVE
**Urgency**: CRITICAL | HIGH | MEDIUM | LOW

**Sample Feedback**:
- "[Quote]" - Customer Type: [Type]
- "[Quote]" - Customer Type: [Type]

**Analysis**:
- [Key insight]
- [Business implication]
- [Recommended action]

**Recommendation**:
- Priority Rank: [1-10]
- Suggested Timeline: [When]
- Estimated Impact: [X companies | $Y | Z%]

---

### By Sentiment

#### Positive Feedback (Promoters)

**Count**: [X] mentions
**Key Themes**:
- [What customers love about product]
- [What's working well]

**Quotes**:
- "[Quote showing satisfaction]" - [Customer]
- "[Quote showing loyalty]" - [Customer]

**Action**: 
- Double down on [Feature/Area] that customers love
- Consider [Feature X] as upsell/expansion opportunity

#### Mixed Feedback (Passives)

**Count**: [X] mentions
**Key Themes**:
- [What's okay but could be better]
- [Nice-to-haves]

**Quotes**:
- "[Quote showing hesitation]" - [Customer]
- "[Quote showing conditional interest]" - [Customer]

**Action**:
- Address [Specific issue] to convert to promoters
- Monitor [Metric] for satisfaction trend

#### Negative Feedback (Detractors)

**Count**: [X] mentions
**Key Themes**:
- [Critical pain points]
- [Churn risks]
- [Major frustrations]

**Quotes**:
- "[Quote showing frustration]" - [Customer] - Status: [Active | At Risk | Churned]
- "[Quote showing complaint]" - [Customer] - Status: [Active | At Risk | Churned]

**Action**:
- URGENT: Address [Issue] to prevent churn from [X, Y, Z customers]
- Plan immediate outreach to [Customers] to understand severity
- Propose [Solution] by [Date]

---

### By Customer Segment

#### Enterprise Customers
**Feedback Count**: [X]
**Key Requests**: [Top 3 feature requests]
**Churn Risk**: [Assessment]
**Revenue at Risk**: $[X]

**Priority Issues**:
1. [Issue]: Impacts [X] enterprise customers
2. [Issue]: Impacts [X] enterprise customers

#### SMB Customers
**Feedback Count**: [X]
**Key Requests**: [Top 3 feature requests]
**Churn Risk**: [Assessment]
**Revenue at Risk**: $[X]

**Priority Issues**:
1. [Issue]: Impacts [X] SMB customers
2. [Issue]: Impacts [X] SMB customers

#### Startup/Individual Users
**Feedback Count**: [X]
**Key Requests**: [Top 3 feature requests]
**Churn Risk**: [Assessment]
**Revenue Impact**: [Growing | Stable | Declining]

**Priority Issues**:
1. [Issue]: High volume, low revenue impact
2. [Issue]: Trend indicator for future segment

---

## Top Requests Ranked by Impact

### Tier 1: Critical (Act Immediately)

| Rank | Request | # Customers | Risk/Opportunity | Timeline | Impact |
| --- | --- | --- | --- | --- | --- |
| 1 | [Request] | [X] | CHURN RISK - $Y | Urgent (1-2 weeks) | Retain [X] customers |
| 2 | [Request] | [X] | EXPANSION - $Y | Soon (3-4 weeks) | Grow [X] customers |

**Explanation**: 
- [Request 1] is critical because [business reason - churn, revenue, competitive]
- [Request 2] is critical because [business reason]

### Tier 2: Important (Plan for Next Quarter)

| Rank | Request | # Customers | Risk/Opportunity | Timeline | Impact |
| --- | --- | --- | --- | --- | --- |
| 3 | [Request] | [X] | Growth opportunity | 4-8 weeks | Enable [use case] |
| 4 | [Request] | [X] | Satisfaction | 2-3 months | Improve NPS by [X pts] |

### Tier 3: Nice-to-Have (Consider for Roadmap)

| Rank | Request | # Customers | Risk/Opportunity | Timeline | Impact |
| --- | --- | --- | --- | --- | --- |
| 5+ | [Request] | [X] | Low-impact | Q[X] or later | [Limited impact] |

---

## Problems vs. Feature Requests

### Critical Problems (Must Fix)
1. **[Problem]**: [X] customers reporting this
   - Impact: [Affects core functionality | Causes workarounds | Limits usage]
   - Effort to Fix: [X hours]
   - Recommendation: FIX IMMEDIATELY
   - Timeline: [Target fix date]

2. **[Problem]**: [X] customers experiencing this
   - Impact: [Description]
   - Effort to Fix: [X hours]
   - Recommendation: FIX in [Timeline]

### Feature Requests (Nice-to-Have)
1. **[Feature]**: [X] customers requesting
   - Business Case: [Why customers want this]
   - Effort to Build: [X story points]
   - Revenue Impact: $[X] or [% increase in usage]
   - Recommendation: Prioritize as [Rank]

---

## Competitive Insights from Customer Feedback

### Where Competitors Win
- [Competitor Feature]: [X] customers mention this as advantage
  - Our Strategy: [How we can compete | When we'll have equivalent]
  
- [Competitor Strength]: [X] customers note this gap in our product
  - Our Strategy: [What we're doing | Timeline]

### Where We Win
- [Our Advantage]: [X] customers praise this vs. competitors
  - Action: Reinforce in marketing, expand on this capability

---

## Customer Health Indicators

### At-Risk Customers
| Customer | Risk Level | Reason | Key Ask | Recommended Action |
| --- | --- | --- | --- | --- |
| [Name] | CRITICAL | [Reason for churn risk] | [Feature] | [Call by X date] |
| [Name] | HIGH | [Reason] | [Feature] | [Offer mitigation] |

### Expansion Opportunities
| Customer | Potential | Key Request | Timeline | Revenue Potential |
| --- | --- | --- | --- | --- |
| [Name] | UPSELL | [Feature] | Q[X] | $[X] |
| [Name] | GROWTH | [Feature] | Q[X] | $[Y] |

---

## Recommendations

### Immediate Actions (Next 2 Weeks)
1. **Fix/Address**: [Critical Problem]
   - Owner: [Name]
   - Target Completion: [Date]
   - Communication: Notify [X customers] when fixed

2. **Customer Outreach**: Call at-risk customers [Names]
   - Owner: [Name]
   - Goal: Understand needs, propose mitigation
   - Expected Outcome: Confirm churn risk and timeline

### Short-term (Next 4-6 Weeks)
1. **Build**: [Tier 1 Feature Request]
   - Addresses: [X customers, $Y revenue, Z% churn prevention]
   - Expected Launch: [Date]
   - Marketing/Sales Plan: [What needs to happen]

2. **Roadmap Communication**: 
   - Publish updated roadmap with [Top Requests]
   - Schedule customer briefings for [Feature X]

### Strategic (Quarter)
1. **Consider Major Initiative**: [Opportunity]
   - Market Potential: [Size]
   - Required Investment: [Effort]
   - Expected ROI: [Timeline to payback]

---

## Next Steps
1. **Validate**: Schedule calls with [X customers] to confirm priorities
2. **Decide**: Review with leadership and finalize [Feature X] decision by [Date]
3. **Communicate**: Share roadmap update with customers by [Date]
4. **Execute**: Kickoff development of [Tier 1 items] in sprint of [Date]
5. **Monitor**: Track churn and NPS for [Customers] monthly
```

---

### 03_Competitive_Analysis.prompt.md

**Use this when:** You have competitor information and market positioning data

**Input Examples:**
- Competitor feature list (screenshot, document, or copy-pasted)
- Customer comments about competitors
- Market research report
- Email with competitive threat
- Feature comparison matrix

**Analysis Focus:**
```markdown
# Competitive Analysis & Market Positioning

## Executive Summary

**Overall Position**: [We are AHEAD | IN LINE WITH | BEHIND competitors]
**Key Gaps**: [What competitors have that we don't]
**Key Advantages**: [Where we lead]
**Competitive Threats**: [Critical issues to address]
**Market Opportunity**: [Where we can differentiate]

---

## Competitive Landscape

### Direct Competitors

#### Competitor 1: [Name]
**Position**: [Market position - leader | challenger | niche player]
**Strengths**:
- [Feature/Capability] - mature, well-integrated
- [Feature/Capability] - strong user base
- [Business model strength]

**Weaknesses**:
- [Gap] - we can exploit
- [Limitation] - customer complaint point
- [Pricing] - higher | lower | similar

**Feature Comparison**:
| Feature | Us | Competitor | Status | Risk |
| --- | --- | --- | --- | --- |
| [Core Feature] | ✅ Advanced | ✅ Basic | IN LINE | No |
| [Feature X] | ❌ None | ✅ Yes | BEHIND | HIGH |
| [Feature Y] | ✅ Yes | ❌ None | AHEAD | No |

**Customer Perception**:
- [Customer feedback about competitor]
- [Why customers choose them vs. us]

**Our Counter-Strategy**:
- [What we're doing to compete]
- [Timeline for competitive feature]
- [How we differentiate]

---

#### Competitor 2: [Name]
**Position**: [Market position]
**Strengths**: [List]
**Weaknesses**: [List]

[Same structure as above]

---

### Indirect/Emerging Competitors
- [Company]: [How they compete | Our response]
- [Company]: [How they compete | Our response]

---

## Feature Matrix: Us vs. Competitors

| Feature Category | Our Product | Competitor A | Competitor B | Competitor C | Our Rating |
| --- | --- | --- | --- | --- | --- |
| **Core Functionality** | | | | | |
| [Feature 1] | Advanced | Basic | None | Advanced | COMPETITIVE ✅ |
| [Feature 2] | None | Advanced | Advanced | None | AT RISK ⚠️ |
| [Feature 3] | Advanced | Advanced | None | Basic | AHEAD ✨ |
| **Integration** | | | | | |
| [Integration 1] | Yes | Yes | Yes | No | STANDARD ✅ |
| [Integration 2] | No | Yes | Yes | Yes | AT RISK ⚠️ |
| **UX/Performance** | | | | | |
| [Metric] | [Our rating] | [Comp A] | [Comp B] | [Comp C] | [Status] |
| **Pricing** | | | | | |
| [Plan] | $X | $Y | $Z | $W | [Comparison] |

**Legend**: ✨ = Competitive Advantage | ✅ = Competitive | ⚠️ = At Risk | ❌ = Significant Gap

---

## Competitive Gaps (Priority by Risk)

### Critical Gaps (High Risk)
| Gap | Competitor | Customers Impacted | Revenue at Risk | Timeline to Close |
| --- | --- | --- | --- | --- |
| [Feature X] | [Competitor] | [X customers] | $[Y] | [When we'll have it] |
| [Feature Y] | [Competitor] | [X customers] | $[Y] | [When we'll have it] |

**Impact**: Losing [X% of pipeline] to competitors lacking [Feature]

**Mitigation Strategy**:
- Short-term: [Workaround | Partner solution | Education]
- Long-term: [Build feature by Date | Roadmap commitment]

### Medium Gaps (Monitor)
| Gap | Competitor | Customer Feedback | Priority | Timeline |
| --- | --- | --- | --- | --- |
| [Feature] | [Competitor] | [X customers mention] | [Priority] | [Plan] |

### Minor Gaps (Nice-to-Have)
| Gap | Competitor | Status | Action |
| --- | --- | --- | --- |
| [Feature] | [Competitor] | Low priority | [Defer or descope] |

---

## Competitive Advantages (Keep/Amplify)

### Existing Strengths

| Advantage | Why It Matters | Customer Value | How to Leverage |
| --- | --- | --- | --- |
| [Feature/Capability] | [Competitors lack this] | [Customer benefit] | Highlight in sales/marketing |
| [Feature/Capability] | [We're significantly better] | [Customer benefit] | Feature in case studies |

### Messaging Strategy
- **Lead with**: [Our key differentiator]
- **Against Competitor A**: [Key messaging point]
- **Against Competitor B**: [Key messaging point]

---

## Market Positioning Strategy

### How We Differentiate
1. **[Dimension]**: We focus on [differentiation]
   - Supported by [Feature X]
   - Validated by [Customer feedback | Market research]

2. **[Dimension]**: We lead in [differentiation]
   - Supported by [Feature Y]
   - Validated by [Customer feedback | Market research]

3. **[Dimension]**: We're unique in [differentiation]
   - Supported by [Feature Z]
   - Opportunity: Expand into [Adjacent market]

### Pricing Strategy
- **Current**: $[X] - [Positioning]
- **Competitor Range**: $[Y] to $[Z]
- **Recommendation**: [Stay competitive | Increase for value | Bundle strategy]

---

## Market Threats & Opportunities

### Immediate Threats (Next 2-4 Weeks)
| Threat | Severity | Impact | Counter-Action |
| --- | --- | --- | --- |
| [New competitor feature] | HIGH | [Loses X deals] | [Our counter] |
| [Competitor pricing change] | MEDIUM | [X% pipeline risk] | [Our response] |

### Market Opportunities (Next Quarter+)
| Opportunity | Market Size | Our Readiness | Action |
| --- | --- | --- | --- |
| [Emerging segment/use case] | [Size] | [Readiness] | [Build/Partner/Wait] |
| [Geographic expansion] | [Market size] | [Readiness] | [Entry strategy] |

---

## Recommendations

### Prioritize These Features
1. **[Feature]**: Required to close deals vs. [Competitor]
   - Priority: IMMEDIATE (closes X deals/month)
   - Timeline: [When to deliver]
   
2. **[Feature]**: Required to reduce churn to [Competitor]
   - Priority: URGENT (prevents $X revenue churn)
   - Timeline: [When to deliver]

### Messaging & Marketing
1. **Update sales deck** with competitive positioning
2. **Create comparison guide** for [Competitor A] differentiation
3. **Train sales team** on messaging against [Top competitor]

### Product Roadmap Alignment
- Tie [Feature] to competitive threat [X]
- Accelerate [Feature] that [Competitor] just launched
- Double down on [Advantage] that differentiates us

### Customer Communication
- Reassure [At-risk customers] with roadmap showing [Feature X]
- Highlight [Advantage Y] in customer communications
- Schedule competitive briefing calls for [Sales team]

---

## Next Steps
1. **Validate**: Get feedback from sales on competitive dynamics
2. **Prioritize**: Lock in roadmap decisions by [Date]
3. **Execute**: Launch counter-competitive features in Sprint [X]
4. **Monitor**: Track win/loss reasons weekly
5. **Iterate**: Monthly competitive assessment
```

---

## Usage Guidelines

### Providing Feedback Data
1. **Copy-paste emails or chat**: Include full context
2. **Attach survey results**: Raw data or summarized results
3. **Share customer names**: Or anonymize as "[Customer Type]"
4. **Provide timestamps**: When feedback was collected

### Expected Output
- **Prioritized list** of what to build
- **Customer segments** affected by gaps
- **Revenue impact** of prioritization
- **Timeline** for execution
- **Communication plan** for customers

### Tips for Best Results
✅ Include multiple feedback sources (not just sales)
✅ Mix quantitative (# of requests) with qualitative (actual quotes)
✅ Provide customer context (type, size, revenue value)
✅ Mention any known competitive threats
✅ Include NPS and churn data if available

# Product Manager Agent - Customer Feedback Synthesis

## Purpose
Analyze customer feedback from multiple sources (tickets, surveys, calls, emails) to identify trends, pain points, and opportunities.

## Supported Input Formats
- Support ticket exports
- Email threads with feedback
- Survey results
- Slack message compilations
- Feature request lists
- NPS survey responses
- Customer meeting notes
- Support chat transcripts

## Analysis Framework

When analyzing customer feedback:

1. **Categorize by Theme**
   - Feature requests
   - Bug reports
   - UX/usability issues
   - Performance complaints
   - Integration requests

2. **Analyze Sentiment**
   - Positive/Promoter
   - Neutral/Passive
   - Negative/Detractor

3. **Extract Business Signals**
   - Churn risk
   - Upsell opportunity
   - Competitive threat
   - Urgent vs. nice-to-have

4. **Segment by Customer Type**
   - Enterprise
   - SMB
   - Startup
   - By industry/geography if relevant

## Output Format

### Feedback Summary Dashboard

**Total Items Analyzed:** [X]  
**Date Range:** [X to X]  
**Sources:** [List]  
**Key Segment:** [Most vocal]

### Top Issues/Requests (Ranked by Impact)

| Rank | Request/Issue | # Customers | Sentiment | Impact | Timeline |
|------|---------------|-------------|-----------|--------|----------|
| 1 | [Description] | [X] | Negative | CHURN RISK | URGENT |
| 2 | [Description] | [X] | Positive | EXPANSION | SOON |

### Customer Segments Affected

**Enterprise:** [Key themes, revenue at risk]
**SMB:** [Key themes, growth potential]
**Startup:** [Key themes, volume indicators]

### Sentiment Breakdown
- Promoters (Positive): [X]% - [Key praise]
- Passives (Neutral): [X]% - [What's okay]
- Detractors (Negative): [X]% - [Critical issues]

### Recommendations
1. **Urgent Fixes:** [Issue] - Prevents churn from [X customers]
2. **Feature Builds:** [Feature] - Requested by [X] customers
3. **Strategic:** [Opportunity] - Market potential $[X]

## Input Examples

**Support Tickets:**
```
Ticket #123: Customer reporting API timeout errors
Ticket #124: Requesting bulk export feature
Ticket #125: SSO integration needed for enterprise rollout
```

**Email/Slack:**
```
Sales: ABC Corp wants feature X before renewal - renews in 30 days
Support: Getting 5+ requests per week for CSV export
Customer call: "Your UI is confusing, competitors are cleaner"
```

**Survey Results:**
```
NPS: 45 (Detractors 25%, Passives 30%, Promoters 45%)
Top frustration: Dashboard is hard to use
Top request: Mobile app
Would leave for competitor if: They added [Feature]
```

## Tips for Best Results
✅ Include customer names/types for context
✅ Quote actual customer feedback
✅ Mention if feedback is from single customer or multiple
✅ Note customer value (enterprise, strategic, etc.)
✅ Include dates to identify trends

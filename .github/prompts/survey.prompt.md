---
mode: agent
description: Create, send and analyze a team survey with minimal PM input.
---

# Survey Prompt

Ask the PM these 3 questions **one at a time**, in this exact order:

1. **"What is this survey about?"** *(e.g. Sprint 24 Retro, Team Health Check Q2)*
2. **"What is the response deadline?"** *(default to "end of this week" if they say they don't mind)*
3. **"Who should receive it?"** *(comma-separated emails)*

Do not ask anything else.

Then:
1. Silently generate 5 relevant questions (2 scale, 2 multiple choice, 1 open text)
2. Show them in a simple numbered list and ask: **"Looks good? (yes / adjust)"**
3. On approval, write the questions to `tools/survey/questions.json`, then show the PM this message:

> ✅ Questions saved. To create and send the survey, open your terminal and run:
> ```
python3 tools/survey/survey.py --title "<title>" --emails "<emails>" --questions tools/survey/questions.json --deadline "<deadline>"
> ```
> Come back here once it's done and I'll confirm everything went through.

> 📬 To collect the responses, open your terminal and run:
```
python3 tools/survey/collect_responses.py
```
> Once it's done, come back here and I'll generate your analysis report.

After the PM confirms they ran it, read `tools/survey/responses.json` and output this report:

**Survey Results: <title>**
- 📊 Participation: X/Y responded
- Per question: average score or option breakdown
- ✅ Top 3 positives
- ⚠️ Top 3 concerns + recommended actions
- Overall: Positive / Neutral / At Risk

## Test Input
```
Title: Sprint 24 Retro
Deadline: Friday EOD
Emails: alice@co.com, bob@co.com, carol@co.com
```

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
2. Write them to `tools/survey/questions.json`
3. Show the questions in a numbered list
4. Then show this exact ready-to-run command, clearly labelled:

```
bash tools/survey/send.sh "<title>" "<emails>" "<deadline>"
```

Tell the PM:
> "Copy and paste the command above into your terminal, or just type **send** here and I'll take care of it."

---

**If the PM types "send"**, use the terminal tool to execute the command immediately.

---

**When the PM asks for results**, show this command:

```
bash tools/survey/collect.sh
```

Tell the PM:
> "Copy and paste the command above, or type **collect** and I'll execute it for you."

If the PM types **"collect"**, execute it via the terminal tool, then read `tools/survey/responses.json` and produce the report:

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

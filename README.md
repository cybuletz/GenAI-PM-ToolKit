# Survey Agent — GenAI PM Toolkit

Automates the creation, distribution, and analysis of team surveys using Google Forms and Gmail — all under your own Google account.

---

## One-Time Setup (per person, ~5 minutes)

### 1. Install Python dependencies
```bash
pip install -r tools/survey/requirements.txt
```

### 2. Create your Google Cloud project
- Go to [console.cloud.google.com](https://console.cloud.google.com)
- Click **Select a project → New Project** (any name, e.g. `pm-survey-agent`)
- Click **Create**

### 3. Enable the required APIs
Inside your new project:
- Go to **APIs & Services → Enable APIs and Services**
- Search and enable each of these one by one:
  - **Google Forms API**
  - **Google Drive API**
  - **Gmail API**

### 4. Create OAuth credentials
- Go to **APIs & Services → Credentials**
- Click **Create Credentials → OAuth 2.0 Client ID**
- If prompted to configure the consent screen: choose **External**, fill in any app name, add your email, save
- Application type: **Desktop App**
- Name it anything (e.g. `Survey Agent`)
- Click **Create**
- Click **Download JSON** → rename the file to `credentials.json`
- Place `credentials.json` in the `tools/survey/` folder

### 5. Add yourself as a test user (required while app is in testing)
- Go to **APIs & Services → OAuth consent screen**
- Scroll to **Test users → Add Users**
- Add your own Gmail address

---

## Running the Agent

### Option A — Via Copilot Chat (recommended)
Open VS Code, open Copilot Chat, select the **Survey Agent** from the agent picker, and type:

> "Create a sprint retrospective survey for my team"

The agent will guide you through the rest.

### Option B — Direct command line

**Step 1: Create and send the survey**
```bash
python tools/survey/survey.py \
  --title "Sprint 42 Retrospective" \
  --emails "alice@company.com,bob@company.com,carol@company.com" \
  --questions tools/survey/questions.example.json
```
On first run, a browser window will open. Log in with your Gmail and approve permissions. This happens once — after that it runs automatically.

**Step 2: Collect responses (after the deadline)**
```bash
python tools/survey/collect_responses.py
```
Responses are saved to `tools/survey/responses.json`.

**Step 3: Analyze**
Ask the Survey Agent in Copilot Chat to analyze the responses, or paste the contents of `responses.json` into any chat.

---

## Files

| File | Purpose |
|---|---|
| `.github/agents/survey-agent.agent.md` | Copilot agent definition |
| `tools/survey/survey.py` | Creates Google Form + sends Gmail invites |
| `tools/survey/collect_responses.py` | Fetches and saves responses from Google Forms |
| `tools/survey/questions.example.json` | Example questions file — copy and customise |
| `tools/survey/requirements.txt` | Python dependencies |
| `tools/survey/credentials.json` | ⚠️ YOUR file — never commit, never share |
| `tools/survey/token.json` | Auto-generated after first login — never commit |

---

## Question Types Supported

| Type | JSON value | Description |
|---|---|---|
| Scale | `"scale"` | 1–5 rating (Low → High) |
| Multiple choice | `"multiple_choice"` | Radio buttons, provide `"options"` array |
| Open text | `"text"` | Free text answer |

---

## Privacy & Security

- Your `credentials.json` and `token.json` are listed in `.gitignore` — they will never be committed
- Each person uses their own Google account — no shared credentials
- Survey responses are saved locally to your machine only

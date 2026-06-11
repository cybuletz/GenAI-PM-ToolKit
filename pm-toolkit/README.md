# PM Toolkit – Desktop App

A standalone desktop app wrapping the GenAI PM Toolkit agents into a simple UI for project managers. No VS Code or terminal required.

## What's Inside

| Panel | Agent | What it does |
|---|---|---|
| 📋 Survey | Survey Agent | Creates Google Form surveys, emails recipients, collects and analyses responses |
| 📊 Metrics | Scrum Master – Metrics & Capacity | Analyses sprint data, generates velocity and capacity reports |
| 📢 Stakeholder | Stakeholder Communicator | Drafts executive status reports, sprint summaries, meeting follow-ups |

## Setup

### 1. Install dependencies
```bash
cd pm-toolkit
pip install -r requirements.txt
```

### 2. Google / Gmail credentials (for Survey panel)
Place your `credentials.json` (Google OAuth Desktop App) in `tools/survey/credentials.json`.  
Follow the [Google Cloud Console setup guide](https://developers.google.com/forms/api/quickstart/python) to create it.

### 3. Run the app
```bash
python main.py
```

### 4. Sign in
- Click **Sign In** next to **Gmail** in the bottom bar → browser opens for Google OAuth
- Click **Sign In** next to **Copilot** → browser opens, enter the displayed code on github.com/login/device
- Select your preferred model from the dropdown

## Packaging as Executable

### Mac
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "PM Toolkit" main.py
```
Output: `dist/PM Toolkit.app`

### Windows
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "PM Toolkit" main.py
```
Output: `dist/PM Toolkit.exe`

## Notes
- The Survey panel calls `tools/survey/survey.py` and `tools/survey/collect_responses.py` directly in-process — no terminal commands or copy-pasting needed.
- The Gmail `token.json` is shared between this app and the VS Code agent, so you only need to sign in once.
- All settings (theme, model, tokens) are saved to `pm-toolkit/settings.json` locally.

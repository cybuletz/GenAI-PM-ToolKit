import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]

# Token and credentials live alongside the survey scripts to stay compatible
SURVEY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
TOKEN_FILE = os.path.abspath(os.path.join(SURVEY_DIR, "token.json"))
CREDENTIALS_FILE = os.path.abspath(os.path.join(SURVEY_DIR, "credentials.json"))


class GmailAuth:
    """
    Reuses the same OAuth flow as tools/survey/survey.py
    so that signing in from the desktop app and from VS Code
    share the same token.json file.
    """

    def authenticate(self) -> str:
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        "credentials.json not found in tools/survey/.\n"
                        "Please follow the README setup steps to download your Google OAuth credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        return TOKEN_FILE

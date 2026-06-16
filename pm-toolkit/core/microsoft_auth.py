"""
MicrosoftAuth — MSAL interactive browser sign-in + silent token refresh.

Mirrors GmailAuth exactly:
  - Reads Client ID from tools/survey/ms_credentials.json  (one-time setup)
  - Caches the token to tools/survey/ms_token_cache.json
  - On subsequent calls: refreshes silently, never re-opens the browser

ms_credentials.json format:
  { "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" }

The browser pop-up is a real Microsoft login page — same experience as Gmail.
"""
import os
import json
import msal

SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Files.ReadWrite.AppFolder",
    "https://graph.microsoft.com/User.Read",
]

SURVEY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
CREDENTIALS_FILE = os.path.abspath(os.path.join(SURVEY_DIR, "ms_credentials.json"))
CACHE_FILE       = os.path.abspath(os.path.join(SURVEY_DIR, "ms_token_cache.json"))


class MicrosoftAuth:
    """
    Drop-in Microsoft equivalent of GmailAuth.
    Call authenticate() → returns a valid access token string.
    """

    def authenticate(self) -> str:
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(
                "ms_credentials.json not found in tools/survey/.\n"
                "Create it with: { \"client_id\": \"<your-azure-app-id>\" }\n"
                "Register a free public-client app at portal.azure.com — "
                "see README for the 3-minute setup."
            )
        with open(CREDENTIALS_FILE) as fh:
            config = json.load(fh)
        client_id = config["client_id"]

        cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as fh:
                cache.deserialize(fh.read())

        app = msal.PublicClientApplication(
            client_id,
            authority="https://login.microsoftonline.com/common",
            token_cache=cache,
        )

        # Try silent refresh first (no browser needed after first sign-in)
        result = None
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])

        # First time (or cache expired) — open the browser, just like Gmail
        if not result:
            result = app.acquire_token_interactive(scopes=SCOPES)

        if "error" in result:
            raise RuntimeError(
                f"Microsoft sign-in failed: {result.get('error_description', result['error'])}"
            )

        # Persist the updated cache so the next call is silent
        if cache.has_state_changed:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w") as fh:
                fh.write(cache.serialize())

        return result["access_token"]

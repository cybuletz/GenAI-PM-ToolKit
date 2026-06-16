"""
MicrosoftAuth — browser-redirect OAuth2 sign-in via MSAL.

Mirrors GmailAuth exactly:
  - Reads Client ID from tools/survey/ms_credentials.json  (one-time setup by developer)
  - Caches token to tools/survey/ms_token_cache.json
  - First call → browser opens → user signs in to Microsoft
  - Every call after → silent refresh, browser never re-opens

ms_credentials.json format:
  { "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" }

App Registration is FREE — no Azure subscription needed.
See README_MS365_SETUP.md for the 5-minute setup guide.
"""

import os
import json
import msal

SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Files.ReadWrite.AppFolder",
    "https://graph.microsoft.com/User.Read",
]

SURVEY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
)
CREDENTIALS_FILE = os.path.join(SURVEY_DIR, "ms_credentials.json")
CACHE_FILE       = os.path.join(SURVEY_DIR, "ms_token_cache.json")

_AUTHORITY = "https://login.microsoftonline.com/common"


class MicrosoftAuth:
    """
    Drop-in Microsoft equivalent of GmailAuth.
    Call authenticate() → returns a valid access token string.
    """

    def authenticate(self) -> str:
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(
                "ms_credentials.json not found in tools/survey/.\n"
                "Follow README_MS365_SETUP.md for the one-time setup (5 minutes, free).\n"
                "No Azure subscription required — only a free App Registration."
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
            authority=_AUTHORITY,
            token_cache=cache,
        )

        # Try silent refresh first — no browser needed after first sign-in
        result = None
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])

        # First time (or cache expired) — opens the real Microsoft login page in browser
        if not result:
            result = app.acquire_token_interactive(scopes=SCOPES)

        if not result or "error" in result:
            raise RuntimeError(
                "Microsoft sign-in failed: "
                + (result.get("error_description") or result.get("error") or "unknown")
                if result else "Microsoft sign-in failed: no response"
            )

        # Persist cache so every subsequent call is silent
        if cache.has_state_changed:
            os.makedirs(SURVEY_DIR, exist_ok=True)
            with open(CACHE_FILE, "w") as fh:
                fh.write(cache.serialize())

        return result["access_token"]

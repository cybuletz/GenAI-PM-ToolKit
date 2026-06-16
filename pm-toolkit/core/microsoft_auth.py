"""
MicrosoftAuth — browser-redirect OAuth2 sign-in via MSAL.

Zero Azure setup required. Uses Microsoft's own pre-registered Office
desktop client ID (d3590ed6-52b3-4102-aeff-aad2292ab01c), which is
trusted by every personal, work, and school Microsoft account — identical
to how Google's credentials.json is pre-created by the developer so
end-users never touch the Google Cloud Console.

Flow (mirrors GmailAuth exactly):
  1. First call  → browser opens → user signs into Microsoft → token cached
  2. Every call after → silent refresh, browser never opens again
  3. Cache file: tools/survey/ms_token_cache.json  (mirrors token.json)
"""

import os
import msal

# Microsoft's own Office desktop app client — pre-registered, no Azure setup needed.
# Scope: least-privilege for Mail.Send + OneDrive AppFolder + basic profile.
_CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"
_AUTHORITY  = "https://login.microsoftonline.com/common"

SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Files.ReadWrite.AppFolder",
    "https://graph.microsoft.com/User.Read",
]

SURVEY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
)
CACHE_FILE = os.path.join(SURVEY_DIR, "ms_token_cache.json")


class MicrosoftAuth:
    """
    Drop-in Microsoft equivalent of GmailAuth.
    Call authenticate() → browser opens once → returns a valid access token.
    """

    def authenticate(self) -> str:
        cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as fh:
                cache.deserialize(fh.read())

        app = msal.PublicClientApplication(
            _CLIENT_ID,
            authority=_AUTHORITY,
            token_cache=cache,
        )

        # Try silent refresh first — no browser needed after first sign-in
        result = None
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])

        # First time (or cache expired) — open the real Microsoft login page
        if not result:
            result = app.acquire_token_interactive(scopes=SCOPES)

        if not result or "error" in result:
            raise RuntimeError(
                f"Microsoft sign-in failed: "
                f"{result.get('error_description', result.get('error', 'unknown error')) if result else 'no response'}"
            )

        # Persist cache so the next call is always silent
        if cache.has_state_changed:
            os.makedirs(SURVEY_DIR, exist_ok=True)
            with open(CACHE_FILE, "w") as fh:
                fh.write(cache.serialize())

        return result["access_token"]

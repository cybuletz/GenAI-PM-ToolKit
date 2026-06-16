"""
MicrosoftAuth — MSAL interactive browser sign-in + silent token refresh.
Mirrors the GmailAuth pattern so the desktop app and CLI share the same
token cache file.

Token cache: tools/survey/ms_token_cache.json
"""
import os
import json
import msal

SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Files.ReadWrite.AppFolder",
    "https://graph.microsoft.com/User.Read",
]

# Keep the cache alongside the Google token so both live in tools/survey/
SURVEY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
CACHE_FILE = os.path.abspath(os.path.join(SURVEY_DIR, "ms_token_cache.json"))

# Public client — no secret needed for desktop apps
CLIENT_ID = os.environ.get("MS_CLIENT_ID", "")


class MicrosoftAuth:
    """
    Interactive MSAL authentication.
    After calling authenticate() the returned access token can be passed
    directly to MicrosoftGraphClient.
    """

    def __init__(self, client_id: str = ""):
        self._client_id = client_id or CLIENT_ID
        if not self._client_id:
            raise EnvironmentError(
                "MS_CLIENT_ID environment variable is not set.\n"
                "Register a public-client Azure app and set the variable before signing in."
            )
        self._cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as fh:
                self._cache.deserialize(fh.read())
        self._app = msal.PublicClientApplication(
            self._client_id,
            authority="https://login.microsoftonline.com/common",
            token_cache=self._cache,
        )

    def authenticate(self) -> str:
        """Return a valid access token, refreshing silently when possible."""
        accounts = self._app.get_accounts()
        result = None
        if accounts:
            result = self._app.acquire_token_silent(SCOPES, account=accounts[0])
        if not result:
            result = self._app.acquire_token_interactive(scopes=SCOPES)
        if "error" in result:
            raise RuntimeError(
                f"Microsoft sign-in failed: {result.get('error_description', result['error'])}"
            )
        self._persist_cache()
        return result["access_token"]

    def _persist_cache(self):
        if self._cache.has_state_changed:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w") as fh:
                fh.write(self._cache.serialize())

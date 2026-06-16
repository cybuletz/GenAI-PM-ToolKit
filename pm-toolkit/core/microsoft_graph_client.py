"""
MicrosoftGraphClient — thin requests wrapper around the Microsoft Graph REST API.
Auto-injects the Bearer token and retries on 429 (rate-limit) and 5xx responses.
"""
import time
import requests

BASE_URL = "https://graph.microsoft.com/v1.0"
_MAX_RETRIES = 3


class MicrosoftGraphClient:
    def __init__(self, access_token: str):
        self._token = access_token
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {access_token}",
             "Content-Type": "application/json"}
        )

    def get(self, path: str, **kwargs) -> dict:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, json: dict = None, **kwargs) -> dict:
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, data: bytes = None, headers: dict = None) -> requests.Response:
        """Raw PUT for OneDrive binary uploads; returns the Response object."""
        hdrs = {"Authorization": f"Bearer {self._token}"}
        if headers:
            hdrs.update(headers)
        for attempt in range(_MAX_RETRIES):
            resp = requests.put(
                BASE_URL + path, data=data, headers=hdrs, timeout=30
            )
            if resp.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            return resp
        resp.raise_for_status()
        return resp

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = BASE_URL + path
        for attempt in range(_MAX_RETRIES):
            resp = self._session.request(method, url, timeout=30, **kwargs)
            if resp.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            if resp.status_code == 204:
                return {}
            resp.raise_for_status()
            return resp.json()
        resp.raise_for_status()
        return {}

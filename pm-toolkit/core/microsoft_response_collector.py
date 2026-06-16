"""
MicrosoftResponseCollector — reads survey responses stored in OneDrive
at Apps/PMToolkit/responses/<survey_id>.json.
Mirrors ResponseCollector public API.
"""
import json
from core.microsoft_graph_client import MicrosoftGraphClient

ONEDRIVE_FOLDER = "Apps/PMToolkit/responses"


class MicrosoftResponseCollector:
    def __init__(self, access_token: str):
        self._client = MicrosoftGraphClient(access_token)

    def collect(self, survey_id: str) -> list:
        path = f"/{ONEDRIVE_FOLDER}/{survey_id}.json"
        try:
            meta = self._client.get(f"/me/drive/root:{path}")
            item_id = meta["id"]
            resp = self._client._session.get(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content",
                timeout=15,
            )
            resp.raise_for_status()
            return json.loads(resp.content.decode("utf-8"))
        except Exception:
            return []

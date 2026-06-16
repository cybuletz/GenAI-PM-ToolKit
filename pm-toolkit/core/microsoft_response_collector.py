"""
MicrosoftResponseCollector — reads survey responses that were POSTed
by the HTML survey page and stored in OneDrive as JSON.

Expected file path: Apps/PMToolkit/responses/<survey_id>.json
Schema: list of { submitted_at, respondent_email, answers: {q_text: value} }

If the collection endpoint has not yet written responses, returns an empty list.
Mirrors ResponseCollector's public API.
"""
import json
from core.microsoft_graph_client import MicrosoftGraphClient

ONEDRIVE_FOLDER = "Apps/PMToolkit/responses"


class MicrosoftResponseCollector:
    def __init__(self, access_token: str):
        self._client = MicrosoftGraphClient(access_token)

    def collect(self, survey_id: str) -> list:
        """
        Fetch all responses for the given survey_id.

        Returns a list of dicts:
          {
            "submitted_at": <ISO str>,
            "respondent_email": <str>,
            "answers": {<question text>: <answer value>}
          }
        """
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

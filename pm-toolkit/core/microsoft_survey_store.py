"""
MicrosoftSurveyStore — persists the survey index to a single JSON file
in the user's OneDrive /Apps/PMToolkit/ folder (app-folder pattern).

File: Apps/PMToolkit/pm_toolkit_surveys.json

On any machine, as long as the user signs in with the same Microsoft account,
the full survey history is available — mirrors the Google Drive SurveyStore.
"""
import json
import uuid
from datetime import datetime, timezone
from core.microsoft_graph_client import MicrosoftGraphClient

INDEX_FILENAME = "pm_toolkit_surveys.json"
ONEDRIVE_FOLDER = "Apps/PMToolkit"
INDEX_PATH = f"{ONEDRIVE_FOLDER}/{INDEX_FILENAME}"


class MicrosoftSurveyStore:
    def __init__(self, access_token: str):
        self._client = MicrosoftGraphClient(access_token)
        self._item_id, self._data = self._load_or_create()

    # ------------------------------------------------------------------ #
    #  Public API  (same surface as SurveyStore)                         #
    # ------------------------------------------------------------------ #

    def all_surveys(self) -> list:
        return sorted(self._data["surveys"],
                      key=lambda s: s["sent_at"], reverse=True)

    def add_survey(self, title: str, survey_id: str, survey_url: str,
                   recipients: list, question_count: int) -> dict:
        record = {
            "id": str(uuid.uuid4()),
            "title": title,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "survey_id": survey_id,
            "survey_url": survey_url,
            "recipients": recipients,
            "question_count": question_count,
            "response_count": 0,
        }
        self._data["surveys"].append(record)
        self._save()
        return record

    def update_response_count(self, survey_id: str, count: int):
        for s in self._data["surveys"]:
            if s["id"] == survey_id:
                s["response_count"] = count
                break
        self._save()

    def last_n(self, n: int) -> list:
        return self.all_surveys()[:n]

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _load_or_create(self) -> tuple:
        try:
            meta = self._client.get(f"/me/drive/root:/{INDEX_PATH}")
            item_id = meta["id"]
            content_resp = self._client._session.get(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content",
                timeout=15,
            )
            content_resp.raise_for_status()
            data = json.loads(content_resp.content.decode("utf-8"))
            return item_id, data
        except Exception:
            empty = {"surveys": []}
            item_id = self._upload(INDEX_FILENAME, empty)
            return item_id, empty

    def _save(self):
        self._item_id = self._upload(INDEX_FILENAME, self._data)

    def _upload(self, filename: str, data: dict) -> str:
        content = json.dumps(data, indent=2).encode("utf-8")
        resp = self._client.put(
            f"/me/drive/root:/{ONEDRIVE_FOLDER}/{filename}:/content",
            data=content,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json().get("id", "")

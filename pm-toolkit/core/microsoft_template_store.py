"""
MicrosoftTemplateStore — persists survey templates to OneDrive Apps/PMToolkit/pm_toolkit_templates.json.
Mirrors TemplateStore (Google Drive) with identical public API.
"""
import json
import uuid
from datetime import datetime, timezone
from core.microsoft_graph_client import MicrosoftGraphClient

TEMPLATES_FILENAME = "pm_toolkit_templates.json"
ONEDRIVE_FOLDER = "Apps/PMToolkit"
TEMPLATES_PATH = f"{ONEDRIVE_FOLDER}/{TEMPLATES_FILENAME}"


class MicrosoftTemplateStore:
    def __init__(self, access_token: str):
        self._client = MicrosoftGraphClient(access_token)
        self._item_id, self._data = self._load_or_create()

    def all_templates(self) -> list:
        def sort_key(t):
            return t.get("last_used_at") or t.get("created_at") or ""
        return sorted(self._data["templates"], key=sort_key, reverse=True)

    def add_template(self, name: str, questions: list) -> dict:
        record = {
            "id": str(uuid.uuid4()),
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used_at": None,
            "use_count": 0,
            "questions": questions,
        }
        self._data["templates"].append(record)
        self._save()
        return record

    def update_template(self, template_id: str, name: str, questions: list):
        for t in self._data["templates"]:
            if t["id"] == template_id:
                t["name"] = name
                t["questions"] = questions
                break
        self._save()

    def delete_template(self, template_id: str):
        self._data["templates"] = [t for t in self._data["templates"] if t["id"] != template_id]
        self._save()

    def record_use(self, template_id: str):
        for t in self._data["templates"]:
            if t["id"] == template_id:
                t["use_count"] = t.get("use_count", 0) + 1
                t["last_used_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._save()

    def _load_or_create(self) -> tuple:
        try:
            meta = self._client.get(f"/me/drive/root:/{TEMPLATES_PATH}")
            item_id = meta["id"]
            content_resp = self._client._session.get(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content",
                timeout=15,
            )
            content_resp.raise_for_status()
            return item_id, json.loads(content_resp.content.decode("utf-8"))
        except Exception:
            empty = {"templates": []}
            return self._upload(TEMPLATES_FILENAME, empty), empty

    def _save(self):
        self._item_id = self._upload(TEMPLATES_FILENAME, self._data)

    def _upload(self, filename: str, data: dict) -> str:
        resp = self._client.put(
            f"/me/drive/root:/{ONEDRIVE_FOLDER}/{filename}:/content",
            data=json.dumps(data, indent=2).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json().get("id", "")

"""
TemplateStore — persists survey question templates to a single JSON file
in Google Drive, under the same 'PM Toolkit' folder as the survey index.

File: PM Toolkit/pm_toolkit_templates.json

Schema:
  {
    "templates": [
      {
        "id": "<uuid>",
        "name": "Sprint Retro (Standard)",
        "created_at": "<ISO>",
        "last_used_at": "<ISO or null>",
        "use_count": 0,
        "questions": [
          {"text": "...", "type": "scale" | "multiple_choice" | "text",
           "options": ["..."]}
        ]
      }
    ]
  }
"""
import json
import io
import uuid
from datetime import datetime, timezone

TEMPLATES_FILENAME = "pm_toolkit_templates.json"
DRIVE_FOLDER_NAME = "PM Toolkit"


class TemplateStore:
    def __init__(self, creds):
        from googleapiclient.discovery import build
        self._drive = build("drive", "v3", credentials=creds)
        self._folder_id = self._ensure_folder()
        self._file_id, self._data = self._load_or_create()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def all_templates(self) -> list:
        """Return templates sorted by most recently used / created."""
        def sort_key(t):
            return t.get("last_used_at") or t.get("created_at") or ""
        return sorted(self._data["templates"], key=sort_key, reverse=True)

    def add_template(self, name: str, questions: list) -> dict:
        """Create and persist a new template. Returns the new record."""
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
        """Overwrite name and questions for an existing template."""
        for t in self._data["templates"]:
            if t["id"] == template_id:
                t["name"] = name
                t["questions"] = questions
                break
        self._save()

    def delete_template(self, template_id: str):
        """Remove a template by id."""
        self._data["templates"] = [
            t for t in self._data["templates"] if t["id"] != template_id
        ]
        self._save()

    def record_use(self, template_id: str):
        """Increment use_count and update last_used_at."""
        for t in self._data["templates"]:
            if t["id"] == template_id:
                t["use_count"] = t.get("use_count", 0) + 1
                t["last_used_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._save()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _ensure_folder(self) -> str:
        """Get or create the 'PM Toolkit' folder in Drive root."""
        q = (
            f"name='{DRIVE_FOLDER_NAME}' "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        )
        results = self._drive.files().list(q=q, fields="files(id)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]
        meta = {
            "name": DRIVE_FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = self._drive.files().create(body=meta, fields="id").execute()
        return folder["id"]

    def _load_or_create(self) -> tuple:
        """Load existing templates file from Drive, or create a fresh one."""
        q = (
            f"name='{TEMPLATES_FILENAME}' "
            f"and '{self._folder_id}' in parents "
            "and trashed=false"
        )
        results = self._drive.files().list(q=q, fields="files(id)").execute()
        files = results.get("files", [])

        if files:
            file_id = files[0]["id"]
            content = self._drive.files().get_media(fileId=file_id).execute()
            data = json.loads(content.decode("utf-8"))
            return file_id, data

        empty = {"templates": []}
        file_id = self._upload(TEMPLATES_FILENAME, empty, file_id=None)
        return file_id, empty

    def _save(self):
        self._file_id = self._upload(
            TEMPLATES_FILENAME, self._data, file_id=self._file_id
        )

    def _upload(self, name: str, data: dict, file_id) -> str:
        content = json.dumps(data, indent=2).encode("utf-8")
        media = self._media(content)
        if file_id:
            self._drive.files().update(fileId=file_id, media_body=media).execute()
            return file_id
        meta = {"name": name, "parents": [self._folder_id]}
        f = self._drive.files().create(
            body=meta, media_body=media, fields="id"
        ).execute()
        return f["id"]

    @staticmethod
    def _media(content: bytes):
        from googleapiclient.http import MediaIoBaseUpload
        return MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype="application/json",
            resumable=False,
        )

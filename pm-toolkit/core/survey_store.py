"""
SurveyStore — persists the survey index to a single JSON file in Google Drive.

File: PM Toolkit/pm_toolkit_surveys.json  (inside a 'PM Toolkit' folder in Drive root)

On any machine, as long as the user signs in with the same Google account,
the full survey history is available.
"""
import json
import io
import uuid
from datetime import datetime, timezone

INDEX_FILENAME = "pm_toolkit_surveys.json"
DRIVE_FOLDER_NAME = "PM Toolkit"


class SurveyStore:
    def __init__(self, creds):
        from googleapiclient.discovery import build
        self._drive = build("drive", "v3", credentials=creds)
        self._folder_id = self._ensure_folder()
        self._file_id, self._data = self._load_or_create()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def all_surveys(self) -> list:
        """Return surveys sorted newest-first."""
        return sorted(self._data["surveys"], key=lambda s: s["sent_at"], reverse=True)

    def add_survey(self, title: str, form_id: str, sheet_id: str,
                   recipients: list, question_count: int) -> dict:
        """Append a new survey record and persist to Drive."""
        record = {
            "id": str(uuid.uuid4()),
            "title": title,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "form_id": form_id,
            "sheet_id": sheet_id,
            "recipients": recipients,
            "question_count": question_count,
            "response_count": 0,
        }
        self._data["surveys"].append(record)
        self._save()
        return record

    def update_response_count(self, survey_id: str, count: int):
        """Update the cached response count after a collect."""
        for s in self._data["surveys"]:
            if s["id"] == survey_id:
                s["response_count"] = count
                break
        self._save()

    def last_n(self, n: int) -> list:
        """Return the n most-recent surveys."""
        return self.all_surveys()[:n]

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
        """Load existing index file from Drive, or create a fresh one."""
        q = (
            f"name='{INDEX_FILENAME}' "
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

        # Create fresh
        empty = {"surveys": []}
        file_id = self._upload(INDEX_FILENAME, empty, file_id=None)
        return file_id, empty

    def _save(self):
        self._file_id = self._upload(INDEX_FILENAME, self._data, file_id=self._file_id)

    def _upload(self, name: str, data: dict, file_id: str | None) -> str:
        content = json.dumps(data, indent=2).encode("utf-8")
        media = self._media(content)
        if file_id:
            self._drive.files().update(fileId=file_id, media_body=media).execute()
            return file_id
        meta = {"name": name, "parents": [self._folder_id]}
        f = self._drive.files().create(body=meta, media_body=media, fields="id").execute()
        return f["id"]

    @staticmethod
    def _media(content: bytes):
        from googleapiclient.http import MediaIoBaseUpload
        return MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype="application/json",
            resumable=False
        )

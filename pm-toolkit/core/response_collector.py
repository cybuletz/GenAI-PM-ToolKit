"""
ResponseCollector — fetches responses from the Google Sheet linked to a Form.

Works at any time after the survey is sent, regardless of whether the app
was open. Partial responses (not everyone has answered) are fully supported.
"""


class ResponseCollector:
    def __init__(self, creds):
        from googleapiclient.discovery import build
        self._sheets = build("sheets", "v4", credentials=creds)
        self._drive = build("drive", "v3", credentials=creds)
        self._forms = build("forms", "v1", credentials=creds)

    def collect(self, sheet_id: str) -> list:
        """
        Fetch all rows from the linked Google Sheet.
        Returns a list of dicts: {submitted_at, answers: {question: value}}
        Partial responses (missing columns) are padded — no filtering.
        """
        result = (
            self._sheets.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range="A:ZZ")
            .execute()
        )
        rows = result.get("values", [])
        if not rows or len(rows) < 2:
            return []

        headers = rows[0]  # first row = question headers
        responses = []
        for row in rows[1:]:
            padded = row + [""] * (len(headers) - len(row))
            entry = {
                "submitted_at": padded[0] if padded else "",
                "answers": {headers[i]: padded[i] for i in range(1, len(headers))},
            }
            responses.append(entry)
        return responses

    def get_linked_sheet_id(self, form_id: str) -> str | None:
        """
        Find the response Sheet ID for a given Form.

        Strategy 0 (authoritative): call Forms API GET /forms/{form_id} and
          read form.linkedSheetId — Google sets this automatically when a
          Sheet is linked, regardless of how it was linked (UI or API).
          Works for ALL existing surveys including sprint 1 / sprint 2.

        Strategy 1 (fallback): search Drive for a Sheet tagged with
          appProperties.linkedFormId == form_id (written at send time by
          tools/survey/survey.py for new surveys).

        Strategy 2 (last resort): search Drive for any Sheet whose name
          contains '(Responses)', most recently modified first.
        """
        # --- strategy 0: Forms API linkedSheetId (most reliable) ---
        try:
            form = self._forms.forms().get(formId=form_id).execute()
            linked = form.get("linkedSheetId", "")
            if linked:
                return linked
        except Exception:
            pass

        # --- strategy 1: appProperties tag written at send time ---
        try:
            q = (
                f"appProperties has {{ key='linkedFormId' and value='{form_id}' }}"
                " and mimeType='application/vnd.google-apps.spreadsheet'"
                " and trashed=false"
            )
            results = self._drive.files().list(
                q=q,
                fields="files(id, name)",
                orderBy="modifiedTime desc",
            ).execute()
            files = results.get("files", [])
            if files:
                return files[0]["id"]
        except Exception:
            pass

        # --- strategy 2: name heuristic (legacy fallback) ---
        try:
            q = (
                "name contains '(Responses)'"
                " and mimeType='application/vnd.google-apps.spreadsheet'"
                " and trashed=false"
            )
            results = self._drive.files().list(
                q=q,
                fields="files(id, name)",
                orderBy="modifiedTime desc",
            ).execute()
            files = results.get("files", [])
            if files:
                return files[0]["id"]
        except Exception:
            pass

        return None

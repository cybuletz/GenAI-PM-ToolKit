"""
ResponseCollector — fetches responses from the Google Sheet linked to a Form.

Works at any time after the survey is sent, regardless of whether the app
was open. Partial responses (not everyone has answered) are fully supported.
"""
import os
import sys


class ResponseCollector:
    def __init__(self, creds):
        from googleapiclient.discovery import build
        self._sheets = build("sheets", "v4", credentials=creds)
        self._drive = build("drive", "v3", credentials=creds)

    def collect(self, sheet_id: str) -> list:
        """
        Fetch all rows from the linked Google Sheet.
        Returns a list of dicts: {respondent, submitted_at, answers: {question: value}}
        Partial responses (missing rows) are returned as-is — no filtering.
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
            # Pad short rows (partial responses)
            padded = row + [""] * (len(headers) - len(row))
            entry = {
                "submitted_at": padded[0] if padded else "",
                "answers": {headers[i]: padded[i] for i in range(1, len(headers))},
            }
            responses.append(entry)
        return responses

    def get_linked_sheet_id(self, form_id: str) -> str | None:
        """
        Given a Form ID, find the linked response Sheet in Drive.
        Google Forms automatically creates a Sheet with the same title.
        """
        q = (
            f"name contains 'Responses' "
            "and mimeType='application/vnd.google-apps.spreadsheet' "
            "and trashed=false"
        )
        results = self._drive.files().list(
            q=q, fields="files(id, name)", orderBy="modifiedTime desc"
        ).execute()
        files = results.get("files", [])
        # Return the most recently modified matching sheet
        return files[0]["id"] if files else None

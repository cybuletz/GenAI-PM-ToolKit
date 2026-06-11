"""
ResponseCollector — fetches responses directly from the Google Forms API.

Mirrors the working approach in tools/survey/collect_responses.py:
  service.forms().responses().list(formId=form_id)

No Google Sheet is required. Responses are available as soon as someone
submits the form, regardless of whether "Link to Sheets" was ever clicked.
"""


class ResponseCollector:
    def __init__(self, creds):
        from googleapiclient.discovery import build
        self._forms = build("forms", "v1", credentials=creds)

    def collect(self, form_id: str) -> list:
        """
        Fetch all responses for a form using the Forms API.

        Returns a list of dicts:
          {
            "submitted_at": <ISO timestamp str>,
            "respondent_email": <str>,
            "answers": {<question title>: <answer value>}
          }

        Works immediately — no linked Sheet required.
        """
        # Fetch raw responses
        result = (
            self._forms.forms()
            .responses()
            .list(formId=form_id)
            .execute()
        )
        raw_responses = result.get("responses", [])
        if not raw_responses:
            return []

        # Build question ID -> title map from the form definition
        question_map = self._build_question_map(form_id)

        parsed = []
        for r in raw_responses:
            answers = {}
            for qid, answer_block in r.get("answers", {}).items():
                title = question_map.get(qid, qid)
                values = answer_block.get("textAnswers", {}).get("answers", [])
                answers[title] = ", ".join(v["value"] for v in values)
            parsed.append({
                "submitted_at": r.get("lastSubmittedTime", ""),
                "respondent_email": r.get("respondentEmail", "anonymous"),
                "answers": answers,
            })
        return parsed

    def _build_question_map(self, form_id: str) -> dict:
        """Return {questionId: question title} for every question in the form."""
        try:
            form = self._forms.forms().get(formId=form_id).execute()
            question_map = {}
            for item in form.get("items", []):
                if "questionItem" in item:
                    qid = item["questionItem"]["question"]["questionId"]
                    question_map[qid] = item.get("title", qid)
            return question_map
        except Exception:
            return {}

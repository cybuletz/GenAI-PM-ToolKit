"""
MicrosoftSurveyPublisher — generates a self-contained HTML survey page,
uploads it to OneDrive Apps/PMToolkit/surveys/, and returns a shareable URL.
No Microsoft Forms API needed.
"""
import json
import uuid
from core.microsoft_graph_client import MicrosoftGraphClient

ONEDRIVE_FOLDER = "Apps/PMToolkit/surveys"


class MicrosoftSurveyPublisher:
    def __init__(self, access_token: str):
        self._token = access_token
        self._client = MicrosoftGraphClient(access_token)

    def publish(self, topic: str, questions: list[dict]) -> tuple[str, str]:
        """
        Build an HTML survey, upload to OneDrive, create an anonymous share link.
        Returns: (survey_id, public_url)
        """
        survey_id = str(uuid.uuid4())
        html = self._build_html(survey_id, topic, questions)
        filename = f"survey_{survey_id[:8]}.html"
        drive_path = f"/{ONEDRIVE_FOLDER}/{filename}"

        self._ensure_folder()
        resp = self._client.put(
            f"/me/drive/root:{drive_path}:/content",
            data=html.encode("utf-8"),
            headers={"Content-Type": "text/html"},
        )
        resp.raise_for_status()

        item_id = resp.json().get("id") or self._get_item_id(drive_path)
        share = self._client.post(
            f"/me/drive/items/{item_id}/createLink",
            json={"type": "view", "scope": "anonymous"},
        )
        url = share["link"]["webUrl"]
        return survey_id, url

    def _ensure_folder(self):
        parts = ONEDRIVE_FOLDER.split("/")
        path = ""
        for part in parts:
            path = f"{path}/{part}" if path else part
            try:
                self._client.get(f"/me/drive/root:/{path}")
            except Exception:
                parent = "/".join(path.split("/")[:-1])
                parent_ref = (
                    self._client.get(f"/me/drive/root:/{parent}")
                    if parent else self._client.get("/me/drive/root")
                )
                self._client.post(
                    f"/me/drive/items/{parent_ref['id']}/children",
                    json={"name": part, "folder": {},
                          "@microsoft.graph.conflictBehavior": "rename"},
                )

    def _get_item_id(self, drive_path: str) -> str:
        return self._client.get(f"/me/drive/root:{drive_path}")["id"]

    @staticmethod
    def _build_html(survey_id: str, topic: str, questions: list[dict]) -> str:
        q_blocks = []
        for i, q in enumerate(questions, 1):
            qtype = q.get("type", "text")
            qtext = q.get("text", "")
            qid = f"q{i}"
            if qtype == "scale":
                inputs = " ".join(
                    f'<label style="margin:0 8px"><input type="radio" name="{qid}" value="{v}" required> {v}</label>'
                    for v in range(1, 6)
                )
                field = f'<div style="margin:8px 0">{inputs}</div>'
            elif qtype == "multiple_choice":
                inputs = "".join(
                    f'<label style="display:block;margin:4px 0"><input type="radio" name="{qid}" value="{opt}" required> {opt}</label>'
                    for opt in q.get("options", [])
                )
                field = f'<div style="margin:8px 0">{inputs}</div>'
            else:
                field = f'<textarea name="{qid}" rows="3" style="width:100%;padding:6px;box-sizing:border-box" required></textarea>'
            q_blocks.append(
                f'<div style="margin-bottom:24px"><p style="font-weight:bold;margin-bottom:6px">{i}. {qtext}</p>{field}</div>'
            )

        questions_html = "\n".join(q_blocks)
        submit_url = f"https://pm-toolkit-collect.example.com/submit/{survey_id}"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{topic}</title>
<style>
  body{{font-family:Segoe UI,Arial,sans-serif;max-width:640px;margin:40px auto;padding:0 16px;color:#333}}
  h1{{font-size:1.4rem;color:#0078d4}}
  button{{background:#0078d4;color:#fff;border:none;padding:10px 28px;border-radius:4px;font-size:1rem;cursor:pointer}}
  button:hover{{background:#005a9e}}
</style>
</head>
<body>
<h1>{topic}</h1>
<form id="survey" action="{submit_url}" method="POST">
  <input type="hidden" name="survey_id" value="{survey_id}">
{questions_html}
  <button type="submit">Submit</button>
</form>
</body>
</html>"""

"""
MicrosoftMail — sends HTML survey invitation emails via Microsoft Graph /me/sendMail.
Mirrors the Google Gmail send approach used by tools/survey/survey.py.
"""
from core.microsoft_graph_client import MicrosoftGraphClient


class MicrosoftMail:
    def __init__(self, access_token: str):
        self._client = MicrosoftGraphClient(access_token)

    def send_survey_invitations(
        self,
        recipients: list[str],
        topic: str,
        survey_url: str,
        deadline: str,
    ) -> int:
        """Send one invitation per recipient. Returns number sent successfully."""
        subject = f"Survey Request: {topic}"
        body_html = self._build_body(topic, survey_url, deadline)
        sent = 0
        for email in recipients:
            message = {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": [{"emailAddress": {"address": email}}],
            }
            self._client.post("/me/sendMail", json={"message": message})
            sent += 1
        return sent

    @staticmethod
    def _build_body(topic: str, url: str, deadline: str) -> str:
        return f"""
<html><body>
<p>Hi,</p>
<p>You are invited to complete a brief survey: <strong>{topic}</strong>.</p>
<p>Please respond by <strong>{deadline}</strong>.</p>
<p><a href="{url}" style="
    background:#0078d4;color:#fff;padding:10px 20px;
    border-radius:4px;text-decoration:none;font-weight:bold;">
  Open Survey
</a></p>
<p style="color:#666;font-size:12px;">
  If the button does not work, copy and paste this link:<br>{url}
</p>
</body></html>
"""

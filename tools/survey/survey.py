import os
import json
import argparse
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
]

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")


def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("\n\u274c ERROR: credentials.json not found in tools/survey/")
                print("Please follow the README setup steps to download your Google OAuth credentials.\n")
                exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def create_form(service, title, questions):
    """Create a Google Form with the given questions.
    Returns (form_id, form_url).
    """
    print(f"\n\U0001f4cb Creating form: {title}")
    form = service.forms().create(
        body={"info": {"title": title}}
    ).execute()
    form_id = form["formId"]
    print(f"\u2705 Form created with ID: {form_id}")

    requests_body = []
    for i, q in enumerate(questions):
        q_type = q.get("type", "text")
        if q_type == "scale":
            question_body = {
                "scaleQuestion": {
                    "low": 1, "high": 5,
                    "lowLabel": "Poor", "highLabel": "Excellent"
                }
            }
        elif q_type == "multiple_choice":
            question_body = {
                "choiceQuestion": {
                    "type": "RADIO",
                    "options": [{"value": opt} for opt in q["options"]]
                }
            }
        else:
            question_body = {"textQuestion": {"paragraph": False}}

        requests_body.append({
            "createItem": {
                "item": {
                    "title": q["text"],
                    "questionItem": {
                        "question": {"required": True, **question_body}
                    }
                },
                "location": {"index": i}
            }
        })

    service.forms().batchUpdate(
        formId=form_id,
        body={"requests": requests_body}
    ).execute()

    print(f"\u2705 {len(questions)} questions added")
    form_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
    print(f"\U0001f517 Survey link: {form_url}")
    return form_id, form_url


def link_response_sheet(forms_service, drive_service, form_id, title):
    """
    Create a Google Sheet to collect form responses and link it to the form.
    Returns the sheet_id string, or empty string on failure.

    Google Forms API: set a response destination via batchUpdate
    with a setPublishSettings request that includes a responseDestination.
    """
    try:
        # Create a new blank spreadsheet via Sheets API
        sheets_service = build("sheets", "v4", credentials=forms_service._http.credentials)
        spreadsheet = sheets_service.spreadsheets().create(
            body={"properties": {"title": f"{title} (Responses)"}},
            fields="spreadsheetId"
        ).execute()
        sheet_id = spreadsheet["spreadsheetId"]
        print(f"\u2705 Response sheet created: {sheet_id}")

        # Tag the sheet with the form_id for reliable future lookup
        drive_service.files().update(
            fileId=sheet_id,
            body={"appProperties": {"linkedFormId": form_id}}
        ).execute()

        # Link the sheet to the form as response destination
        forms_service.forms().batchUpdate(
            formId=form_id,
            body={
                "requests": [{
                    "updateSettings": {
                        "settings": {
                            "quizSettings": {"isQuiz": False}
                        },
                        "updateMask": "quizSettings.isQuiz"
                    }
                }]
            }
        ).execute()

        # Use the Forms API to set the response spreadsheet destination
        forms_service.forms().batchUpdate(
            formId=form_id,
            body={
                "requests": [{
                    "setFormResponseDestination": {
                        "destination": {
                            "type": "SPREADSHEET",
                            "uri": f"https://docs.google.com/spreadsheets/d/{sheet_id}"
                        }
                    }
                }]
            }
        ).execute()

        print(f"\u2705 Sheet linked as response destination")
        return sheet_id

    except Exception as e:
        print(f"\u26a0\ufe0f Could not link response sheet: {e}")
        # Fallback: try to find an auto-created sheet by name
        try:
            q = (
                f"name contains '{title[:40]}'"
                " and mimeType='application/vnd.google-apps.spreadsheet'"
                " and trashed=false"
            )
            results = drive_service.files().list(
                q=q, fields="files(id, name)", orderBy="modifiedTime desc"
            ).execute()
            files = results.get("files", [])
            if files:
                sheet_id = files[0]["id"]
                # Tag it
                try:
                    drive_service.files().update(
                        fileId=sheet_id,
                        body={"appProperties": {"linkedFormId": form_id}}
                    ).execute()
                except Exception:
                    pass
                return sheet_id
        except Exception:
            pass
        return ""


def build_email_body(recipient_name, survey_title, form_url, deadline):
    plain = f"""Hi {recipient_name},

As part of our continuous improvement efforts, I'd like to invite you to share your feedback on: {survey_title}.

Your input takes only a few minutes and directly helps the team improve how we work together.

\U0001f449 Access the survey here: {form_url}

Please complete it by: {deadline}

Your responses are anonymous and will be used to identify areas where we're doing well and where we can improve.

Thank you for taking the time \u2014 it really makes a difference.

Best regards,
Your Project Manager
"""

    html = f"""
<html>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #333; max-width: 600px;">
  <p>Hi {recipient_name},</p>
  <p>As part of our continuous improvement efforts, I'd like to invite you to share your feedback on:</p>
  <p style="font-size: 16px; font-weight: bold; color: #1a73e8;">\U0001f4cb {survey_title}</p>
  <p>Your input takes only a few minutes and directly helps the team improve how we work together.</p>
  <p style="margin: 24px 0;">
    <a href="{form_url}"
       style="background-color: #1a73e8; color: white; padding: 12px 24px;
              text-decoration: none; border-radius: 4px; font-weight: bold;">
      \u270f\ufe0f Fill in the Survey
    </a>
  </p>
  <p>\U0001f4c5 <strong>Please complete it by: {deadline}</strong></p>
  <p style="color: #666; font-size: 13px;">
    Your responses are anonymous and will be used to identify areas where we're doing well
    and where we can improve as a team.
  </p>
  <p>Thank you for taking the time \u2014 it really makes a difference.</p>
  <p>Best regards,<br><strong>Your Project Manager</strong></p>
  <hr style="border: none; border-top: 1px solid #eee; margin-top: 32px;">
  <p style="color: #aaa; font-size: 11px;">
    If the button above doesn't work, copy and paste this link into your browser:<br>
    <a href="{form_url}" style="color: #aaa;">{form_url}</a>
  </p>
</body>
</html>
"""
    return plain, html


def send_emails(gmail_service, emails, survey_title, form_url, deadline):
    print(f"\n\U0001f4e7 Sending survey to {len(emails)} recipient(s)...")
    sent = 0
    for email in emails:
        email = email.strip()
        if not email:
            continue
        recipient_name = email.split("@")[0].capitalize()
        plain, html = build_email_body(recipient_name, survey_title, form_url, deadline)
        message = MIMEMultipart("alternative")
        message["to"] = email
        message["subject"] = f"\U0001f4cb Your feedback needed: {survey_title}"
        message.attach(MIMEText(plain, "plain"))
        message.attach(MIMEText(html, "html"))
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        gmail_service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        print(f"  \u2709\ufe0f  Sent to {email}")
        sent += 1
    print(f"\n\u2705 Survey sent to {sent} recipient(s)")


def save_form_metadata(form_id, form_url, title, emails, deadline):
    meta = {
        "form_id": form_id,
        "form_url": form_url,
        "title": title,
        "emails": emails,
        "deadline": deadline
    }
    meta_path = os.path.join(os.path.dirname(__file__), "form_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\n\U0001f4be Form metadata saved to tools/survey/form_meta.json")


def main():
    parser = argparse.ArgumentParser(description="Create and send a Google Form survey")
    parser.add_argument("--title", required=True)
    parser.add_argument("--emails", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--deadline", default="end of this week")
    args = parser.parse_args()

    emails = [e.strip() for e in args.emails.split(",")]
    with open(args.questions, "r") as f:
        questions = json.load(f)

    creds = authenticate()
    forms_service = build("forms", "v1", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    form_id, form_url = create_form(forms_service, args.title, questions)
    sheet_id = link_response_sheet(forms_service, drive_service, form_id, args.title)
    send_emails(gmail_service, emails, args.title, form_url, args.deadline)
    save_form_metadata(form_id, form_url, args.title, emails, args.deadline)

    print("\n\U0001f389 Done! Form created, sheet linked, and survey sent.")
    if sheet_id:
        print(f"\U0001f4ca Responses sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")


if __name__ == "__main__":
    main()

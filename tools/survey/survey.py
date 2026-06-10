import os
import json
import argparse
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
]

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")


def authenticate():
    """Handles OAuth login. Opens browser on first run, uses saved token after that."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("\n❌ ERROR: credentials.json not found in tools/survey/")
                print("Please follow the README setup steps to download your Google OAuth credentials.\n")
                exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def create_form(service, title, questions):
    """Creates a Google Form with the given title and questions."""
    print(f"\n📋 Creating form: {title}")

    # Step 1: Create empty form
    form = service.forms().create(
        body={"info": {"title": title}}
    ).execute()

    form_id = form["formId"]
    print(f"✅ Form created with ID: {form_id}")

    # Step 2: Build batch requests for each question
    requests = []
    for i, q in enumerate(questions):
        q_type = q.get("type", "text")

        if q_type == "scale":
            question_body = {
                "scaleQuestion": {
                    "low": 1,
                    "high": 5,
                    "lowLabel": "Poor",
                    "highLabel": "Excellent"
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

        requests.append({
            "createItem": {
                "item": {
                    "title": q["text"],
                    "questionItem": {
                        "question": {
                            "required": True,
                            **question_body
                        }
                    }
                },
                "location": {"index": i}
            }
        })

    service.forms().batchUpdate(
        formId=form_id,
        body={"requests": requests}
    ).execute()

    print(f"✅ {len(questions)} questions added to the form")
    form_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
    print(f"🔗 Survey link: {form_url}")
    return form_id, form_url


def send_emails(gmail_service, emails, survey_title, form_url):
    """Sends the survey link to each team member via Gmail."""
    print(f"\n📧 Sending survey to {len(emails)} recipients...")

    subject = f"📋 Survey Request: {survey_title}"
    body = f"""Hi,

You have been invited to complete a short survey: {survey_title}

Please take a few minutes to share your feedback using the link below:
{form_url}

Your input is important and will help us improve.

Thank you!
"""

    sent = 0
    for email in emails:
        email = email.strip()
        if not email:
            continue

        message = MIMEText(body)
        message["to"] = email
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        gmail_service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        print(f"  ✉️  Sent to {email}")
        sent += 1

    print(f"\n✅ Survey sent to {sent} recipient(s)")


def save_form_metadata(form_id, form_url, title, emails):
    """Saves form metadata locally for use by collect_responses.py."""
    meta = {
        "form_id": form_id,
        "form_url": form_url,
        "title": title,
        "emails": emails
    }
    meta_path = os.path.join(os.path.dirname(__file__), "form_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\n💾 Form metadata saved to tools/survey/form_meta.json")


def main():
    parser = argparse.ArgumentParser(description="Create and send a Google Form survey")
    parser.add_argument("--title", required=True, help="Survey title")
    parser.add_argument("--emails", required=True, help="Comma-separated list of recipient emails")
    parser.add_argument("--questions", required=True, help="Path to questions JSON file")
    args = parser.parse_args()

    emails = [e.strip() for e in args.emails.split(",")]

    with open(args.questions, "r") as f:
        questions = json.load(f)

    creds = authenticate()
    forms_service = build("forms", "v1", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)

    form_id, form_url = create_form(forms_service, args.title, questions)
    send_emails(gmail_service, emails, args.title, form_url)
    save_form_metadata(form_id, form_url, args.title, emails)

    print("\n🎉 Done! Form created and survey sent successfully.")
    print(f"➡️  To collect responses later, run:")
    print(f"   python tools/survey/collect_responses.py --form-id {form_id}")


if __name__ == "__main__":
    main()

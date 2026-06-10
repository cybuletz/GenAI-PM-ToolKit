import os
import json
import argparse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/forms.responses.readonly",
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
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def collect(form_id):
    creds = authenticate()
    service = build("forms", "v1", credentials=creds)

    print(f"\n🔍 Fetching responses for form: {form_id}")
    result = service.forms().responses().list(formId=form_id).execute()
    responses = result.get("responses", [])

    if not responses:
        print("⚠️  No responses found yet. Try again later.")
        return

    print(f"✅ {len(responses)} response(s) found")

    # Also load question titles from the form for readable output
    form = service.forms().get(formId=form_id).execute()
    question_map = {}
    for item in form.get("items", []):
        if "questionItem" in item:
            qid = item["questionItem"]["question"]["questionId"]
            question_map[qid] = item["title"]

    readable = []
    for r in responses:
        entry = {"respondent_email": r.get("respondentEmail", "anonymous"), "answers": {}}
        for qid, answer in r.get("answers", {}).items():
            question_title = question_map.get(qid, qid)
            values = answer.get("textAnswers", {}).get("answers", [])
            entry["answers"][question_title] = [v["value"] for v in values]
        readable.append(entry)

    out_path = os.path.join(os.path.dirname(__file__), "responses.json")
    with open(out_path, "w") as f:
        json.dump(readable, f, indent=2)

    print(f"💾 Responses saved to tools/survey/responses.json")
    print(f"\n➡️  Now ask the Survey Agent in Copilot Chat to analyze the responses.")


def main():
    parser = argparse.ArgumentParser(description="Collect Google Form responses")
    parser.add_argument("--form-id", help="Google Form ID")
    args = parser.parse_args()

    form_id = args.form_id
    if not form_id:
        meta_path = os.path.join(os.path.dirname(__file__), "form_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            form_id = meta["form_id"]
            print(f"ℹ️  Using form ID from form_meta.json: {form_id}")
        else:
            print("❌ No --form-id provided and no form_meta.json found.")
            exit(1)

    collect(form_id)


if __name__ == "__main__":
    main()

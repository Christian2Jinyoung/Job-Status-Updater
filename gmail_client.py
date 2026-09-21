import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, TOKEN_FILE, GMAIL_SCOPES


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def list_recent_messages(service, max_results=10, query=""):
    results = service.users().messages().list(
        userId="me", maxResults=max_results, q=query
    ).execute()
    return results.get("messages", [])


def get_message(service, message_id):
    return service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()


if __name__ == "__main__":
    service = get_gmail_service()
    messages = list_recent_messages(service, max_results=5, query="category:primary")

    print(f"Found {len(messages)} messages.\n")

    for msg_meta in messages:
        msg = get_message(service, msg_meta["id"])
        headers = msg["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(unknown sender)")
        print(f"From: {sender}\nSubject: {subject}\n")

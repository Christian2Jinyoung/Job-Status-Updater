from typing import Literal

import anthropic
from pydantic import BaseModel

from config import ANTHROPIC_MODEL

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You extract job-application status updates from emails for a personal tracker.
Use only what the email actually says - never invent a company, role, or date you can't find.
If a field can't be determined from the email, use "Unknown".
If the email body has no date, use the provided received date.
Format the date as MM/DD/YYYY (e.g. 10/01/2026).
Keep notes to one short sentence."""


class JobUpdate(BaseModel):
    status: Literal["Applied", "Assessment", "Interview", "Offer", "Rejected", "Other"]
    company: str
    position: str
    location: str
    job_type: str
    date: str
    notes: str


def extract_job_update(subject: str, sender: str, body: str, received_date: str) -> dict:
    """Extract structured job-application fields from an email. Returns a dict keyed by config.COLUMNS."""
    response = client.messages.parse(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Subject: {subject}\n"
                f"From: {sender}\n"
                f"Received: {received_date}\n\n"
                f"{body}"
            ),
        }],
        output_format=JobUpdate,
    )
    update = response.parsed_output
    return {
        # A tracker row already implies "Applied", so confirmations carry no status to record.
        "Status": None if update.status == "Applied" else update.status,
        "Company": update.company,
        "Position": update.position,
        "Location": update.location,
        "Type": update.job_type,
        "Date": update.date,
        "Notes": update.notes,
    }


if __name__ == "__main__":
    from gmail_client import get_gmail_service, list_recent_messages, get_message
    from prefilter import build_search_query, is_candidate_message

    service = get_gmail_service()
    query = build_search_query()
    messages = list_recent_messages(service, max_results=5, query=query)

    for msg_meta in messages:
        msg = get_message(service, msg_meta["id"])
        headers = msg["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        received_date = next((h["value"] for h in headers if h["name"] == "Date"), "")
        snippet = msg.get("snippet", "")

        if not is_candidate_message(subject, sender, snippet):
            continue

        print(extract_job_update(subject, sender, snippet, received_date))

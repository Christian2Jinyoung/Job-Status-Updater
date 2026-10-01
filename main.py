import argparse
import base64
import os
from datetime import date, timedelta
from email.utils import parsedate_to_datetime

from gmail_client import get_gmail_service, list_recent_messages, get_message
from prefilter import build_search_query, is_candidate_message
from extractor import extract_job_update
from tracker import update_entry, append_unmatched
from config import LAST_SCAN_FILE, DEFAULT_LOOKBACK_DAYS, UNMATCHED_FILE


def get_email_body(message: dict) -> str:
    """Return the plain-text body of a Gmail message, falling back to its snippet."""
    payload = message["payload"]
    parts = payload.get("parts", [payload])

    for part in parts:
        if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return message.get("snippet", "")


def format_received_timestamp(received_date: str, fallback: str) -> str:
    """Format the email's Date header as local 'MM/DD/YYYY hh:mm AM/PM' for note prefixes."""
    try:
        received = parsedate_to_datetime(received_date).astimezone()
    except (TypeError, ValueError):
        return fallback
    return received.strftime("%m/%d/%Y %I:%M %p")


def read_last_scan_date() -> str | None:
    if os.path.exists(LAST_SCAN_FILE):
        with open(LAST_SCAN_FILE) as f:
            return f.read().strip()
    return None


def write_last_scan_date(date_str: str) -> None:
    with open(LAST_SCAN_FILE, "w") as f:
        f.write(date_str)


def run(max_results: int = 20, since: str | None = None) -> None:
    """Fetch candidate job emails since the given date, update matching tracker rows, and log the rest to the unmatched file."""
    after_date = since or read_last_scan_date()
    if not after_date:
        after_date = (date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS)).strftime("%Y/%m/%d")

    service = get_gmail_service()
    query = build_search_query(after_date=after_date)
    messages = list_recent_messages(service, max_results=max_results, query=query)

    print(f"Scanning from {after_date}. Fetched {len(messages)} messages matching: {query}\n")

    updated = 0
    unmatched = 0
    skipped = 0
    for msg_meta in messages:
        msg = get_message(service, msg_meta["id"])
        headers = msg["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        received_date = next((h["value"] for h in headers if h["name"] == "Date"), "")
        snippet = msg.get("snippet", "")

        if not is_candidate_message(subject, sender, snippet):
            continue

        body = get_email_body(msg)
        update = extract_job_update(subject, sender, body, received_date)

        result = update_entry(
            status=update["Status"],
            company=update["Company"],
            position=update["Position"],
            location=update["Location"],
            job_type=update["Type"],
            email_timestamp=format_received_timestamp(received_date, fallback=update["Date"]),
            notes=update["Notes"],
        )
        label = f"{update['Company']} — {update['Position']}"
        if result == "updated":
            updated += 1
            print(f"✅ {label} — {update['Status'] or 'status unchanged'}")
        elif result == "duplicate":
            skipped += 1
            print(f"⏭️ {label} — note for this email already exists, skipped")
        elif append_unmatched(update, subject, sender, received_date):
            unmatched += 1
            print(f"❓ {label} — no tracker match, logged to unmatched file")
        else:
            skipped += 1
            print(f"⏭️ {label} — already in unmatched file, skipped")

    print(
        f"\nDone. Updated {updated} tracker entries; skipped {skipped} duplicates; "
        f"{unmatched} unmatched emails logged to {UNMATCHED_FILE}."
    )
    write_last_scan_date(date.today().strftime("%Y/%m/%d"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", help="Scan emails after this date (YYYY/MM/DD). Overrides the saved last-scan date.")
    parser.add_argument("--max-results", type=int, default=20)
    args = parser.parse_args()

    run(max_results=args.max_results, since=args.since)

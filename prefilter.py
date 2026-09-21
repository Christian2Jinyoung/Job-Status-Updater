KNOWN_ATS_DOMAINS = [
    "greenhouse.io",
    "lever.co",
    "myworkday.com",
    "icims.com",
    "smartrecruiters.com",
    "jobvite.com",
    "taleo.net",
    "successfactors.com",
    "ashbyhq.com",
    "workable.com",
    "bamboohr.com",
    "breezy.hr",
    "linkedin.com",
]

KEYWORDS = [
    "application",
    "applied",
    "interview",
    "assessment",
    "offer",
    "unfortunately",
    "moving forward",
    "regret to inform",
    "next steps",
    "thank you for applying",
    "candidacy",
    "position",
]


def build_search_query():
    keyword_clause = " OR ".join(f'"{kw}"' for kw in KEYWORDS)
    return f"category:primary ({keyword_clause})"


def get_sender_domain(sender_header):
    if "@" not in sender_header:
        return ""
    domain = sender_header.split("@")[-1]
    domain = domain.strip().strip(">").lower()
    return domain


def is_candidate_message(subject, sender, snippet):
    domain = get_sender_domain(sender)
    if any(ats_domain in domain for ats_domain in KNOWN_ATS_DOMAINS):
        return True

    text = f"{subject} {snippet}".lower()
    return any(keyword.lower() in text for keyword in KEYWORDS)

# sanity check
if __name__ == "__main__":
    from gmail_client import get_gmail_service, list_recent_messages, get_message

    service = get_gmail_service()
    query = build_search_query()
    print(f"Query: {query}\n")

    messages = list_recent_messages(service, max_results=15, query=query)
    print(f"Fetched {len(messages)} messages from Gmail search.\n")

    for msg_meta in messages:
        msg = get_message(service, msg_meta["id"])
        headers = msg["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        snippet = msg.get("snippet", "")

        candidate = is_candidate_message(subject, sender, snippet)
        flag = "✅" if candidate else "❌"
        print(f"{flag} From: {sender}\n   Subject: {subject}\n")

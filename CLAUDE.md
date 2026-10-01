# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal job-application tracker. It pulls Gmail messages, filters them down to job-application-related emails, and (intended) extracts structured status updates into an Excel tracker using the Claude API.

`main.py` runs the full pipeline: Gmail fetch → prefilter → Claude extraction → Excel update. Run `venv/Scripts/python main.py [--since YYYY/MM/DD] [--max-results N]`.

## Setup & running

```bash
# from project root, with venv/ already created
venv/Scripts/pip install -r requirements.txt   # Windows
venv/Scripts/python gmail_client.py            # sanity-check Gmail auth + list recent messages
venv/Scripts/python prefilter.py               # sanity-check the search query + candidate filter against live Gmail
```

There is no test suite, linter, or build step configured yet.

Gmail OAuth: `credentials.json` (OAuth client) and `token.json` (cached user token, auto-created/refreshed on first run) live in the project root and are gitignored. `gmail_client.get_gmail_service()` handles the auth flow, including refresh.

## Architecture

- **config.py** — single source of truth for file paths (`credentials.json`, `token.json`, `job_tracker.xlsx`), Gmail API scopes, the Excel tracker's sheet name/columns, and the Anthropic model id. Other modules import constants from here rather than hardcoding paths/scopes.
- **gmail_client.py** — thin Gmail API wrapper: `get_gmail_service()` (auth), `list_recent_messages()`, `get_message()`. This is the only module that talks to the Gmail API directly.
- **prefilter.py** — decides which Gmail messages are worth sending to the (future) Claude extraction step, without an LLM call. `build_search_query()` builds the Gmail search query (`category:primary` + keyword OR-clause) used to narrow the initial fetch; `is_candidate_message()` is a second, cheaper pass over subject/sender/snippet that flags a message as job-related if it's from a known ATS domain (`KNOWN_ATS_DOMAINS`) or contains one of `KEYWORDS`. Keep both lists in sync when tuning recall/precision — the search query and the local filter are meant to agree on what counts as "job-related."
- **extractor.py** — calls Claude (via `client.messages.parse()` against the `JobUpdate` Pydantic schema) to turn a filtered email into structured fields. `extract_job_update()` takes subject/sender/body/received-date and returns a dict keyed exactly to `config.COLUMNS`, ready for the Excel writer. Grounds "Date" on the email's `Date` header when the body doesn't state one, and asks for `"Unknown"` rather than a guess when a field can't be determined — keep prompt edits consistent with that no-invention rule.
- **tracker.py** — the only module that writes Excel: `update_entry()` updates a matching row in `Job_List.xlsx`; `append_unmatched()` logs non-matching emails to `Unmatched_Emails.xlsx`.
- **main.py** — entry point wiring auth → fetch → prefilter → extract → tracker update. Scans from `--since`, else the date saved in `last_scan.txt`, else 30 days back.

The Excel output schema (`config.COLUMNS`: Status, Company, Position, Location, Type, Date Applied, Notes) is the contract the extraction step must fill — any new field needs to be added there first.

## Tracker rules (user preferences)

- **Dates are MM/DD/YYYY** (e.g. `10/01/2026`) everywhere — the tracker, notes, and the extractor's output.
- **Date Applied is never overwritten** by the pipeline; it's the user's own record of when they applied.
- **Status updates go in Notes, timestamped**: the email's received time (from its `Date` header, local time) is prefixed to the note, e.g. `10/01/2026 02:35 PM Candidate was not selected...`. New notes are added on top of existing ones (newest first, one per line), never replacing them.
- **Re-runs don't duplicate**: if a row's notes already have a line starting with the email's timestamp, that email is treated as already processed and the row is left alone. The timestamp comes from the header, not Claude, so it's identical across runs. Unmatched emails are deduped by Sender + Received header.
- **No "Unknown" in Location/Type**: if the extractor returns `"Unknown"` for either, the cell is left as-is (blank stays blank, existing values aren't overwritten).
- **No "Applied" status**: a row existing already means "applied", so confirmation emails leave Status unchanged.
- **No new rows**: emails that don't match an existing Company+Position go to `Unmatched_Emails.xlsx` instead.
- **Loose company matching**: company names are compared ignoring case, punctuation, and trailing suffixes (Inc, Corp, Corporation, Company, LLC, ...), and one name may be the other plus extra trailing words (`Allstate` ↔ `Allstate Insurance Company`). A loose match is used only if exactly one row qualifies; an exact match always wins. Position must still match exactly (case-insensitive).

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal job-application tracker. It pulls Gmail messages, filters them down to job-application-related emails, and (intended) extracts structured status updates into an Excel tracker using the Claude API.

Early-stage: `main.py` and `extractor.py` are currently empty stubs — the pipeline they're meant to wire together (Gmail fetch → prefilter → Claude extraction → Excel write) is not yet assembled end-to-end.

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
- **extractor.py** (stub) — intended to hold the Claude API call that turns a filtered email into structured fields (status, company, position, etc.) matching `config.COLUMNS`.
- **main.py** (stub) — intended entry point wiring auth → fetch → prefilter → extract → Excel write together.

The Excel output schema (`config.COLUMNS`: Status, Company, Position, Location, Type, Date, Notes) is the contract the extraction step must fill — any new field needs to be added there first.

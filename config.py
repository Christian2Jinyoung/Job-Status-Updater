import os

# Base directory of project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Gmail API
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Excel tracker
TRACKER_FILE = os.path.join(BASE_DIR, "job_tracker.xlsx")
SHEET_NAME = "Applications"
COLUMNS = ["Status", "Company", "Position", "Location", "Type", "Date", "Notes"]

# Claude API
ANTHROPIC_MODEL = "claude-sonnet-5"
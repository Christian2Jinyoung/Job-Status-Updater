import os

# Base directory of project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Gmail API
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Excel tracker
TRACKER_FILE = os.path.join(BASE_DIR, "Job_List.xlsx")
SHEET_NAME = "Sheet1"
COLUMNS = ["Status", "Company", "Position", "Location", "Type", "Date Applied", "Notes"]

# Emails whose extracted Company+Position don't match a tracker row
UNMATCHED_FILE = os.path.join(BASE_DIR, "Unmatched_Emails.xlsx")
UNMATCHED_COLUMNS = COLUMNS + ["Subject", "Sender", "Received"]

# Claude API
ANTHROPIC_MODEL = "claude-sonnet-5"

# Scan state
LAST_SCAN_FILE = os.path.join(BASE_DIR, "last_scan.txt")
DEFAULT_LOOKBACK_DAYS = 30
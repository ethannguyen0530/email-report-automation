import os
from dotenv import load_dotenv

load_dotenv()

# Gmail API
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")

# AI Extraction
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() == "true"

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#project-updates")

# Email (SMTP)
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
REPORT_RECIPIENTS = [r.strip() for r in os.getenv("REPORT_RECIPIENTS", "").split(",") if r.strip()]

# Database
DB_PATH = os.getenv("DB_PATH", "projects.db")

# Gmail Query
GMAIL_QUERY = os.getenv("GMAIL_QUERY", "label:project-updates OR subject:project OR subject:update")
GMAIL_MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "10"))

# Scheduling — set SCAN_INTERVAL_MINUTES=0 to disable auto-scan
# SCAN_INTERVAL_MINUTES: how often to check Gmail for new emails (default 15 min)
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES",
    str(int(os.getenv("SCAN_INTERVAL_HOURS", "0")) * 60 or 15)))
# REPORT_SEND_TIME: fixed daily time to send the executive report (24h format, default 09:00)
# Set to empty string to disable auto-report
_send_time = os.getenv("REPORT_SEND_TIME", "09:00").strip()
REPORT_SEND_TIME = _send_time
if _send_time:
    try:
        _parts = _send_time.split(":")
        if len(_parts) < 2:
            raise ValueError("expected HH:MM format")
        REPORT_SEND_HOUR = int(_parts[0])
        REPORT_SEND_MINUTE = int(_parts[1])
        if not (0 <= REPORT_SEND_HOUR <= 23 and 0 <= REPORT_SEND_MINUTE <= 59):
            raise ValueError(f"hour must be 0-23, minute must be 0-59")
    except (ValueError, IndexError):
        import sys
        print(f"WARNING: Invalid REPORT_SEND_TIME '{_send_time}' — expected HH:MM (e.g. 09:00). Auto-report disabled.", file=sys.stderr)
        REPORT_SEND_TIME = ""
        REPORT_SEND_HOUR = None
        REPORT_SEND_MINUTE = None
else:
    REPORT_SEND_HOUR = None
    REPORT_SEND_MINUTE = None

# Flask
FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))

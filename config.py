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
REPORT_SEND_HOUR = int(_send_time.split(":")[0]) if _send_time else None
REPORT_SEND_MINUTE = int(_send_time.split(":")[1]) if _send_time else None

# Flask
FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))

# Email Report Automation

Scans Gmail from program managers and delivery leads, extracts project details via AI, consolidates into a live executive dashboard and sends reports via email + Slack.

**Dashboard:** `http://localhost:5001` (after setup)
**Repo:** `github.com/ethannguyen0530/email-report-automation`

---

## What It Does

- **Gmail scanning** — OAuth2, fetches emails matching your search criteria
- **AI extraction** — GPT pulls customer, project, status, progress %, milestone, blocker, owner from each email
- **React dashboard** — Metric cards (click to filter), inline status editing, red-flag alerts for stale projects, email inbox, file uploads
- **Executive report** — Professional HTML report with accomplishments, blockers, full project table — send to email + Slack in one click
- **Always-on** — Runs as a macOS background service, auto-starts on login, no terminal needed

---

## Setup (First Time)

### 1. Clone and install

```bash
git clone https://github.com/ethannguyen0530/email-report-automation
cd email-report-automation
pip3 install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your credentials
```

| Variable | How to get it |
|---|---|
| `OPENAI_API_KEY` | platform.openai.com → API keys |
| `SLACK_BOT_TOKEN` | api.slack.com → Your Apps → Bot Token (xoxb-...) |
| `SLACK_CHANNEL` | e.g. `#project-updates` |
| `SENDER_EMAIL` | Gmail address that sends reports |
| `SENDER_PASSWORD` | Gmail App Password (not your login password) |
| `REPORT_RECIPIENTS` | Comma-separated, e.g. `boss@company.com,you@company.com` |
| `GMAIL_QUERY` | Search filter, e.g. `from:@company.com subject:update` |

**Gmail OAuth credentials (`credentials.json`):**
1. Google Cloud Console → APIs & Services → Enable Gmail API
2. Create OAuth2 credentials (Desktop app) → Download → save as `credentials.json` in project root
3. Set `USE_MOCK_DATA=False` in `.env`
4. First run opens a browser to authorize — after that, token is saved automatically

**Gmail App Password (for SMTP sending):**
1. myaccount.google.com → Security → 2-Step Verification → App Passwords
2. Generate for "Mail" → paste as `SENDER_PASSWORD`

### 3. Install as a permanent background service

```bash
bash install_service.sh
```

Builds the frontend, installs gunicorn, and registers a launchd service that starts automatically on every login and restarts on crash. No terminal needed.

Open **http://localhost:5001** — dashboard is live.

---

## Daily Use

Visit **http://localhost:5001**. Everything runs automatically.

**Scan emails manually:**
```bash
python3 main.py   # select option 2
```

**Enable automatic scanning** — set in `.env`:
```
SCAN_INTERVAL_HOURS=6
```

**After any `.env` or code change, restart the service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist && \
launchctl load ~/Library/LaunchAgents/com.emailreport.plist
```

**View logs:**
```bash
tail -f ~/email-report-automation/logs/server.log
```

---

## Dashboard Pages

| Page | What it shows |
|---|---|
| Overview | Metric cards (click to filter by status), all projects with last-updated timestamps, red flags for stale projects, accomplishments, blockers |
| Emails | Inbox view of all scanned emails with received and processed timestamps |
| Report | Live executive report preview + Send via Email + Slack button |
| Files | Drag-and-drop file upload |

---

## Architecture

```
Gmail API → GmailService (OAuth2)
                ↓
        ExtractionService (GPT-3.5)
                ↓
          SQLite Database
                ↓
    Flask REST API (port 5001)          ← APScheduler (auto email scan)
    React Frontend (served by Flask)
                ↓
    ReportService → SMTP Email + Slack
```

### Key Files

```
email-report-automation/
├── main.py                     CLI — manual scan, report, seed
├── config.py                   Loads all .env variables
├── start.sh                    Dev mode (Flask dev + Vite HMR)
├── run.sh                      Production (gunicorn)
├── install_service.sh          macOS launchd installer
├── REPO_COVERAGE_AND_QUESTIONS.md  Full feature inventory + open questions
│
├── database/schema.py          All SQL queries and DB management
├── services/
│   ├── gmail_service.py        OAuth2 + recursive multipart body extraction
│   ├── extraction_service.py   GPT extraction with regex fallback
│   ├── report_service.py       HTML report + SMTP delivery
│   └── slack_service.py        Slack Block Kit formatting + delivery
├── dashboard/app.py            Flask API, scheduler, React static serving
│
└── frontend/src/
    ├── pages/Dashboard.jsx     Overview — filters, red flags, inline edit
    ├── pages/Emails.jsx        Inbox with timestamps
    ├── pages/Report.jsx        Report preview + send button
    ├── pages/Uploads.jsx       Drag-and-drop upload
    └── components/
        ├── MetricCard.jsx      Clickable stat card with filter state
        ├── StatusSelect.jsx    Inline status dropdown (PATCH to API)
        └── StatusBadge.jsx     Color-coded status pill
```

---

## Development Mode

For hot-reload while editing frontend code:

```bash
bash start.sh
# Flask on :5001, Vite on :3000 — use http://localhost:3000
```

---

## Pre-Production Checklist

See `REPO_COVERAGE_AND_QUESTIONS.md` for the full gap analysis, critical questions, and success criteria before going live.

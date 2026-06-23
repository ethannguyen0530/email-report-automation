# Email Report Automation

Scans Gmail from program managers and delivery leads, extracts project details via AI, and consolidates everything into a live executive dashboard with one-click report delivery via email and Slack.

**Dashboard:** `http://localhost:5001`
**Repo:** `github.com/ethannguyen0530/email-report-automation`

---

## What It Does

- **Gmail scanning** — OAuth2, reads emails matching a configurable search query
- **AI extraction** — GPT-3.5 extracts customer, project, status, progress %, milestone, blocker, and owner from each email; regex fallback if GPT fails
- **React dashboard** — clickable metric cards that filter the projects table, inline status editing, red-flag alerts (⚑) for projects not updated in 7+ days, email inbox with timestamps, drag-and-drop file upload
- **Executive report** — professional HTML report (gradient header, color-coded status pills, progress bars) with one-click delivery to email + Slack
- **Always-on service** — runs as a macOS background service via launchd; auto-starts on login, restarts on crash, no terminal needed; auto-scans Gmail every N hours if configured

---

## First-Time Setup

### 1. Install Python dependencies

```bash
cd email-report-automation
pip3 install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env and fill in your credentials (see table below)
```

| Variable | What it is | How to get it |
|---|---|---|
| `OPENAI_API_KEY` | AI extraction | platform.openai.com → API Keys |
| `SLACK_BOT_TOKEN` | Slack delivery | api.slack.com → Your Apps → Bot Token (starts with `xoxb-`) |
| `SLACK_CHANNEL` | Slack channel | e.g. `#project-updates` |
| `SENDER_EMAIL` | Gmail that sends reports | Your Gmail address |
| `SENDER_PASSWORD` | Gmail App Password | myaccount.google.com → Security → App Passwords → generate for Mail |
| `REPORT_RECIPIENTS` | Who gets the email report | Comma-separated: `boss@co.com,you@co.com` |
| `GMAIL_QUERY` | Which emails to scan | e.g. `from:@yourcompany.com subject:update` |
| `SCAN_INTERVAL_HOURS` | Auto-scan frequency | `6` = every 6 hours; `0` = manual only |

**Gmail OAuth setup (`credentials.json`):**
1. Google Cloud Console → APIs & Services → Enable Gmail API
2. Credentials → Create OAuth2 client (Desktop app) → Download JSON
3. Save as `credentials.json` in the project root
4. Set `USE_MOCK_DATA=False` in `.env`
5. First run opens a browser to authorize — token is saved as `token.pickle` automatically

### 3. Install as a permanent background service (macOS)

```bash
bash install_service.sh
```

This does everything: installs pip deps, builds the React frontend, writes a launchd plist, and starts the service. After this you never need to run anything manually again.

Visit **http://localhost:5001** — dashboard is live.

---

## Daily Use

Open `http://localhost:5001`. Everything else runs automatically.

**Manually trigger an email scan:**
```bash
python3 main.py    # select option 2
```

**Restart the service** (required after `.env` or code changes):
```bash
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist && \
launchctl load ~/Library/LaunchAgents/com.emailreport.plist
```

**Stop / start:**
```bash
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist   # stop
launchctl load ~/Library/LaunchAgents/com.emailreport.plist     # start
```

**View logs:**
```bash
tail -f ~/email-report-automation/logs/server.log
```

---

## Dashboard Pages

| Page | What it shows |
|---|---|
| **Overview** | 5 metric cards (click any to filter the table by status), all projects with Last Updated column, ⚑ red flag on projects not updated in 7+ days, Recent Accomplishments panel, Open Blockers panel |
| **Emails** | Inbox of all scanned emails — subject, sender, received timestamp, processed timestamp, full body on click |
| **Report** | Live preview of the executive HTML report + "Send via Email + Slack" button |
| **Files** | Drag-and-drop file upload (PDF, DOC, images, CSV) stored in `uploads/` |

---

## API Reference

All endpoints at `http://localhost:5001/api/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/summary` | Full executive summary — metrics, accomplishments, blockers, all projects |
| GET | `/api/projects` | All projects as JSON |
| GET | `/api/projects/:id` | Single project + full update history |
| PATCH | `/api/projects/:id` | Update status / progress / owner inline |
| GET | `/api/customers` | All customers |
| GET | `/api/customers/:id` | Customer + their projects |
| GET | `/api/emails` | All scanned emails with timestamps |
| GET | `/api/report` | Executive report as rendered HTML |
| POST | `/api/send-report` | Send report via SMTP email + Slack |
| POST | `/api/scan-now` | Manually trigger a Gmail scan (runs in background) |
| POST | `/api/upload` | Upload a file |
| GET | `/api/uploads/:filename` | Serve an uploaded file |

---

## Architecture

```
Gmail API ──► GmailService (OAuth2 + recursive body extraction)
                    │
                    ▼
         ExtractionService (GPT-3.5 + regex fallback)
                    │
                    ▼
            SQLite Database (projects.db)
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
  Flask REST API          APScheduler
  (port 5001)         (auto email scan)
          │
    ┌─────┴────────────────────┐
    ▼                          ▼
React Frontend           ReportService
(served as static)    (SMTP + Slack Block Kit)
```

**Production stack:** gunicorn (1 worker, SQLite-safe) → Flask → React build  
**Dev stack:** Flask dev server + Vite HMR (`bash start.sh`)

### File Structure

```
email-report-automation/
├── main.py                     CLI — manual scan, seed data, view menu
├── config.py                   All .env variable loading with defaults
├── start.sh                    Dev mode: Flask + Vite HMR on :3000
├── run.sh                      Production: gunicorn on :5001
├── install_service.sh          One-command macOS service installer (launchd)
├── requirements.txt
├── credentials.json            Gmail OAuth credentials (not committed)
├── .env                        Your credentials (not committed)
├── .env.example                Credential template
├── REPO_COVERAGE_AND_QUESTIONS.md  Full gap analysis + open questions
│
├── database/schema.py          DatabaseManager — all SQL (init, queries, inserts)
│
├── services/
│   ├── gmail_service.py        OAuth2 + recursive multipart email body extraction
│   ├── extraction_service.py   GPT prompt + regex fallback → structured dict
│   ├── report_service.py       HTML report generation + SMTP email delivery
│   └── slack_service.py        Slack Block Kit formatting + delivery
│
├── dashboard/app.py            Flask — all API routes, scheduler, React static serving
│
├── frontend/src/
│   ├── App.jsx                 Page routing + layout
│   ├── pages/
│   │   ├── Dashboard.jsx       Overview (filters, red flags, inline edit)
│   │   ├── Emails.jsx          Inbox with timestamps
│   │   ├── Report.jsx          Report preview + send button
│   │   └── Uploads.jsx         Drag-and-drop upload
│   └── components/
│       ├── Sidebar.jsx         Nav: Overview, Emails, Report, Files
│       ├── MetricCard.jsx      Clickable stat card with filter state
│       ├── StatusSelect.jsx    Inline status dropdown (fires PATCH)
│       └── StatusBadge.jsx     Color-coded status pill
│
├── frontend/dist/              Built React app (served by Flask)
├── logs/                       server.log, access.log, error.log
└── uploads/                    Uploaded files
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

See `REPO_COVERAGE_AND_QUESTIONS.md` for the full gap analysis, open questions, and success criteria before going live with real data.

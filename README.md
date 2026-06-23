# Email Report Automation

Scans Gmail from program managers and delivery leads, extracts project details via AI, and consolidates everything into a live executive dashboard with one-click report delivery via email and Slack.

**Dashboard:** `http://localhost:5001`  
**Repo:** `github.com/ethannguyen0530/email-report-automation`

---

## What It Does

- **Gmail scanning** — OAuth2, reads emails matching a configurable search query every 15 minutes; attachment text (PDF, Word, Excel, PowerPoint) extracted and fed to AI alongside email body
- **AI extraction** — GPT-3.5 extracts customer, project, status, progress %, milestone, blocker, owner, and summary from each email+attachment block; regex fallback if GPT fails; confidence gating (≥40 to store, <60 also flagged)
- **React dashboard** — clickable metric cards, inline status editing, health score breakdown modals, click-through from accomplishments/blockers to source emails, real-time updates via Server-Sent Events, red-flag alerts for stale projects
- **Portfolio health scores** — 0–100 per project (−35 Delayed, −20 At Risk, −25 active blocker, −20 stale 14d, −10 stale 7d, −10 low progress); click any score for a full breakdown with reasons and timestamp
- **Executive report** — professional HTML report built for 60-second skimming (metric strip, customer traffic lights, project table with inline blockers); auto-sent daily via email + Slack; preview and send on-demand from Report tab
- **File upload** — drag-and-drop files (PDF, Word, Excel, PowerPoint, CSV, TXT) run through the same AI extraction pipeline as emails and appear on the dashboard automatically
- **Customer management** — auto-detects new customers from emails; manual add/delete from Customers tab; per-customer health scores with breakdown
- **Always-on service** — runs as a macOS background service via launchd; auto-starts on login, restarts on crash, no terminal needed

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
| `SLACK_BOT_TOKEN` | Slack delivery | api.slack.com → Your Apps → Bot Token (`xoxb-...`) |
| `SLACK_CHANNEL` | Slack channel | e.g. `#project-updates` |
| `SENDER_EMAIL` | Gmail that sends reports | Your Gmail address |
| `SENDER_PASSWORD` | Gmail App Password | myaccount.google.com → Security → App Passwords → generate for Mail |
| `GMAIL_QUERY` | Which emails to scan | e.g. `from:@yourcompany.com subject:update` |
| `SCAN_INTERVAL_MINUTES` | Auto-scan frequency | `15` = every 15 minutes; `0` = manual only |
| `REPORT_SEND_HOURS` | Auto-report frequency | `24` = daily; `0` = manual only |

Report recipients are managed from the **Settings tab** in the dashboard (stored in the DB). As a fallback, set `REPORT_RECIPIENTS` in `.env` as a comma-separated list.

**Gmail OAuth setup (`credentials.json`):**
1. Google Cloud Console → APIs & Services → Enable Gmail API
2. Credentials → Create OAuth2 client (Desktop app) → Download JSON
3. Save as `credentials.json` in the project root
4. Set `USE_MOCK_DATA=False` in `.env`
5. First run opens a browser to authorize — token saved as `token.pickle` automatically

### 3. Install as a permanent background service (macOS)

```bash
bash install_service.sh
```

Installs all pip deps, builds the React frontend, writes a launchd plist, and starts the service. After this you never need to run anything manually again.

Visit **http://localhost:5001** — dashboard is live.

---

## Daily Use

Open `http://localhost:5001`. Everything else runs automatically.

**Manually trigger an email scan:**
```bash
curl -X POST http://localhost:5001/api/scan-now
```

**Manually send the report:**
Open dashboard → Report tab → "Send via Email + Slack"

**Restart the service** (required after `.env` or code changes):
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
| **Overview** | 5 clickable metric cards (filter projects table), all projects with inline status editing, clickable health score circles (breakdown with reasons + timestamp), portfolio health score, accomplishments (click any row → source email), open blockers (click → source email), real-time update via SSE |
| **Emails** | All scanned emails — subject, sender, received/processed timestamps, customer filter chips; full body on click |
| **Customers** | All customers with project count, last-updated date, health score (clickable for breakdown); add/delete customers |
| **Report** | Live preview of the executive HTML report + "Send via Email + Slack" button |
| **Files** | Drag-and-drop upload — AI extracts project data and loads it into the dashboard the same as an email scan |
| **Settings** | Manage report recipients without editing `.env` |

---

## API Reference

All endpoints at `http://localhost:5001/api/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/summary` | Metrics, accomplishments_rich, blockers_rich, all projects |
| GET | `/api/projects` | All projects as JSON |
| GET | `/api/projects/:id` | Single project + full update history |
| PATCH | `/api/projects/:id` | Update status / progress / owner inline |
| GET | `/api/customers` | All customers |
| POST | `/api/customers` | Add customer |
| DELETE | `/api/customers/:id` | Delete customer + cascade |
| GET | `/api/customers/:id` | Customer + their projects |
| GET | `/api/emails` | All scanned emails with timestamps |
| GET | `/api/emails?customer=` | Emails filtered by customer name |
| GET | `/api/email-detail/:id` | Full email for source-link click-through |
| GET | `/api/health` | Portfolio + per-project health scores with reasons |
| GET | `/api/alerts` | Stale customers + flagged email count |
| GET | `/api/email-stats` | All-time, weekly, monthly, per-customer counts |
| GET | `/api/report` | Executive report as rendered HTML |
| POST | `/api/send-report` | Send report via SMTP email + Slack |
| POST | `/api/scan-now` | Manually trigger Gmail scan (background) |
| POST | `/api/upload` | Upload file to `uploads/` |
| POST | `/api/process-file` | Trigger AI extraction on uploaded file |
| GET | `/api/uploads/:filename` | Serve an uploaded file |
| GET | `/api/recipients` | List report recipients |
| POST | `/api/recipients` | Add recipient |
| DELETE | `/api/recipients/:id` | Remove recipient |
| GET | `/api/stream` | SSE — real-time scan completion events |

---

## Architecture

```
Gmail API ──► GmailService (OAuth2 + recursive body + attachment extraction)
                    │
              file_extractor.py (shared PDF/Word/Excel/PowerPoint text extraction)
                    │
                    ▼
         ExtractionService (GPT-3.5 + regex fallback + confidence gating)
                    │
                    ▼
            SQLite Database (projects.db)
            customers / projects / updates / emails / recipients
                    │
          ┌─────────┴──────────────────────┐
          ▼                                ▼
  Flask REST API                    APScheduler
  (port 5001)            ┌──────────────────────────┐
          │              │  Email scan: every 15 min │
    ┌─────┴────┐         │  Report send: every 24h   │
    ▼          ▼         └──────────────────────────┘
React Build  SSE /api/stream
(static)    (real-time push to dashboard)
              │
         ReportService (SMTP email + Slack Block Kit)
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
├── requirements.txt            + gunicorn, apscheduler, pdfplumber, python-docx, openpyxl, python-pptx
├── credentials.json            Gmail OAuth credentials (not committed)
├── .env                        Your credentials (not committed)
├── .env.example                Credential template
├── autonomize-report-auto.md   Dev session changelog
├── REPO_COVERAGE_AND_QUESTIONS.md  Full gap analysis + open questions
├── HANDOFF.md                  Setup guide for Ujjwal
│
├── database/schema.py          DatabaseManager — all SQL, health score computation, executive summary
│
├── services/
│   ├── gmail_service.py        OAuth2 + recursive multipart extraction + attachment download
│   ├── file_extractor.py       Shared PDF/Word/Excel/PowerPoint text extraction utility
│   ├── extraction_service.py   GPT prompt + regex fallback → structured dict
│   ├── report_service.py       Executive HTML report generation + SMTP delivery
│   └── slack_service.py        Slack Block Kit formatting + delivery
│
├── dashboard/app.py            Flask — all API routes, APScheduler, React static serving
│
├── frontend/src/
│   ├── App.jsx                 Page routing + layout
│   ├── pages/
│   │   ├── Dashboard.jsx       Overview (health modals, email source modal, full status sync)
│   │   ├── Emails.jsx          Inbox with timestamps + customer filter chips
│   │   ├── Customers.jsx       Customer list + health scores + add/delete
│   │   ├── Report.jsx          Report preview + send button
│   │   ├── Uploads.jsx         Drag-and-drop upload with AI extraction pipeline
│   │   ├── Settings.jsx        Recipient management
│   │   └── ProjectDetail.jsx   Per-project update history
│   └── components/
│       ├── Sidebar.jsx         Nav: Overview, Emails, Customers, Report, Files, Settings
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

```bash
bash start.sh
# Flask on :5001, Vite on :3000 — use http://localhost:3000
```

Build frontend for production:
```bash
cd frontend && /Applications/Cursor.app/Contents/Resources/app/resources/helpers/node node_modules/.bin/vite build
```

---

## Hard Rules

- **No hallucinations** — the system only extracts and summarizes what is explicitly in emails and attachments. GPT never predicts or fills gaps. Ground truth only.
- **Zero duplicates** — enforced at DB level via `gmail_id TEXT UNIQUE`; IntegrityError on duplicate INSERT silently skips
- **Manual status preservation** — `get_or_create_project()` only writes status/progress on first creation; user-set values are never overwritten by subsequent email scans
- **Always running** — launchd KeepAlive=true; scan every 15 min; report every 24h; no human intervention after setup

---

## Pre-Production Checklist

See `REPO_COVERAGE_AND_QUESTIONS.md` for the full gap analysis, open questions, and success criteria before going live with real data.

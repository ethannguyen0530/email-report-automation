# autonomize-report-auto

**Project:** Email Report Automation System  
**Repo:** github.com/ethannguyen0530/email-report-automation  
**Session Date:** June 22, 2026  
**Stack:** Python Flask + React (Vite) + SQLite + OpenAI GPT-3.5 + Gmail OAuth2 + Slack Block Kit

---

## What Was Built This Session

### 1. Dashboard — Metric Card Filters

**Problem:** Dashboard showed stats but clicking them did nothing.  
**Fix:** Made all 5 metric cards (Total, On Track, At Risk, Delayed, Completed) clickable. Clicking a card filters the projects table to that status. Active card shows glow, bottom accent bar, and tinted background. A "Clear filter ×" button resets. Title and subtitle update to reflect the current filter.

**Files changed:** `frontend/src/pages/Dashboard.jsx`, `frontend/src/components/MetricCard.jsx`

---

### 2. Dashboard — Red Flag Alerts for Stale Projects

**Problem:** No visibility into which projects hadn't been updated recently.  
**Fix:** Added `isStale()` logic — any project with no update in 7+ days gets a red ⚑ flag, red-tinted row, and red "Last Updated" text. Completed projects are exempt. A "X need attention" badge appears in the header when stale projects exist.

**Files changed:** `frontend/src/pages/Dashboard.jsx`

---

### 3. Dashboard — "Last Updated" Column

**Problem:** Projects table had no timestamp showing recency.  
**Fix:** Added Last Updated column with human-readable relative dates (Today, Yesterday, 3d ago, Jun 15). Backed by a LEFT JOIN in `get_all_projects()` that returns `MAX(u.created_at)` as `last_updated`.

**Files changed:** `frontend/src/pages/Dashboard.jsx`, `database/schema.py`

---

### 4. Executive Report Page

**Problem:** No way to view or send the executive report from the dashboard.  
**Fix:** Added a Report page that fetches `/api/report` and renders it in a full-height iframe. "Send via Email + Slack" button calls `POST /api/send-report` and shows ✓ Sent or an error message. Added Report nav item to Sidebar with a document SVG icon.

**Files changed:** `frontend/src/pages/Report.jsx` (new), `frontend/src/components/Sidebar.jsx`, `frontend/src/App.jsx`, `dashboard/app.py`

---

### 5. Executive Report — Full HTML Redesign

**Problem:** Report HTML was plain and ugly.  
**Fix:** Complete rewrite with professional styling:
- Dark indigo/purple gradient header with "CONFIDENTIAL · EXECUTIVE SUMMARY" label
- 5 metric cards with colored values
- Two-column grid: Recent Accomplishments (green) + Open Blockers (red)
- Full Projects table with color-coded status pills and inline progress bars
- Clean white card layout on light gray background

**Files changed:** `services/report_service.py`

---

### 6. Executive Report — Data Quality Fixes

**Problem:** Accomplishments showed "Unknown completed TBD on Wed, 20 Ma" filler. Blockers appeared twice.

**Fixes:**
- Accomplishments query now uses `summary` field (not `milestone`), filters out Unknown/TBD/empty/short strings, deduplicates with `DISTINCT`
- Blockers query deduplicates with `DISTINCT`
- Removed the "Project Milestones & Updates" section entirely (was redundant with the rest of the report)
- "Key Highlights & Blockers" renamed and blockers removed from that section (they already have their own dedicated section)

**Files changed:** `database/schema.py`, `services/report_service.py`

---

### 7. Emails Page — Processed Timestamps

**Problem:** Emails tab showed no timing information.  
**Fix:** Added "Received" and "Processed" timestamps per email. Processed timestamp shown in green. Both shown in inbox list and in the detail pane.

**Files changed:** `frontend/src/pages/Emails.jsx`

---

### 8. Gmail Body Extraction Fix

**Problem:** Some emails showed blank or partial body because Gmail's nested `multipart/alternative` structure wasn't being traversed correctly.  
**Fix:** Replaced flat `_get_body()` with recursive `_extract_text()` that traverses all nested parts. Three-pass priority order: plain text first, then nested multipart containers, then HTML fallback (tags stripped).

**Files changed:** `services/gmail_service.py`

---

### 9. GPT Extraction — Summary Field + Body Limit

**Problem:** Extraction prompt had no `summary` field; body was cut at 1000 chars (too short for real emails).  
**Fix:** Added `summary` field to GPT prompt: "One sentence describing the current status or key update." Raised body limit from 1000 to 3000 chars. Added `In Progress` to valid status list. Placeholder extraction returns `summary: None` instead of `milestone: "TBD"`.

**Files changed:** `services/extraction_service.py`

---

### 10. Update Storage Fix

**Problem:** `main.py` and the scheduler were storing "Update from:" prefix strings as the summary, producing junk data everywhere.  
**Fix:** Both `process_real_emails()` and the scheduler's `run_email_scan()` now store:
```python
extracted.get('summary') or extracted.get('milestone') or email['subject'][:120]
```

**Files changed:** `main.py`, `dashboard/app.py`

---

### 11. CustomerDetail Dark Theme Fix

**Problem:** CustomerDetail.jsx had hardcoded white/light colors that looked broken in the dark UI.  
**Fix:** Complete rewrite using CSS variables (`var(--bg-card)`, `var(--border)`, `var(--text-primary)`, etc.).

**Files changed:** `frontend/src/pages/CustomerDetail.jsx`

---

### 12. Sidebar Footer Cleanup

**Problem:** "Email Report Automation" text appeared in the bottom-left corner of the sidebar — redundant and visually cluttered.  
**Fix:** Removed entirely. Footer is now just a spacer div.

**Files changed:** `frontend/src/components/Sidebar.jsx`

---

### 13. Automated Email Scanning (APScheduler)

**Problem:** No way to run scans automatically — had to keep a terminal open and run manually.  
**Fix:** Added `BackgroundScheduler` from APScheduler to `dashboard/app.py`. Interval controlled by `SCAN_INTERVAL_HOURS` in `.env` (0 = disabled). Guard against double-start in Flask debug reloader via `WERKZEUG_RUN_MAIN` environment variable check. Also added `POST /api/scan-now` endpoint for manual trigger without the CLI.

**Files changed:** `dashboard/app.py`, `config.py`, `requirements.txt`

---

### 14. Production Service — Gunicorn + macOS launchd

**Problem:** App required an open terminal to stay running. Sharing with Ujjwal needed a sustainable deployment.  
**Fix:**
- Added `gunicorn` as WSGI server (`--workers 1` for SQLite safety)
- Flask now serves the React build as static files — no Node process at runtime
- `install_service.sh`: one-command installer that finds Python/npm dynamically, builds the React frontend, writes a launchd plist to `~/Library/LaunchAgents/com.emailreport.plist`, and starts the service immediately
- `KeepAlive=true` restarts on crash; `ThrottleInterval=10` prevents spin loops
- Logs to `logs/server.log`, `logs/access.log`, `logs/error.log`

**Files changed/created:** `run.sh` (new), `install_service.sh` (new), `dashboard/app.py`, `requirements.txt`

---

### 15. Config Cleanup

**Problem:** `config.py` had `FLASK_DEBUG=True` default; no `SCAN_INTERVAL_HOURS` or `FLASK_PORT`.  
**Fix:** Defaults set to `FLASK_DEBUG=False`, added `SCAN_INTERVAL_HOURS`, `FLASK_PORT=5001`.

**Files changed:** `config.py`, `.env.example`

---

### 16. Full Code Audit — 5 Bugs Fixed

After building everything, a full file-by-file audit found and fixed:

| # | File | Bug | Fix |
|---|---|---|---|
| 1 | `report_service.py` | `notes_html` built on every report request but never used (dead code after section deletion) | Removed the unused code block |
| 2 | `database/schema.py` | No real `processed_at` timestamp — was returning `created_at` (insert time, not processing time) | Added `processed_at` column with auto-migration; `mark_email_processed()` now writes real timestamp |
| 3 | `dashboard/app.py` | Emails API returned `created_at` labeled as `processed_at` | Now selects actual `processed_at` column |
| 4 | `services/gmail_service.py` | If HTML part appears before plain text in Gmail's parts list, returned tag-stripped HTML instead of clean plain text | Three-pass extraction: plain text → nested multipart → HTML fallback |
| 5 | `main.py` | Top-level `from dashboard.app import app` started APScheduler on every CLI run; seed function stored `"Update from email"` filler | Moved import to lazy (only loads for option 4); seed uses real milestone text |

---

## Documentation Created

### `REPO_COVERAGE_AND_QUESTIONS.md`
Full technical inventory of the MVP:
- Everything that is built (18 features, all marked complete/incomplete)
- What's not in the repo yet (11 missing features with priority)
- 7 sections of critical questions that must be answered before production
- Credentials status table
- Success criteria (MVP vs Production Ready)
- Next steps in priority order
- Full file structure reference

### `HANDOFF.md` (for Ujjwal)
Step-by-step handoff document covering:
- What is already built (the 80–90%)
- Exact credentials needed and how to get each one (OpenAI, Slack, Gmail SMTP, OAuth)
- Gmail search query questions to answer
- Deployment decision table (laptop / local network / cloud + auth)
- 8-step setup sequence
- Service commands quick reference
- Fill-in-the-blank answers section

### `README.md` (full rewrite)
- Accurate setup guide for the current production setup
- Full API reference table (12 endpoints)
- Architecture diagram
- File structure with descriptions
- Daily use and service commands
- Development mode instructions

---

## Final File State

```
email-report-automation/
├── main.py                     CLI — lazy dashboard import, fixed seed data
├── config.py                   FLASK_DEBUG=False default, SCAN_INTERVAL_HOURS, FLASK_PORT
├── start.sh                    Dev mode (Flask + Vite HMR)
├── run.sh                      Production (gunicorn --workers 1)
├── install_service.sh          macOS launchd one-command installer
├── requirements.txt            + gunicorn==21.2.0, apscheduler==3.10.4
├── .env.example                Clean template with all current keys
├── README.md                   Full rewrite — accurate production docs
├── HANDOFF.md                  Ujjwal next-steps document
├── REPO_COVERAGE_AND_QUESTIONS.md  Full gap analysis
│
├── database/schema.py          processed_at column + migration, last_updated JOIN
├── services/
│   ├── gmail_service.py        Three-pass recursive body extraction
│   ├── extraction_service.py   summary field, 3000 char body, In Progress status
│   ├── report_service.py       Full HTML redesign, removed dead notes code
│   └── slack_service.py        Unchanged
├── dashboard/app.py            APScheduler, /api/scan-now, /api/report, /api/send-report,
│                               React static serving, processed_at in emails API
└── frontend/src/
    ├── App.jsx                 + Report page route
    ├── pages/
    │   ├── Dashboard.jsx       Filters, red flags, last_updated, stale detection
    │   ├── Emails.jsx          Received + processed timestamps
    │   ├── Report.jsx          New — iframe preview + send button
    │   └── CustomerDetail.jsx  Full dark theme rewrite
    └── components/
        ├── Sidebar.jsx         + Report nav item, footer text removed
        └── MetricCard.jsx      + onClick, active props, glow state
```

---

## Current Status

**Service:** Running permanently at `http://localhost:5001` via launchd  
**Auto-scan:** Every 6 hours (`SCAN_INTERVAL_HOURS=6` in `.env`)  
**GitHub:** Fully up to date — `github.com/ethannguyen0530/email-report-automation`  
**Terminal needed:** No — close all terminals, service auto-restarts on crash and login

**Blocked on (Ujjwal to provide):**
- `OPENAI_API_KEY` — required for AI extraction
- `SLACK_BOT_TOKEN` + `SLACK_CHANNEL` — required for Slack delivery
- `SENDER_EMAIL` + `SENDER_PASSWORD` + `REPORT_RECIPIENTS` — required for email delivery
- Gmail search query tuned to real project update senders

# Repo Coverage & Open Questions

**Project:** Email Report Automation System  
**Last Updated:** June 22, 2026  
**Author:** Ethan Nguyen  
**Repo:** github.com/ethannguyen0530/email-report-automation

---

## What This Repo Does — MVP Complete ✅

### ✅ Gmail Integration (OAuth2)

- OAuth2 authentication via `credentials.json` + `token.pickle` (browser prompt on first run, silent after)
- Scans Gmail for emails using a configurable search query (`GMAIL_QUERY` in `.env`)
- Configurable result limit (`GMAIL_MAX_RESULTS`)
- Recursive multipart body extraction — handles nested `multipart/alternative` and `multipart/mixed` structures; falls back from HTML to plain text
- Deduplication: skips emails already stored by `gmail_id`
- Stores raw emails in SQLite `emails` table with sender, subject, body, received timestamp, processed flag

### ✅ AI-Powered Data Extraction (OpenAI GPT-3.5)

- Each email body (up to 3000 chars) sent to GPT with a structured prompt
- Extracts per email:
  - **Customer name**
  - **Project name**
  - **Status** — On Track / At Risk / Delayed / Completed / In Progress
  - **Progress %** — 0–100
  - **Milestone** — what was completed
  - **Blocker** — what is blocking progress
  - **Owner** — who sent the update
  - **Summary** — one-sentence current status
- **Regex fallback** if GPT fails or returns malformed JSON
- Results stored in `projects`, `customers`, `updates` tables
- Update summary stored as: `extracted.get('summary') or extracted.get('milestone') or email subject`

### ✅ SQLite Database (4 tables)

| Table | Contents |
|---|---|
| `customers` | Unique customer names |
| `projects` | Project per customer — status, progress, owner, created_at |
| `updates` | Update records — summary, milestone, blocker, owner, date |
| `emails` | Raw email archive — gmail_id (unique), sender, subject, body, received_at, processed flag |

Key queries:
- `get_all_projects()` — LEFT JOIN on updates for `MAX(created_at)` as `last_updated`
- `get_executive_summary()` — aggregates metrics, accomplishments (deduped, no Unknown/TBD), blockers (deduped), project notes (one per project, milestone > blocker > summary priority)
- `mark_email_processed()` — sets `processed=1` and `created_at` (used as processed timestamp)

### ✅ React Dashboard (Vite, served by Flask in production)

**Overview Page**
- 5 clickable metric cards: Total, On Track, At Risk, Delayed, Completed
  - Clicking any card **filters the projects table** to that status
  - Active card shows glow + bottom accent bar; "Clear filter" button resets
  - Filter persists until cleared or a different card is clicked
- Projects table columns: Project, Customer, Status (inline editable), Progress bar, Owner, Last Updated
- **Red flag alerts (⚑):** projects with no update in 7+ days highlighted in red — Completed projects are exempt
- "X projects need attention" badge in table header when stale projects exist
- Recent Accomplishments panel — real data from updates, deduped, Unknown/TBD filtered out
- Open Blockers panel — real data, deduped

**Emails Page**
- Inbox-style list of all scanned emails
- Per email: subject, sender, received timestamp, processed timestamp (green when processed), status badge
- Click email to open detail pane with full body and all timestamps
- Split layout when detail pane is open

**Executive Report Page**
- Renders the full HTML executive report live in an iframe (fetches `/api/report`)
- Report sections: gradient header, metric cards, Recent Accomplishments, Open Blockers, All Projects table
- "Send via Email + Slack" button — calls `POST /api/send-report`, shows ✓ Sent or error

**Files Page**
- Drag-and-drop upload zone
- Supported: PDF, TXT, DOC, DOCX, CSV, PNG, JPG, GIF, WEBP
- Image preview on hover; file size and type display
- Files stored in `uploads/` directory, served via Flask

### ✅ Flask REST API (port 5001)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/summary` | Metrics, accomplishments, blockers, all projects |
| GET | `/api/projects` | All projects as JSON |
| GET | `/api/projects/:id` | Single project + update history |
| PATCH | `/api/projects/:id` | Update status / progress / owner |
| GET | `/api/customers` | All customers |
| GET | `/api/customers/:id` | Customer + their projects |
| GET | `/api/emails` | All emails with received and processed timestamps |
| GET | `/api/report` | Executive report as rendered HTML |
| POST | `/api/send-report` | Send report via SMTP + Slack |
| POST | `/api/scan-now` | Trigger Gmail scan in background thread |
| POST | `/api/upload` | Upload file |
| GET | `/api/uploads/:filename` | Serve uploaded file |

- CORS enabled (for React dev proxy on `:3000`)
- Legacy HTML routes: `/html`, `/html/customer/:id`, `/html/project/:id`

### ✅ Executive Report Generation

HTML report sections:
- Dark gradient header (indigo/purple) with confidential label, date, generated-at time
- 5 metric cards (Total, On Track, At Risk, Delayed, Completed) with colored values
- Recent Accomplishments — real summaries, deduped, no Unknown/TBD filler
- Open Blockers — real blocker text, deduped
- All Projects table — color-coded status pills, inline progress bars, owner column
- Footer: "Confidential — For internal use only"

Dual delivery:
- SMTP email (HTML formatted) to `REPORT_RECIPIENTS`
- Slack (Block Kit formatted) to `SLACK_CHANNEL`

### ✅ Inline Status Editing

- Each project row has a `<StatusSelect>` dropdown
- Selecting a new status fires `PATCH /api/projects/:id` immediately — no page reload

### ✅ Automatic Email Scanning (APScheduler)

- `SCAN_INTERVAL_HOURS` in `.env` controls frequency (0 = disabled)
- `BackgroundScheduler` starts when gunicorn imports `dashboard.app`
- Guard against double-start in Flask debug reloader (`WERKZEUG_RUN_MAIN` check)
- Also available on-demand via `POST /api/scan-now` or `python3 main.py` → option 2

### ✅ macOS Background Service (launchd)

- `bash install_service.sh` — one command installs everything:
  - Finds Python and npm dynamically
  - Builds React frontend (`npm run build`)
  - Installs pip deps
  - Writes `~/Library/LaunchAgents/com.emailreport.plist`
  - Starts service immediately (`launchctl load`)
- `KeepAlive=true` — restarts on crash
- `ThrottleInterval=10` — 10-second delay before restart (prevents spin loop)
- Logs to `logs/server.log`, `logs/access.log`, `logs/error.log`
- **No terminal needed at runtime** — close all terminal windows after setup

### ✅ Production WSGI Server (gunicorn)

- `python3 -m gunicorn dashboard.app:app --bind 127.0.0.1:5001 --workers 1 --timeout 120`
- Single worker — safe for SQLite (no concurrent write conflicts)
- Flask serves React build as static files — no Node process at runtime

### ✅ GitHub Deployment

- Full repo at `github.com/ethannguyen0530/email-report-automation`
- `requirements.txt` — all Python deps including gunicorn, apscheduler
- `.env.example` — clean template with all required keys
- `install_service.sh` — one-command setup for any Mac
- `REPO_COVERAGE_AND_QUESTIONS.md` — this file

---

## What's NOT in This Repo Yet ❌

| Feature | Status | Priority |
|---|---|---|
| **Scheduled report delivery** | Manual "Send" button only — no automatic daily/weekly send | High — add `APScheduler` job for `run_send_report()` |
| **Real-time dashboard updates** | Manual page refresh required | Medium — add `setInterval` polling or WebSocket |
| **Cloud deployment** | Local only — dashboard not accessible from outside your Mac | High if others need access |
| **User authentication** | No login — anyone on same network can access dashboard | High if dashboard is public-facing |
| **OpenAI API key** | `.env` var exists, no key set yet | Required for AI extraction to work |
| **Slack bot token** | `.env` var exists, no token set yet | Required for Slack delivery |
| **SMTP credentials** | `.env` vars exist, not configured yet | Required for email delivery |
| **Email search tuning** | `GMAIL_QUERY` is a broad default — may pull irrelevant emails | High — needs tuning to real senders/keywords |
| **Duplicate project detection** | GPT may extract "Cigna Migration" and "Cigna migration" as different | Medium — fuzzy match on project + customer |
| **Multi-Gmail account support** | Single OAuth account per deployment | Low |
| **PostgreSQL option** | SQLite fine for 1 user / <10k rows; not for concurrent multi-user | Low unless scaling |
| **Charts / visualizations** | Table and card layout only — no trend charts | Low |
| **Test suite** | No automated tests (unit or integration) | Medium for production confidence |
| **Pagination** | All rows loaded at once — fine for <100 projects | Low |
| **Settings UI** | Email query and scan interval configurable only via `.env` | Low |
| **Data validation layer** | Trusts GPT extraction — no field-level validation before DB insert | Medium |

---

## Critical Questions — Answer Before Production

### 1. Gmail

- ☐ **Which Gmail account** scans project update emails? (Personal? Shared team inbox?)
- ☐ **Search criteria** — how to identify the right emails?
  - By sender domain? (e.g., `from:@autonomize.ai`)
  - By specific senders? (list all program managers by email)
  - By Gmail label applied manually or by a filter rule?
  - By subject keywords? (e.g., `subject:"weekly update" OR subject:"project status"`)
- ☐ **How far back** should the initial scan go? (7 days? 30 days? All time?)
- ☐ **Ongoing frequency** — every 6 hours is currently configured; is that right?
- ☐ **Read-only OK?** — system never modifies or labels emails, only reads

### 2. Report Distribution

- ☐ **Exact email recipients** — who receives the executive report?
- ☐ **Slack workspace and channel** — which workspace? Which channel?
- ☐ **Report frequency** — automatic on a schedule, or manual button only?
- ☐ **Report scope** — all projects, or only At Risk + Delayed?

### 3. Credentials Needed

| Credential | How to Get | Current Status |
|---|---|---|
| `credentials.json` (Gmail OAuth2) | Google Cloud Console → Gmail API → OAuth client | ✅ File exists |
| `OPENAI_API_KEY` | platform.openai.com → API Keys | ☐ Not set in .env |
| `SLACK_BOT_TOKEN` | api.slack.com → Your Apps → Bot Token (xoxb-...) | ☐ Not set in .env |
| `SLACK_CHANNEL` | Slack channel name | ☐ Not set in .env |
| `SENDER_EMAIL` | Gmail address that sends reports | ☐ Not set in .env |
| `SENDER_PASSWORD` | Gmail App Password | ☐ Not set in .env |
| `REPORT_RECIPIENTS` | Comma-separated recipient list | ☐ Not set in .env |

**How to generate a Gmail App Password:**
1. myaccount.google.com → Security → 2-Step Verification → App Passwords
2. Name it anything → Generate
3. Paste the 16-character password into `.env` as `SENDER_PASSWORD`

### 4. Data Extraction Quality

- ☐ **Are the 7 extracted fields correct?** (Customer, Project, Status, Progress %, Milestone, Blocker, Owner) — or are more needed (due date, priority, budget)?
- ☐ **Customer name canonicalization** — GPT may extract "Cigna", "CIGNA Corp", "Cigna Health" as different customers. Is a canonical name list needed?
- ☐ **OpenAI cost** — GPT-3.5 is ~$0.001–0.002 per email. At 50 emails/day that's ~$2–3/month. Acceptable?
- ☐ **What defines a valid "blocker"?** The AI infers blocking language. Does your team use specific terms?

### 5. Scheduling

- ☐ **Automatic report delivery?**
  - Option A: Manual only (press Send in dashboard)
  - Option B: Scheduled — system sends report at a fixed time (daily at 8am, weekly on Monday, etc.)
  - Option C: Both — scheduled + on-demand button
- ☐ **Email scan trigger?** Currently set to every 6 hours (`SCAN_INTERVAL_HOURS=6`). Is this right?
- ☐ **Machine-off behavior** — if the MacBook is closed/off, no scans run. Is this acceptable or does this need cloud hosting?

### 6. Deployment Environment

- ☐ **Who needs dashboard access?**
  - Just you → `localhost:5001` is fine, no changes needed
  - Others on same network → expose port, add IP restriction
  - Remote stakeholders → needs cloud deployment + public URL + auth
- ☐ **Cloud deployment needed?** Options: Railway, Render, GCP Cloud Run (~2–4h to set up, ~$5–20/month)
- ☐ **Authentication needed?** If others access the dashboard, a login screen is required

### 7. Scale

- ☐ **How many emails per day?** (10? 100? 1,000?)
- ☐ **How many projects total?** (10? 50? 500?)
- ☐ **How long keep history?** All time? 90 days? 1 year?
- ☐ **SQLite acceptable?** Fine for single user + <10k rows. Multiple simultaneous users → PostgreSQL

---

## Answers (Fill In Before Production)

### Gmail
- Account to scan: `_________________________________`
- Search query: `_________________________________`
- Initial lookback: `_________________________________`
- Scan frequency (currently 6h): `_________________________________`

### Report Distribution
- Email recipients: `_________________________________`
- Slack workspace: `_________________________________`
- Slack channel: `_________________________________`
- Report schedule: `_________________________________`

### Credentials Checklist
- ☐ `credentials.json` in project root
- ☐ `OPENAI_API_KEY` set in `.env`
- ☐ `SLACK_BOT_TOKEN` set in `.env`
- ☐ `SLACK_CHANNEL` set in `.env`
- ☐ `SENDER_EMAIL` + `SENDER_PASSWORD` set in `.env`
- ☐ `REPORT_RECIPIENTS` set in `.env`
- ☐ `GMAIL_QUERY` tuned to real senders/keywords

### Deployment
- ☐ Local laptop only (current)
- ☐ Cloud VM — provider: `_________________________________`
- ☐ PaaS — platform: `_________________________________`

---

## Success Criteria

### MVP — Functionally Complete ✅
- ✅ Gmail OAuth2 connects and scans emails
- ✅ GPT extracts structured data from email body
- ✅ Dashboard loads with real extracted data (not mock)
- ✅ Metric cards filter projects table by status when clicked
- ✅ Red flag alerts highlight stale projects (>7 days, excludes Completed)
- ✅ Status editable inline per project row
- ✅ Last Updated column shows human-readable relative timestamp
- ✅ Files uploadable via drag-and-drop
- ✅ Emails viewable with received and processed timestamps
- ✅ Executive report renders with real data — professional layout
- ✅ All code in GitHub (`github.com/ethannguyen0530/email-report-automation`)
- ✅ `install_service.sh` installs service with one command
- ✅ Service auto-starts on login, restarts on crash, needs no open terminal
- ✅ Auto email scan every 6 hours via APScheduler

### Production Ready — Remaining Gaps
- ☐ All credentials filled in `.env` (OpenAI, Slack, SMTP)
- ☐ `GMAIL_QUERY` tuned to target only real project update emails
- ☐ Extraction quality validated on 20+ real emails (no Unknown/TBD spam)
- ☐ Report sends successfully to real email recipients via SMTP
- ☐ Slack message delivers to correct workspace and channel
- ☐ End-to-end test: email arrives → extracted → appears on dashboard → report sent
- ☐ Deployment decision made (local vs cloud) based on who needs access

---

## Next Steps — In Priority Order

1. **Answer the critical questions above** — Gmail criteria and report recipients first
2. **Set credentials in `.env`** — OpenAI, Slack, SMTP
3. **Tune `GMAIL_QUERY`** — restrict to real project update senders
4. **Authorize Gmail** — `python3 main.py` → option 2 → browser auth flow → `token.pickle` saved
5. **Validate extraction quality** — run on 20–30 real emails, check dashboard for bad data
6. **Test report delivery** — click "Send via Email + Slack", confirm receipt
7. **Decide deployment** — if others need access, deploy to cloud
8. **Add scheduled report send** (if required) — ~30 min with APScheduler

---

## File Structure Reference

```
email-report-automation/
├── main.py                     CLI entry point — scan, report, seed
├── config.py                   .env variable loading with defaults
├── start.sh                    Dev mode (Flask dev + Vite HMR on :3000)
├── run.sh                      Production startup (gunicorn on :5001)
├── install_service.sh          macOS launchd service installer
├── requirements.txt            Python deps (gunicorn, apscheduler, flask, openai, etc.)
├── credentials.json            Gmail OAuth creds (not committed to git)
├── token.pickle                Gmail access token (auto-created on first auth, not committed)
├── .env                        Credentials (not committed)
├── .env.example                Template for .env
│
├── database/schema.py          DatabaseManager — init, queries, inserts
│
├── services/
│   ├── gmail_service.py        OAuth2 auth + recursive email body extraction
│   ├── extraction_service.py   GPT prompt + regex fallback
│   ├── report_service.py       HTML report generation + SMTP delivery
│   └── slack_service.py        Slack Block Kit formatting + delivery
│
├── dashboard/app.py            Flask app — all routes, APScheduler, React serving
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             Page router
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   Overview — filters, stale flags, inline edit
│   │   │   ├── Emails.jsx      Inbox with timestamps
│   │   │   ├── Report.jsx      Report iframe + send button
│   │   │   └── Uploads.jsx     Drag-and-drop upload
│   │   └── components/
│   │       ├── Sidebar.jsx     Navigation
│   │       ├── MetricCard.jsx  Clickable stat card
│   │       ├── StatusSelect.jsx Inline dropdown (PATCH)
│   │       └── StatusBadge.jsx Color-coded pill
│   ├── dist/                   Built React app (served by Flask)
│   └── vite.config.js          Proxies /api/* to :5001 in dev
│
├── logs/
│   ├── server.log              Combined stdout/stderr
│   ├── access.log              HTTP access log
│   └── error.log               gunicorn error log
│
└── uploads/                    Uploaded files
```

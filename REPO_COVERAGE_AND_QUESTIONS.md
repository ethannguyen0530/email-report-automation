# Repo Coverage & Open Questions

**Project:** Email Report Automation System
**Last Updated:** June 22, 2026
**Author:** Ethan Nguyen
**Repo:** github.com/ethannguyen0530/email-report-automation

---

## What This Repo WILL Do — MVP Complete ✅

### ✅ Gmail Integration (Real, OAuth2)

- **OAuth2 authentication** to a Google account via `credentials.json` + `token.pickle`
- Scans Gmail for emails from program managers and delivery leads
- Configurable search criteria (keyword, sender, label, date range) in `.env`
- Retrieves full email body + metadata (from, subject, date, thread ID)
- Deduplication: skips emails already stored by `gmail_id`
- Stores raw emails in SQLite `emails` table for audit trail

### ✅ AI-Powered Data Extraction (OpenAI GPT)

- Each email is sent to GPT (model configurable in `.env`) with a structured prompt
- GPT extracts per email:
  - **Customer name**
  - **Project name**
  - **Status** (On Track / At Risk / Delayed / Completed / In Progress)
  - **Progress %** (0–100)
  - **Milestone** (what was completed)
  - **Blocker** (what is blocking progress)
  - **Owner name** (who sent the update)
- **Regex fallback** if GPT fails or returns malformed JSON
- Handles multiple projects per email
- Results stored in `projects`, `customers`, and `updates` tables

### ✅ Structured SQLite Database

Four tables:
| Table | Contents |
|---|---|
| `customers` | Unique customer names |
| `projects` | Project per customer with status, progress, owner |
| `updates` | Individual update records linked to projects |
| `emails` | Raw email archive with processed flag |

- `get_all_projects()` — returns all projects with last update timestamp via LEFT JOIN
- `get_executive_summary()` — aggregates metrics, accomplishments, blockers, project notes
- `mark_email_processed()` — tracks which emails have been processed

### ✅ React Dashboard (Vite, port 3000)

**Overview Page (`/dashboard`)**
- 5 clickable metric cards: Total, On Track, At Risk, Delayed, Completed
  - Clicking any card **filters the projects table** to that status
  - Active card glows with color accent; "Clear filter" button resets
- Recent Accomplishments panel — pulled from real update summaries
- Open Blockers panel — deduplicated, real blocker text only
- Projects table with columns: Project, Customer, Status (inline editable), Progress bar, Owner, Last Updated
- **Red flag alerts** (⚑): projects with no update in 7+ days highlighted in red — Completed projects exempt
- "X projects need attention" badge in header when stale projects exist

**Emails Page (`/emails`)**
- Inbox-style list of all scanned emails
- Per email: subject, sender, received timestamp, processed timestamp, status badge (processed / pending)
- Click to open detail pane: full email body, all timestamps
- Split layout when detail pane is open

**Executive Report Page (`/report`)**
- Renders the full HTML executive report live in an iframe
- Professional design: gradient header, pill status badges, inline progress bars, card layout
- "Send via Email + Slack" button — triggers `/api/send-report` endpoint

**Files Page (`/uploads`)**
- Drag-and-drop file upload zone
- Supported types: PDF, TXT, DOC, DOCX, CSV, PNG, JPG, GIF, WEBP
- Image preview on hover
- File size display, file type icons
- Files stored in `uploads/` directory, served via Flask

### ✅ Flask REST API (port 5001)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/summary` | Executive summary with projects, metrics, accomplishments, blockers, notes |
| GET | `/api/projects` | All projects as JSON |
| GET | `/api/projects/:id` | Single project with full update history |
| PATCH | `/api/projects/:id` | Update project status/progress/owner (inline edit) |
| GET | `/api/customers` | All customers |
| GET | `/api/customers/:id` | Customer + their projects |
| GET | `/api/emails` | All emails with processed timestamps |
| GET | `/api/report` | Executive report as rendered HTML |
| POST | `/api/send-report` | Sends report via SMTP email + Slack |
| POST | `/api/upload` | File upload endpoint |
| GET | `/api/uploads/:filename` | Serve uploaded file |

- CORS enabled for React dev proxy
- Legacy HTML routes at `/html`, `/html/customer/:id`, `/html/project/:id`

### ✅ Executive Report Generation

HTML report includes:
- Dark gradient header with date/time and confidential label
- 5 metric cards (Total, On Track, At Risk, Delayed, Completed)
- Recent Accomplishments section (real data, deduped, no Unknown/TBD)
- Open Blockers section (real data, deduped)
- **Project Notes section** — most recent update summaries per project
- Full Projects table with color-coded status pills and inline progress bars
- Professional typography, clean white card layout

Dual distribution:
- Email via SMTP (Gmail or custom SMTP server) — HTML formatted
- Slack via Bot token — Block Kit formatted

### ✅ Inline Status Editing

- Each project row has a `<StatusSelect>` dropdown
- Selecting a new status fires `PATCH /api/projects/:id` immediately
- Options: On Track, At Risk, Delayed, Completed, In Progress
- No page reload required

### ✅ One-Command Startup

```bash
bash ~/email-report-automation/start.sh
```

Starts both Flask (port 5001) and React (port 3000) in parallel background processes. Handles Node.js PATH injection for non-standard installs.

### ✅ GitHub Deployment

- Full repo at `github.com/ethannguyen0530/email-report-automation`
- `requirements.txt` with all Python dependencies
- `.env.example` with all required credential placeholders
- `start.sh` one-command startup
- Authenticated as `ethannguyen0530` via `gh` CLI

---

## What's NOT in This Repo Yet ❌

| Feature | Why Excluded | Add Later? |
|---|---|---|
| **Automatic Scheduling** | Need to confirm frequency preference | Yes — APScheduler or cron, ~30 min to add |
| **Slack Bot Token** | `.env` var exists, no token provided yet | Yes — needs workspace + token from Slack API |
| **SMTP Email Credentials** | `.env` var exists, no credentials yet | Yes — Gmail app password or SMTP server |
| **OpenAI API Key** | Required for real extraction; user must provide | Yes — add to `.env` as `OPENAI_API_KEY` |
| **Cloud Deployment** | Local/GitHub only for MVP | Yes — GCP Cloud Run, Railway, or Render (~2h) |
| **User Authentication** | No login system for dashboard | Yes — Flask-Login or JWT if multi-user needed |
| **Scheduled Report Sending** | Manual "Send" button only | Yes — APScheduler, daily/weekly trigger |
| **Multi-Gmail Account** | Single OAuth account per deployment | Yes — can loop multiple `credentials.json` files |
| **PostgreSQL Option** | SQLite works for MVP, not for scale | Yes — swap `DatabaseManager` driver (~4h) |
| **Real-time Dashboard Updates** | Page requires manual refresh | Yes — polling via `setInterval` or WebSocket |
| **Charts & Visualizations** | Table/card only, no charts | Yes — Recharts or Chart.js integration |
| **Email Search Config UI** | Hardcoded in `.env`, no UI to change | Yes — Settings page |
| **Test Suite** | No automated tests | Yes — pytest for API, Vitest for React |
| **Production WSGI Server** | Dev Flask only (`app.run`) | Yes — Gunicorn behind nginx for production |
| **Duplicate Project Detection** | GPT may create near-duplicate project names | Yes — fuzzy match on project names |
| **Email Search Criteria** | Currently broad, may pull irrelevant emails | Needs tuning — sender filters, subject keywords |
| **Data Validation Layer** | Trusts GPT extraction output | Yes — validate fields before DB insert |
| **Pagination** | Projects/emails tables show all rows | Yes — add server-side pagination if >100 rows |
| **Dark Mode for Report PDF** | Report HTML is light-themed only | Nice-to-have |
| **Apollo/Hunter API integration** | Not relevant for this tool | No |

---

## Critical Questions — MUST Answer Before Production Build

### 1. Gmail Setup

- ☐ **Which Gmail account** should the system scan? (Your personal Gmail? A shared team inbox? A service account?)
- ☐ **Email search criteria** — how to identify project update emails?
  - By sender domain? (e.g., `@company.com`)
  - By specific sender addresses? (list all program managers / delivery leads)
  - By Gmail label? (e.g., a "Project Updates" label)
  - By subject keywords? (e.g., "status update", "weekly report", "project sync")
- ☐ **How far back** should the initial scan go? (Last 7 days? 30 days? All time?)
- ☐ **Ongoing scan frequency** — every 1 hour? Every morning at 8am? Manual only?
- ☐ **Scan mode** — read-only OK? Or should the system label/archive processed emails?

### 2. Report Distribution

- ☐ **Who receives the executive report via email?**
  - Exact recipient email addresses (give a list)
  - Should the sender appear as you or a generic system address?
- ☐ **Slack workspace and channel**
  - Which workspace?
  - Which channel? (`#project-updates`? `#leadership`? New channel?)
  - What should the bot be named?
- ☐ **Report frequency**
  - Daily at a specific time? Weekly on a specific day?
  - Manual trigger only (button in dashboard)?
  - Both — scheduled + on-demand button?
- ☐ **Report scope** — all projects? Or only active/at-risk projects?

### 3. Credentials — All Required Before Production

| Credential | Where to Get It | Status |
|---|---|---|
| `credentials.json` (Gmail OAuth2) | Google Cloud Console → APIs → Gmail API → OAuth credentials | ✅ Done |
| `OPENAI_API_KEY` | platform.openai.com → API keys | ☐ Not set |
| `SLACK_BOT_TOKEN` (xoxb-...) | api.slack.com → Your Apps → Bot Token | ☐ Not set |
| `SLACK_CHANNEL` | Slack channel name (e.g., `#updates`) | ☐ Not set |
| `SENDER_EMAIL` | Gmail or SMTP address that sends reports | ☐ Not set |
| `SENDER_PASSWORD` | Gmail App Password (not your login password) | ☐ Not set |
| `REPORT_RECIPIENTS` | Comma-separated email list | ☐ Not set |

**How to get Gmail App Password:**
1. Go to myaccount.google.com → Security → 2-Step Verification → App Passwords
2. Generate a password for "Mail"
3. Paste into `.env` as `SENDER_PASSWORD`

### 4. Data Extraction Quality

- ☐ **Are these the right fields?**
  Customer, Project, Status, Progress %, Milestone, Blocker, Owner — or are there additional fields needed (e.g., due date, priority, budget)?
- ☐ **How should status be determined?**
  - AI judgment from email language? (current approach)
  - Explicit keywords only? ("status: on track")
  - Manual override always wins? (current dashboard allows this)
- ☐ **What makes a valid "blocker"?** The AI currently looks for blocking language. Does the team use specific terminology?
- ☐ **Customer name standardization** — GPT may extract "Acme Corp", "ACME", "Acme" as three different customers. Do you need a canonical customer name list?
- ☐ **OpenAI cost budget** — GPT-4 runs ~$0.01–0.05 per email. If scanning 100 emails/day, that's $1–5/day or $30–150/month. Is that acceptable? (Can switch to GPT-3.5 to reduce cost ~10x.)

### 5. Scheduling & Automation

- ☐ **Automatic report delivery?**
  - Option A: Manual only — press "Send" in the dashboard
  - Option B: Scheduled — system runs every morning at 8am, sends report automatically
  - Option C: Both — scheduled background job + manual override button
- ☐ **Email scan trigger?**
  - Manual only (run `python3 main.py` then press 2)?
  - Automatic on schedule (e.g., every 6 hours)?
- ☐ **What happens when the machine is off?** If local, scheduled jobs don't run. Needs a cloud VM or service for always-on scheduling.

### 6. Scale & Reliability

- ☐ **How many emails per day** are expected? (10? 100? 1,000?)
- ☐ **How many projects** will be tracked? (10? 50? 500?)
- ☐ **Is SQLite acceptable long-term?**
  - SQLite is fine for 1 user, <10,000 rows
  - If multiple people need simultaneous access → PostgreSQL
- ☐ **What happens if GPT extraction fails?** Currently uses regex fallback and creates an "Unknown" project. Is that acceptable?
- ☐ **Data retention** — how long should email and update history be kept? Forever? 90 days?

### 7. Deployment Environment

- ☐ **Where should this run in production?**
  - Your laptop (free, but must be on and running)
  - A cloud VM (GCP/AWS/Azure) — ~$10–30/month
  - Platform-as-a-service (Railway, Render, Fly.io) — ~$5–20/month
  - Company server/infrastructure — coordinate with IT
- ☐ **Does the dashboard need to be accessible to others?** (Or just you?)
  - If others need access → needs public URL + authentication
  - If just you → localhost is fine

---

## Answers (Fill These In Before Production)

### Gmail
- Account to scan: `_________________________________`
- Search criteria (senders/labels/keywords): `_________________________________`
- Initial scan lookback period: `_________________________________`
- Ongoing scan frequency: `_________________________________`

### Report Distribution
- Email recipient(s): `_________________________________`
- Slack workspace: `_________________________________`
- Slack channel: `_________________________________`
- Report frequency: `_________________________________`

### Credentials Status
- ☐ Gmail OAuth credentials ready? (`credentials.json` exists)
- ☐ OpenAI API key set in `.env`?
- ☐ Slack bot token ready?
- ☐ Email SMTP configured (sender email + app password)?
- ☐ Report recipient list configured?

### Data & Extraction
- Additional fields needed beyond the 7 current ones: `_________________________________`
- Customer name canonical list needed? `_________________________________`
- OpenAI model preference (gpt-4o vs gpt-3.5-turbo for cost): `_________________________________`

### Deployment
- ☐ Local laptop only
- ☐ Cloud VM (specify provider): `_________________________________`
- ☐ PaaS platform: `_________________________________`

---

## Success Criteria — How You'll Know It's Done

### MVP (Current State — Functionally Complete)
- ✅ Gmail OAuth2 connects and scans real emails
- ✅ GPT extracts customer/project/status/progress/milestone/blocker/owner from emails
- ✅ Dashboard loads with real extracted data (not mock)
- ✅ Metric cards filter the projects table when clicked
- ✅ Red flag alerts highlight stale projects (>7 days, not Completed)
- ✅ Status can be changed inline on the dashboard
- ✅ Files can be uploaded via drag-and-drop
- ✅ Emails are viewable with processed timestamps
- ✅ Executive report renders with real data
- ✅ Report HTML is professional and formatted correctly
- ✅ All code in GitHub repo (`github.com/ethannguyen0530/email-report-automation`)
- ✅ `start.sh` starts both servers with one command

### Production Ready (Remaining Gaps)
- ☐ Email report sends to real recipients via SMTP
- ☐ Slack message delivers to correct channel
- ☐ Email search criteria tuned to only pull relevant project update emails
- ☐ GPT extraction quality validated on at least 20 real emails (no Unknown/TBD spam)
- ☐ Automatic scheduling configured (if required)
- ☐ All credentials filled in `.env` (OpenAI, Slack, SMTP)
- ☐ System tested end-to-end: email arrives → extracted → appears on dashboard → report sent
- ☐ Deployed to environment accessible to stakeholders (if needed)
- ☐ `.env.example` updated with all required keys

---

## Next Steps — Ordered by Priority

1. **Answer the critical questions above** — especially Gmail search criteria and report recipients ← DO THIS FIRST
2. **Set credentials in `.env`**:
   - `OPENAI_API_KEY` — required for extraction to work
   - `SLACK_BOT_TOKEN` + `SLACK_CHANNEL` — required for Slack delivery
   - `SENDER_EMAIL` + `SENDER_PASSWORD` + `REPORT_RECIPIENTS` — required for email delivery
3. **Tune email search criteria** — update `GMAIL_SEARCH_QUERY` in `.env` to target only project update emails from known senders
4. **Validate extraction quality** — run `python3 main.py` → option 2 on 20–30 real emails, review the dashboard for bad extractions, adjust GPT prompt if needed
5. **Test full send pipeline** — click "Send via Email + Slack" in the Report tab, verify delivery
6. **Add automatic scheduling** (if required) — ~30 min with APScheduler
7. **Cloud deployment** (if required) — ~2–4 hours to containerize and deploy to Railway or GCP Cloud Run
8. **Add user auth** (if others need dashboard access) — ~4 hours with Flask-Login

---

## File Structure Reference

```
email-report-automation/
├── main.py                    # CLI entry point — scan emails, view menu
├── config.py                  # Loads all .env variables
├── start.sh                   # One-command startup (Flask + React)
├── requirements.txt           # Python dependencies
├── .env                       # Credentials (not committed)
├── .env.example               # Template for .env
│
├── database/
│   └── schema.py              # DatabaseManager — all SQL queries
│
├── services/
│   ├── gmail_service.py       # Gmail OAuth2, email fetch
│   ├── extraction_service.py  # GPT + regex extraction
│   ├── report_service.py      # HTML report generation + SMTP send
│   └── slack_service.py       # Slack Block Kit delivery
│
├── dashboard/
│   └── app.py                 # Flask REST API (all /api/* routes)
│
├── frontend/                  # React + Vite (port 3000)
│   ├── src/
│   │   ├── App.jsx            # Router + layout
│   │   ├── components/
│   │   │   ├── Sidebar.jsx    # Nav: Overview, Emails, Report, Files
│   │   │   ├── MetricCard.jsx # Clickable stat card with filter state
│   │   │   ├── StatusSelect.jsx # Inline status dropdown (PATCH)
│   │   │   └── ProgressBar.jsx
│   │   └── pages/
│   │       ├── Dashboard.jsx  # Overview with filters + red flags
│   │       ├── Emails.jsx     # Inbox view with timestamps
│   │       ├── Report.jsx     # Report preview + send button
│   │       ├── Uploads.jsx    # Drag-and-drop file upload
│   │       ├── ProjectDetail.jsx
│   │       └── CustomerDetail.jsx
│   └── vite.config.js         # Proxies /api to localhost:5001
│
└── uploads/                   # Uploaded files storage
```

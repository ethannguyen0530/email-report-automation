# Repo Coverage & Open Questions

**Project:** Email Report Automation System  
**Last Updated:** June 23, 2026  
**Author:** Ethan Nguyen  
**Repo:** github.com/ethannguyen0530/email-report-automation

---

## What This Repo Does — MVP Complete ✅

### ✅ Gmail Integration (OAuth2)

- OAuth2 authentication via `credentials.json` + `token.pickle` (browser prompt on first run, silent after)
- Scans Gmail for emails using a configurable search query (`GMAIL_QUERY` in `.env`)
- Configurable result limit (`GMAIL_MAX_RESULTS`)
- Recursive multipart body extraction — handles nested `multipart/alternative` and `multipart/mixed` structures
- **Email attachment extraction** — downloads attachment bytes from Gmail API; extracts text from PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx), CSV, TXT via shared `services/file_extractor.py`
- Deduplication: `gmail_id TEXT UNIQUE` in DB — IntegrityError on duplicate silently skips
- Stores raw emails in SQLite `emails` table with sender, subject, body, received timestamp, processed flag, flagged flag

### ✅ AI-Powered Data Extraction (OpenAI GPT-3.5)

- Each email body + attachment text (up to 3000 chars combined) sent to GPT with a strict JSON-only prompt
- Extracts per email:
  - **Customer name**
  - **Project name**
  - **Status** — On Track / At Risk / Delayed / Completed / In Progress
  - **Progress %** — 0–100
  - **Milestone** — what was completed
  - **Blocker** — what is blocking progress
  - **Owner** — who sent the update
  - **Summary** — one-sentence current status
  - **is_project_related** — boolean gate
  - **confidence** — 0–100 confidence score
- Confidence gating: `confidence >= 40 AND is_project_related` → stored; `confidence < 60` → also flagged
- **Regex fallback** if GPT fails or returns malformed JSON
- Update summary stored as: `extracted.get('summary') or extracted.get('milestone') or email subject`

### ✅ SQLite Database (5 tables)

| Table | Contents |
|---|---|
| `customers` | Unique customer names |
| `projects` | Project per customer — status, progress, owner, created_at |
| `updates` | Update records — summary, milestone, blocker, owner, date, gmail_id, confidence |
| `emails` | Raw email archive — gmail_id (unique), sender, subject, body, received_at, processed flag, flagged flag |
| `recipients` | Report recipient list — email, name |

Key queries:
- `get_all_projects()` — LEFT JOIN on updates for `MAX(created_at)` as `last_updated`
- `get_executive_summary()` — aggregates metrics, `accomplishments_rich` (with gmail_id backlinks), `blockers_rich` (with gmail_id), project notes (blocker > milestone > summary priority)
- `get_project_health_scores()` — computes 0–100 per project with `reasons` array; portfolio average
- `get_stale_customers(days=7)` — customers who previously had updates but went silent; excludes never-active customers
- `get_or_create_project()` — creates project on first email only; subsequent scans only update `owner` if non-placeholder; **never overwrites user-set status or progress**
- `mark_email_processed()` — sets `processed=1`, `processed_at=now`

### ✅ Portfolio Health Scores

- Formula: start at 100, deduct:
  - −35 if status is Delayed
  - −20 if status is At Risk
  - −25 if active blocker in updates table
  - −20 if no update in 14+ days
  - −10 if no update in 7–14 days
  - −10 if progress < 20% (and not Completed)
- Portfolio score = average of all project scores
- Scores computed on-read (not cached) — always reflect current DB state
- `last_updated` from `MAX(update_date)` — moves forward automatically with each new email scan
- Scores exposed via `GET /api/health`

### ✅ React Dashboard (Vite, served by Flask in production)

**Overview Page**
- 5 clickable metric cards: Total, On Track, At Risk, Delayed, Completed — filter projects table
- Projects table: Project, Customer, Status (inline editable), Progress bar, Owner, Last Updated, Health score (clickable)
- **Portfolio health score circle** — clickable → opens portfolio breakdown modal
  - Lists all projects with scores; each project score circle clickable → per-project breakdown
  - Prev/Next navigation between projects
  - Back button to return to portfolio list
  - "Score reflects data as of [date]" timestamp
- **Per-project health circles in table** — clickable → same per-project breakdown modal
- **Accomplishments panel** — real summaries, each row clickable → source email modal (AI summary, sender, subject, date, full body)
- **Open Blockers panel** — same click-through to source email
- Red flag alerts (⚑) for projects not updated in 7+ days
- Smart Alerts banner — stale customers who went quiet + flagged email count
- Real-time updates via Server-Sent Events — dashboard auto-refreshes when scan completes with new emails; live purple dot indicator
- **Status change full sync** — changing a project status via dropdown immediately syncs: metric cards, health scores, portfolio score, Smart Alerts

**Emails Page**
- Inbox of all scanned emails with subject, sender, received + processed timestamps
- Customer filter chips — filter by customer; "All" resets
- Click email to open detail pane with full body
- Duplicate-row bug fixed — filter chips and all-emails view are mutually exclusive

**Customers Page**
- All customers with project count, last-updated date, health score (click for breakdown)
- Add customer button (form + `POST /api/customers`)
- Delete customer button (`DELETE /api/customers/:id` with cascade)
- New customers auto-detected from email scans

**Executive Report Page**
- Live preview of the full HTML executive report in an iframe
- "Send via Email + Slack" button — `POST /api/send-report`

**Files Page**
- Drag-and-drop upload zone
- Supported: PDF, TXT, DOC, DOCX, CSV, XLSX, PPTX (`.xls` explicitly rejected — openpyxl doesn't support legacy BIFF)
- Upload → `POST /api/upload` → `POST /api/process-file` → same GPT extraction pipeline as email scan → dedup via `file:{filename}` synthetic ID → SSE event `file_processed` updates UI
- Shows extraction result: customer, project, confidence, ✓ Added to dashboard / Duplicate / Error

**Settings Page**
- Manage report recipients (add/remove) from the UI
- Stored in `recipients` DB table
- Falls back to `.env REPORT_RECIPIENTS` if table is empty

### ✅ Flask REST API (port 5001)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/summary` | Metrics, accomplishments_rich, blockers_rich, all projects |
| GET | `/api/projects` | All projects |
| GET | `/api/projects/:id` | Single project + update history |
| PATCH | `/api/projects/:id` | Update status / progress / owner |
| GET | `/api/customers` | All customers |
| POST | `/api/customers` | Add customer |
| DELETE | `/api/customers/:id` | Delete + cascade |
| GET | `/api/customers/:id` | Customer + their projects |
| GET | `/api/emails` | All emails with timestamps |
| GET | `/api/emails?customer=` | Customer-filtered email list |
| GET | `/api/email-detail/:id` | Full email for source-link click-through |
| GET | `/api/health` | Portfolio + per-project health scores with reasons |
| GET | `/api/alerts` | Stale customers + flagged email count |
| GET | `/api/email-stats` | All-time, weekly, monthly, per-customer counts |
| GET | `/api/report` | Executive report as rendered HTML |
| POST | `/api/send-report` | Send report via SMTP + Slack |
| POST | `/api/scan-now` | Trigger Gmail scan in background thread |
| POST | `/api/upload` | Upload file |
| POST | `/api/process-file` | AI extraction on uploaded file |
| GET | `/api/uploads/:filename` | Serve uploaded file |
| GET | `/api/recipients` | List report recipients |
| POST | `/api/recipients` | Add recipient |
| DELETE | `/api/recipients/:id` | Remove recipient |
| GET | `/api/stream` | SSE — real-time scan completion events |

### ✅ Executive Report Generation

Executive brief designed for 60-second skim:
- 1-sentence AI intro (GPT, max 25 words, temperature 0.3)
- Metric strip: Total / On Track / At Risk / Delayed / Completed
- Customer Snapshot table with traffic lights per customer: Action Required / Monitor Closely / On Track
- All Projects table with inline blocker text (60-char truncation)
- Wins and Blockers sections
- No essay paragraphs, no filler

Dual delivery: SMTP email (HTML) + Slack (Block Kit formatted summary)

### ✅ Automatic Scheduling (APScheduler)

- `run_email_scan()` fires every `SCAN_INTERVAL_MINUTES` (default 15)
- `run_report_send()` fires every `REPORT_SEND_HOURS` (default 24)
- Both start when gunicorn imports `dashboard.app`
- Guard against double-start in Flask debug reloader (`WERKZEUG_RUN_MAIN` check)
- On-demand scan available via `POST /api/scan-now` or `python3 main.py → option 2`

### ✅ macOS Background Service (launchd)

- `bash install_service.sh` — one command installs everything
- `KeepAlive=true` — restarts on crash; `ThrottleInterval=10` — prevents spin loop
- Logs to `logs/server.log`, `logs/access.log`, `logs/error.log`
- **No terminal needed at runtime**

### ✅ Shared File Extraction Utility

- `services/file_extractor.py` — single source of truth for all file-to-text conversion
- Used by both the email attachment pipeline (`gmail_service.py`) and the file upload pipeline (`app.py`)
- Handles: PDF (pdfplumber), Word (.docx, python-docx), Excel (.xlsx, openpyxl), PowerPoint (.pptx, python-pptx), CSV/TXT/MD
- Bug fixes propagate to both pipelines automatically

---

## What's NOT in This Repo Yet ❌

| Feature | Status | Priority |
|---|---|---|
| **OpenAI API key** | `.env` var exists, no key set yet | Required for AI extraction to work |
| **Slack bot token** | `.env` var exists, no token set yet | Required for Slack delivery |
| **SMTP credentials** | `.env` vars exist, not configured | Required for email delivery |
| **Email search tuning** | `GMAIL_QUERY` is a broad default — may pull irrelevant emails | High — needs tuning to real senders/keywords |
| **Cloud deployment** | Local only — dashboard not accessible from outside this Mac | High if others need access |
| **User authentication** | No login — anyone on same network can access dashboard | High if dashboard is public-facing |
| **Duplicate project detection** | GPT may extract "Cigna Migration" and "Cigna migration" as different projects | Medium — fuzzy match on project + customer |
| **Multi-Gmail account support** | Single OAuth account per deployment | Low |
| **PostgreSQL option** | SQLite fine for 1 user / <10k rows; not for concurrent multi-user | Low unless scaling |
| **Charts / visualizations** | Table and card layout only — no trend charts | Low |
| **Test suite** | No automated tests | Medium for production confidence |
| **Pagination** | All rows loaded at once — fine for <200 projects | Low |
| **Video processing** | Video files not extractable (no speech-to-text integration) | Low |

---

## Critical Questions — Answer Before Production

### 1. Gmail

- ☐ **Which Gmail account** scans project update emails?
- ☐ **Search criteria** — how to identify the right emails?
  - By sender domain? (e.g., `from:@autonomize.ai`)
  - By specific senders? (list all program managers by email)
  - By Gmail label?
  - By subject keywords? (e.g., `subject:"weekly update" OR subject:"project status"`)
- ☐ **How far back** should the initial scan go? (7 days? 30 days? All time?)
- ☐ **Ongoing frequency** — 15 minutes is currently configured; is that right?

### 2. Report Distribution

- ☐ **Exact email recipients** — who receives the executive report?
- ☐ **Slack workspace and channel** — which workspace? Which channel?
- ☐ **Report scope** — all projects, or only At Risk + Delayed?

### 3. Credentials Needed

| Credential | How to Get | Current Status |
|---|---|---|
| `credentials.json` (Gmail OAuth2) | Google Cloud Console → Gmail API → OAuth client | ✅ File exists |
| `OPENAI_API_KEY` | platform.openai.com → API Keys | ☐ Not set |
| `SLACK_BOT_TOKEN` | api.slack.com → Your Apps → Bot Token (xoxb-...) | ☐ Not set |
| `SLACK_CHANNEL` | Slack channel name | ☐ Not set |
| `SENDER_EMAIL` | Gmail address that sends reports | ☐ Not set |
| `SENDER_PASSWORD` | Gmail App Password | ☐ Not set |
| Report recipients | Add in Settings tab (or `REPORT_RECIPIENTS` in `.env`) | ☐ Not configured |

### 4. Data Extraction Quality

- ☐ **Are the extracted fields correct?** (Customer, Project, Status, Progress %, Milestone, Blocker, Owner, Summary)
- ☐ **Customer name canonicalization** — GPT may extract "Cigna", "CIGNA Corp", "Cigna Health" as different customers. Is a canonical name list needed?
- ☐ **OpenAI cost** — GPT-3.5 is ~$0.001–0.002 per email. Acceptable?

### 5. Deployment Environment

- ☐ **Who needs dashboard access?**
  - Just you → `localhost:5001` is fine
  - Others on same network → expose port, add IP restriction
  - Remote stakeholders → needs cloud deployment + public URL + auth
- ☐ **Cloud deployment needed?** Options: Railway, Render, GCP Cloud Run (~2–4h, ~$5–20/month)
- ☐ **Authentication needed?** If others access the dashboard, a login screen is required

### 6. Scale

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
- Scan frequency (currently 15 min): `_________________________________`

### Report Distribution
- Email recipients: `_________________________________`
- Slack workspace: `_________________________________`
- Slack channel: `_________________________________`

### Credentials Checklist
- ☐ `credentials.json` in project root
- ☐ `OPENAI_API_KEY` set in `.env`
- ☐ `SLACK_BOT_TOKEN` set in `.env`
- ☐ `SLACK_CHANNEL` set in `.env`
- ☐ `SENDER_EMAIL` + `SENDER_PASSWORD` set in `.env`
- ☐ Recipients added in Settings tab (or `REPORT_RECIPIENTS` in `.env`)
- ☐ `GMAIL_QUERY` tuned to real senders/keywords

### Deployment
- ☐ Local laptop only (current)
- ☐ Cloud VM — provider: `_________________________________`
- ☐ PaaS — platform: `_________________________________`

---

## Success Criteria

### MVP — Functionally Complete ✅
- ✅ Gmail OAuth2 connects and scans emails + attachments
- ✅ GPT extracts structured data from email body + attachment text
- ✅ Dashboard loads with real extracted data
- ✅ Metric cards filter projects table by status when clicked
- ✅ Red flag alerts highlight stale projects (>7 days, excludes Completed)
- ✅ Status editable inline; all health scores sync on change
- ✅ Portfolio health score with full breakdown modal (prev/next navigation)
- ✅ Accomplishments and blockers link back to source email
- ✅ Files uploadable and AI-processed identically to email scans
- ✅ Executive report auto-generated and sent daily (email + Slack)
- ✅ Customer management (auto-detect + manual add/delete + health scores)
- ✅ Report recipients managed from Settings tab
- ✅ Real-time dashboard updates via Server-Sent Events
- ✅ Service auto-starts on login, restarts on crash, no open terminal needed
- ✅ Zero duplicates enforced at DB level
- ✅ User-set project status never overwritten by email scans
- ✅ All code in GitHub (`github.com/ethannguyen0530/email-report-automation`)

### Production Ready — Remaining Gaps
- ☐ All credentials filled in `.env` (OpenAI, Slack, SMTP)
- ☐ `GMAIL_QUERY` tuned to target only real project update emails
- ☐ Extraction quality validated on 20+ real emails
- ☐ Report sends successfully to real email recipients via SMTP
- ☐ Slack message delivers to correct workspace and channel
- ☐ End-to-end test: email arrives → extracted → appears on dashboard → report sent
- ☐ Deployment decision made (local vs cloud) based on who needs access

---

## Next Steps — In Priority Order

1. **Set OpenAI key in `.env`** — required for everything to work
2. **Answer Gmail criteria questions** — which account, which senders, which subjects
3. **Tune `GMAIL_QUERY`** — restrict to real project update senders
4. **Authorize Gmail** — `python3 main.py → option 2 → browser auth → token.pickle saved`
5. **Add Slack credentials** in `.env`
6. **Configure SMTP** and add recipients in Settings tab
7. **Validate extraction quality** — run on 20–30 real emails, check dashboard
8. **Test report delivery** — click "Send via Email + Slack", confirm receipt
9. **Decide deployment** — if others need access, deploy to cloud

---

## File Structure Reference

```
email-report-automation/
├── main.py                     CLI entry point — scan, report, seed
├── config.py                   .env variable loading with defaults
├── start.sh                    Dev mode (Flask dev + Vite HMR on :3000)
├── run.sh                      Production startup (gunicorn on :5001)
├── install_service.sh          macOS launchd service installer
├── requirements.txt            Python deps (gunicorn, apscheduler, flask, openai, pdfplumber, etc.)
├── credentials.json            Gmail OAuth creds (not committed to git)
├── token.pickle                Gmail access token (auto-created on first auth, not committed)
├── .env                        Credentials (not committed)
├── .env.example                Template for .env
│
├── database/schema.py          DatabaseManager — init, queries, health scores, executive summary
│
├── services/
│   ├── gmail_service.py        OAuth2 auth + recursive email body + attachment extraction
│   ├── file_extractor.py       Shared PDF/Word/Excel/PowerPoint text extraction utility
│   ├── extraction_service.py   GPT prompt + regex fallback
│   ├── report_service.py       Executive HTML report generation + SMTP delivery
│   └── slack_service.py        Slack Block Kit formatting + delivery
│
├── dashboard/app.py            Flask app — all routes, APScheduler, React serving
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             Page router
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   Overview — health modals, email source modal, status sync
│   │   │   ├── Emails.jsx      Inbox with customer filter chips
│   │   │   ├── Customers.jsx   Customer list + health scores + add/delete
│   │   │   ├── Report.jsx      Report iframe + send button
│   │   │   ├── Uploads.jsx     Drag-and-drop upload with AI extraction
│   │   │   ├── Settings.jsx    Recipient management UI
│   │   │   └── ProjectDetail.jsx  Per-project update history
│   │   └── components/
│   │       ├── Sidebar.jsx     Navigation
│   │       ├── MetricCard.jsx  Clickable stat card
│   │       ├── StatusSelect.jsx Inline dropdown (PATCH)
│   │       └── StatusBadge.jsx Color-coded pill
│   ├── dist/                   Built React app (served by Flask)
│   └── vite.config.js          Proxies /api/* to :5001 in dev
│
├── logs/
│   ├── server.log
│   ├── access.log
│   └── error.log
│
└── uploads/                    Uploaded files
```

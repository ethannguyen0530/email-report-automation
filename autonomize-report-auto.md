# autonomize-report-auto

**Project:** Email Report Automation System  
**Repo:** github.com/ethannguyen0530/email-report-automation  
**Stack:** Python Flask + React (Vite) + SQLite + OpenAI GPT-3.5 + Gmail OAuth2 + Slack

---

## Session 2 — June 23, 2026

### 1. Executive Report — Rebuilt for Executives

**Problem:** Report was an essay. Executives need to skim it in 60 seconds.  
**Fix:** Complete rewrite of `report_service.py`:
- 1-sentence AI intro (GPT, max 25 words, temperature 0.3)
- Metric strip: Total / On Track / At Risk / Delayed / Completed
- Customer Snapshot table with traffic-light signals per customer: Action Required / Monitor Closely / On Track
- All Projects table with inline blocker text (truncated to 60 chars)
- Wins + Blockers sections
- No more essay paragraphs, no redundant sections

**Files changed:** `services/report_service.py`

---

### 2. Scheduled Report Delivery (was a listed gap — now complete)

**Problem:** Report could only be sent manually by clicking a button.  
**Fix:** Added `run_report_send()` as a second APScheduler job alongside the email scan. Controlled by `REPORT_SEND_HOURS` in `.env` (default `24` = daily). Sends via SMTP email + Slack automatically. No human action needed.

**Files changed:** `dashboard/app.py`, `config.py`, `.env`

---

### 3. Real-Time Dashboard via Server-Sent Events

**Problem:** Dashboard required a manual page refresh to see new data.  
**Fix:** Added `/api/stream` SSE endpoint. Dashboard holds a persistent connection. When a scan completes, the server broadcasts `scan_complete` with `{ new_emails, total, flagged }`. If `new_emails > 0`, the dashboard re-fetches all data automatically. Live purple dot indicator in the header.

**Files changed:** `dashboard/app.py`, `frontend/src/pages/Dashboard.jsx`

---

### 4. Portfolio Health Score + Click-Through Breakdown

**Problem:** No way to see a score or know WHY a project was healthy or at risk.  
**Fix:**
- `get_project_health_scores()` in `schema.py` computes a 0-100 score per project. Formula: start at 100 then deduct: Delayed (−35), At Risk (−20), active blocker (−25), no update in 14d (−20), no update in 7d (−10), progress <20% (−10)
- Portfolio score = average of all project scores
- Score circle on the Overview page is clickable → opens portfolio breakdown modal listing all projects
- Each project's score circle in the modal is clickable → opens per-project breakdown with reason rows (factor, impact, ok/warn/bad)
- Per-project health circles in the projects table are also clickable → same breakdown modal
- Modal has prev/next navigation between projects + back-to-list button
- All breakdowns show "Score reflects data as of [date]" — timestamp from `MAX(update_date)` in DB

**Files changed:** `database/schema.py`, `frontend/src/pages/Dashboard.jsx`, `frontend/src/pages/Customers.jsx`

---

### 5. Accomplishments / Blockers → Click to Source Email

**Problem:** Accomplishments and blockers were text-only with no way to trace them back to the original email.  
**Fix:** `get_executive_summary()` now returns `accomplishments_rich` and `blockers_rich` arrays — each item has `{ text, gmail_id }`. Each row in the dashboard cards is clickable. Clicking opens an Email Source Modal with:
- AI summary (1-2 sentences)
- Sender, subject, date
- Full scrollable email body

**Files changed:** `database/schema.py`, `frontend/src/pages/Dashboard.jsx`, `dashboard/app.py`

---

### 6. Email Attachment Processing

**Problem:** Attachments in emails (Excel reports, PowerPoint decks, Word docs) were completely ignored.  
**Fix:**
- `gmail_service.py` downloads attachment bytes from Gmail API and runs them through a shared extraction utility
- `services/file_extractor.py` (new) — handles PDF (pdfplumber), Word (.docx, python-docx), Excel (.xlsx, openpyxl), PowerPoint (.pptx, python-pptx), CSV/TXT/MD
- Extracted text appended to email body as `--- ATTACHMENTS ---` block before GPT extraction
- AI sees full email + all documents as one context

**Files new/changed:** `services/file_extractor.py` (new), `services/gmail_service.py`

---

### 7. File Upload → AI Extraction Pipeline

**Problem:** Files tab stored uploads but did nothing with them — they never entered the dashboard.  
**Fix:** Uploading a file now triggers the same extraction pipeline as email scanning:
- `/api/process-file` reads bytes, calls `file_extractor.extract_text_from_bytes()`, sends to GPT
- Deduplication via synthetic ID `file:{filename}` — same file can't be processed twice
- Customer / project / update rows created in DB identically to email scan
- SSE event `file_processed` broadcasts result back to the upload UI
- Supported: PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx), CSV, TXT
- `.xls` explicitly rejected (openpyxl doesn't support legacy BIFF format)

**Files changed:** `dashboard/app.py`, `frontend/src/pages/Uploads.jsx`

---

### 8. Manual Status Change → Full UI Sync

**Problem:** When a user changed a project's status via the dropdown, health scores, metric counts, and the portfolio score didn't update to reflect the change.  
**Fix:** `updateStatus()` in Dashboard.jsx now:
1. Applies an optimistic local update immediately (badge flips instantly)
2. Fires parallel re-fetches of `/api/summary`, `/api/health`, `/api/alerts`
3. Updates all derived state: metric card counts, health scores, portfolio score, Smart Alerts
4. Version counter prevents a stale re-fetch chain from overwriting a newer change
The manual status override is also protected at the DB layer — `get_or_create_project()` never overwrites user-set status from subsequent email scans.

**Files changed:** `frontend/src/pages/Dashboard.jsx`, `database/schema.py`

---

### 9. Customer Management (Add / Auto-Detect / Delete)

**Problem:** Customers could only appear if an email mentioned them — no way to add or remove manually.  
**Fix:**
- New customers extracted from emails are automatically added to DB (was already true but now surfaced in UI)
- `POST /api/customers` — add customer by name
- `DELETE /api/customers/:id` — delete customer + cascade (projects + updates)
- Customers tab shows all customers with their project count and health score
- Health score click-through per customer (same breakdown modal as dashboard)

**Files changed:** `dashboard/app.py`, `database/schema.py`, `frontend/src/pages/Customers.jsx`

---

### 10. Report Recipients — Settings Tab

**Problem:** Recipients were hardcoded in `.env` — Ujjwal couldn't change them without editing a file.  
**Fix:**
- `recipients` table in SQLite stores email + name
- `GET/POST/DELETE /api/recipients` endpoints
- Settings tab in the UI to add/remove recipients with a form
- Report sending falls back to `.env` `REPORT_RECIPIENTS` only if the DB table is empty

**Files changed:** `dashboard/app.py`, `database/schema.py`, `frontend/src/pages/Settings.jsx`

---

### 11. Smart Alerts — Stale Customer Detection

**Problem:** No automated signal when a customer went quiet.  
**Fix:** `get_stale_customers()` queries which customers had updates previously but nothing in the last 7 days. Appears in the Smart Alerts banner on the Overview dashboard. Customers who have never had any updates (recently added, never emailed) are excluded to avoid false alerts.

**Files changed:** `database/schema.py`, `dashboard/app.py`, `frontend/src/pages/Dashboard.jsx`

---

### 12. Email Filtering by Customer

**Problem:** Emails tab showed all emails with no way to filter by customer.  
**Fix:** Customer filter chips above the email list. Clicking a chip queries `/api/emails?customer=Name` which JOINs emails → updates → projects → customers. "All" chip clears the filter. Active chip highlighted in purple.

**Files changed:** `frontend/src/pages/Emails.jsx`, `dashboard/app.py`

---

### 13. New Pages

| Page | What's New |
|---|---|
| `Customers.jsx` | Customer list with per-customer health scores and add/delete controls |
| `ProjectDetail.jsx` | Per-project update history timeline |
| `Settings.jsx` | Manage report recipients from the UI |

---

### 14. New API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Portfolio score + per-project health scores with reasons |
| GET | `/api/alerts` | Stale customers + flagged email count |
| GET | `/api/email-stats` | All-time, weekly, monthly, per-customer email counts |
| GET | `/api/email-detail/:id` | Source email for click-through modal |
| GET | `/api/emails?customer=` | Customer-filtered email list |
| POST | `/api/customers` | Add customer |
| DELETE | `/api/customers/:id` | Delete customer + cascade |
| GET | `/api/recipients` | List report recipients |
| POST | `/api/recipients` | Add recipient |
| DELETE | `/api/recipients/:id` | Remove recipient |
| POST | `/api/process-file` | Trigger AI extraction on an uploaded file |
| GET | `/api/stream` | SSE endpoint — real-time scan completion events |

---

### 15. QA Pass — 12 Bugs Found and Fixed

Full code audit surfaced and fixed:

| # | File | Bug | Fix |
|---|---|---|---|
| 1 | `Emails.jsx` | `normalEmails.map` rendered unconditionally AND `activeCustomer && emails.map` also rendered — duplicate rows when customer filter active | Wrapped `normalEmails.map` in `{!activeCustomer && ...}` |
| 2 | `Dashboard.jsx` | `isLast` for accomplishments computed from `summary.accomplishments.length` but iterated `accomplishments_rich` — wrong border placement | Fixed to use actual iterated array length |
| 3 | `Dashboard.jsx` | Same `isLast` mismatch for blockers | Same fix |
| 4 | `Dashboard.jsx` | `updateStatus` re-fetched summary/health but never called `setProjects(sumData.projects)` | Added `setProjects` call after re-fetch |
| 5 | `schema.py` | `get_or_create_project` unconditionally overwrote `status` and `progress_percent` on every email scan | Status/progress now only set on first creation; owner-only updates thereafter |
| 6 | `schema.py` | `get_stale_customers` HAVING `last_update IS NULL` flagged never-active customers as stale | Changed to `last_update IS NOT NULL AND last_update < ...` |
| 7 | `app.py` | `ALLOWED_EXTENSIONS` included image types (png, jpg, gif, webp) that produce no text | Removed image types; added xlsx, pptx |
| 8 | `app.py` + `Uploads.jsx` | `.xls` accepted but `openpyxl` silently fails on legacy BIFF format — showed false "✓ Added to dashboard" | Removed `.xls` from all allow-lists |
| 9 | `Dashboard.jsx` | `openEmailModal` had no request cancellation — rapid row clicks showed wrong email | Added `AbortController`; each new click cancels in-flight request |
| 10 | `Dashboard.jsx` | Rapid status changes caused stale `Promise.all` chain to overwrite newer state | Added `_updateVer` ref counter — stale chains are discarded |
| 11 | `Dashboard.jsx` | `allProjects.findIndex` returns `-1` when health refreshes during modal — `hasNext` incorrectly enabled, position showed "0 of N" | Added `found = currentIdx > -1` guard |
| 12 | `app.py` + `gmail_service.py` | xlsx/pptx extraction logic duplicated in two places — fixes in one wouldn't reach the other | Extracted to shared `services/file_extractor.py` |

---

## Final File State — After Session 2

```
email-report-automation/
├── main.py
├── config.py                     REPORT_SEND_HOURS added; SCAN_INTERVAL_MINUTES=15
├── start.sh / run.sh / install_service.sh
├── requirements.txt              + pdfplumber, python-docx, openpyxl, python-pptx
├── .env                          REPORT_SEND_HOURS=24, SCAN_INTERVAL_MINUTES=15
├── autonomize-report-auto.md     This file
├── README.md                     Updated — new pages, endpoints, architecture
├── HANDOFF.md                    Updated — most gaps now filled
├── REPO_COVERAGE_AND_QUESTIONS.md   Updated — coverage map current
│
├── database/schema.py            Health scores, stale customers fix, get_or_create fix,
│                                 accomplishments_rich/blockers_rich, email_sources_count
│
├── services/
│   ├── gmail_service.py          Attachment extraction, uses shared file_extractor
│   ├── file_extractor.py         NEW — shared PDF/Word/Excel/PowerPoint text extraction
│   ├── extraction_service.py     Unchanged
│   ├── report_service.py         Full executive-brief rewrite
│   └── slack_service.py          Unchanged
│
├── dashboard/app.py              /api/health, /api/alerts, /api/email-stats,
│                                 /api/email-detail, /api/stream (SSE), /api/process-file,
│                                 /api/customers POST/DELETE, /api/recipients CRUD,
│                                 run_report_send scheduled job
│
└── frontend/src/
    ├── App.jsx                   + Customers, Settings, ProjectDetail routes
    ├── pages/
    │   ├── Dashboard.jsx         Health modal + project breakdown + prev/next nav,
    │   │                         email source modal, updateStatus full sync,
    │   │                         AbortController, version-guarded re-fetch
    │   ├── Emails.jsx            Customer filter chips, duplicate-render fix
    │   ├── Customers.jsx         Customer list + health scores + add/delete
    │   ├── Settings.jsx          Recipient management
    │   ├── ProjectDetail.jsx     Per-project update history
    │   ├── Report.jsx            Unchanged
    │   └── Uploads.jsx           AI extraction pipeline, xls removed
    └── components/
        ├── Sidebar.jsx           + Customers, Settings nav items
        ├── StatusSelect.jsx      Unchanged
        ├── StatusBadge.jsx       Unchanged
        ├── MetricCard.jsx        Unchanged
        └── ProgressBar.jsx       Unchanged
```

---

## Current Status — After Session 2

**Service:** Running permanently at `http://localhost:5001` via launchd  
**Auto-scan:** Every 15 minutes (`SCAN_INTERVAL_MINUTES=15`)  
**Auto-report:** Every 24 hours (`REPORT_SEND_HOURS=24`) — sends email + Slack  
**GitHub:** Fully up to date  
**Terminal needed:** No

**Still blocked on (Ujjwal to provide):**
- `OPENAI_API_KEY` — required for AI extraction
- `SLACK_BOT_TOKEN` + `SLACK_CHANNEL` — required for Slack delivery
- `SENDER_EMAIL` + `SENDER_PASSWORD` + `REPORT_RECIPIENTS` (or set in Settings tab)
- Gmail search query tuned to real project update senders

---

## Session 1 — June 22, 2026

### 1. Dashboard — Metric Card Filters
Metric cards (Total, On Track, At Risk, Delayed, Completed) are clickable and filter the projects table. Active card shows glow + accent bar. "Clear filter ×" button resets.

### 2. Dashboard — Red Flag Alerts
Projects with no update in 7+ days get a red ⚑ flag, red-tinted row, red "Last Updated" text. Completed projects exempt.

### 3. Dashboard — Last Updated Column
Human-readable relative timestamps (Today, Yesterday, 3d ago). Backed by `MAX(u.created_at)` JOIN in `get_all_projects()`.

### 4. Executive Report Page
Report.jsx — iframe preview + "Send via Email + Slack" button calling `POST /api/send-report`.

### 5. Executive Report — Professional HTML
Gradient header, metric cards, accomplishments/blockers panels, full projects table with status pills and progress bars.

### 6. Executive Report — Data Quality
Accomplishments and blockers deduplicated. Unknown/TBD/empty text filtered out. No more filler content.

### 7. Emails Page — Processed Timestamps
Received and processed timestamps per email. Processed shown in green.

### 8. Gmail Body Extraction Fix
Recursive `_extract_text()` handles nested `multipart/alternative`. Three-pass priority: plain text → nested multipart → HTML fallback.

### 9. GPT Extraction — Summary Field + 3000 Char Body
Added `summary` field to prompt. Body limit raised from 1000 to 3000 chars. `In Progress` added to valid status list.

### 10. Update Summary Storage Fix
Scheduler and scan now store: `extracted.get('summary') or extracted.get('milestone') or email subject`. Eliminates "Update from:" filler.

### 11. CustomerDetail Dark Theme Fix
Rewritten using CSS variables — no more hardcoded white/light colors.

### 12. Automated Email Scanning (APScheduler)
`BackgroundScheduler` added. `SCAN_INTERVAL_MINUTES` in `.env` controls frequency.

### 13. Production Service — Gunicorn + macOS launchd
`install_service.sh` one-command installer. `KeepAlive=true` restarts on crash.

### 14. Config Cleanup
`FLASK_DEBUG=False` default. `FLASK_PORT=5001`. `.env.example` updated.

### 15. Full Code Audit — 5 Bugs Fixed
`processed_at` column added. Dead code removed. Email processing timestamps corrected.

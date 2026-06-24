# autonomize-report-auto

**Project:** Email Report Automation System  
**Repo:** github.com/ethannguyen0530/email-report-automation  
**Stack:** Python Flask + React (Vite) + SQLite + OpenAI GPT-3.5 + Gmail OAuth2 + Slack

---

## Session 3 — June 23, 2026

### 1. Email Sending — Wired Up and Tested

**Problem:** Report email was not sending (`email: false` in API response).  
**Root cause:** `SENDER_EMAIL`, `SENDER_PASSWORD`, `REPORT_RECIPIENTS` were all blank in `.env`.  
**Fix:** Filled in `.env` with Ethan's test credentials for validation:
- `SENDER_EMAIL=en2569@nyu.edu`
- `SENDER_PASSWORD=meyvkdmpdegevavy` (NYU Gmail App Password — 16 chars, no spaces)
- `REPORT_RECIPIENTS=ethann0530@gmail.com,ujjwal.rajbhandari@autonomize.ai`

**IMPORTANT:** These are Ethan's temporary test credentials. Before go-live, Ujjwal must replace `SENDER_EMAIL` and `SENDER_PASSWORD` with his own Gmail + App Password (or use Settings tab for recipients).

**Files changed:** `.env`

---

### 2. Email HTML — Rebuilt for Gmail

**Problem:** Email rendered with broken fonts and broken layout in Gmail ("all fucked up").  
**Root cause:** Gmail strips external `<link>` tags (Google Fonts) and ignores `display:flex` and `display:grid` in inline styles entirely.  
**Fix:** Complete rewrite of `generate_executive_report_html()` in `report_service.py`:

- **Fonts:** Removed Google Fonts `<link>`. Now uses system font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif` (stored in variable `F`, used everywhere)
- **Layout engine:** Every multi-column layout replaced with `<table cellpadding="0" cellspacing="0" border="0">` — the only layout that Gmail consistently respects
- **Status pills:** `display:inline-block` (was `inline-flex`) with a 6px inline `<span>` colored dot
- **Progress bars:** `<table>` with a 70px width cell (the bar) + a text cell (the %)
- **Wins / Blockers side-by-side:** 2-column `<table>` at `49% / 2% / 49%` widths
- **Metric strip:** 5-cell `<table>` row using `metric_td()` inner helper function
- **Section headers:** `<table>` with a 3px colored bar cell + label cell
- **All emojis removed:** wins use `+`, blockers/actions use `!`, separator dots use `&middot;`, arrows use `&rarr;`

**Files changed:** `services/report_service.py`

---

### 3. Slack Report — Rebuilt with Block Kit

**Problem:** Slack output was unstructured; emojis made it look unprofessional.  
**Fix:** Complete rewrite of `build_slack_blocks()` in `slack_service.py`:

Block layout (in order):
1. `header` — report title
2. `context` — date/time
3. `divider`
4. `section` — 1-sentence AI intro paragraph
5. `section` with `fields` — 5 metrics: Projects / On Track / At Risk / Delayed / Completed
6. `divider`
7. `section` — Customer Snapshot: `CustomerName — N projects — signal` per customer
8. `divider`
9. `section` — Actions Required (only if any exist): `! *Project* / Customer / Note`
10. `divider`
11. `section` with `fields` — Wins (left) + Blockers (right) in 2-column layout
12. `divider`
13. `context` — footer

Formatting rules: completely emoji-free. Uses `!` for blockers/actions, `+` for wins, `·` as separators, standard Slack markdown bold/italic.

**Files changed:** `services/slack_service.py`

---

### 4. Unknown Customer Fix

**Problem:** Projects from CVS, Cigna, Molina, and Autonomize Internal were showing under "Unknown Customer" in the dashboard. GPT had extracted the project update correctly but missed the customer on those emails.

**Fix — Part 1 (existing DB data):** One-off Python script using prefix matching corrected 4 existing records:
- CVS Integration - UAT Approved → CVS Health
- Cigna Migration - Phase 1 Complete → Cigna
- Molina Implementation - Needs Client Review → Molina Healthcare
- ACI Scan Implementation → Autonomize Internal

**Fix — Part 2 (future prevention):** Added inference logic to `get_or_create_project()` in `schema.py`. When the extracted customer is Unknown, the function now uses a `LIKE` prefix query against known projects to infer the real customer:
```sql
SELECT p.customer_id FROM projects p
JOIN customers c ON p.customer_id = c.id
WHERE c.name NOT IN ('Unknown Customer', 'Unknown', '')
AND length(p.project_name) >= 8
AND (
    ? LIKE p.project_name || ' %'
    OR ? LIKE p.project_name || ' - %'
    OR ? LIKE p.project_name || ': %'
)
ORDER BY length(p.project_name) DESC
LIMIT 1
```

**Files changed:** `database/schema.py`

---

### 5. Code Review — 5 Bugs Found and Fixed

Full automated code review (8 finder angles × 6 candidates → verify) surfaced and fixed:

| # | File | Bug | Fix |
|---|---|---|---|
| 1 | `schema.py` | No `try/finally` in `get_or_create_project` — any SQL exception between connection open and close leaked the SQLite connection | Wrapped entire function body in `try/finally: conn.close()` |
| 2 | `schema.py` | Extra SQL query (`SELECT name FROM customers WHERE id = ?`) fired unconditionally on every `get_or_create_project` call, even for known customers — overhead on every email in a scan batch | Added optional `customer_name` param; if passed, the lookup is skipped |
| 3 | `schema.py` | `instr(?, p.project_name) = 1` prefix match too broad — a 5-char project name like "Login" or "Alpha" under any known customer would silently absorb any new project starting with those chars | Replaced with `LIKE p.project_name || ' %'` (requires separator); raised minimum length from 5 → 8 chars |
| 4 | `slack_service.py` | `n['status']`, `n['type']`, `n['project']` used direct key access — if a project_note dict is missing a key, raises uncaught `KeyError` that propagates out of `build_slack_blocks` (not caught by `SlackApiError` handler) | All `n[key]` → `n.get('key', '')` throughout the notes loop |
| 5 | `slack_service.py` | Actions header said `ACTIONS REQUIRED (N)` using full list count, but display capped at 8 rows — count and visible lines mismatched for >8 actions | Added `"... and N more"` line when truncated; header count still shows total |

**Files changed:** `database/schema.py`, `services/slack_service.py`

---

### 6. Report Schedule — Fixed to 9 AM Cron

**Problem:** Scheduler used `'interval', hours=24` — fired 24 hours after service startup, not at a fixed time. If service restarted at 3 PM, report fired at 3 PM daily.  
**Fix:** Replaced interval trigger with APScheduler `cron` trigger. New env var `REPORT_SEND_TIME` (24h format, default `09:00`) controls the daily fire time. `REPORT_SEND_HOURS` removed.  
**Safety:** Parsing wrapped in `try/except` — a malformed value (e.g. `9am`, `0900`) prints a warning and disables auto-report instead of crashing Flask at import time with an `IndexError`.

**Files changed:** `config.py`, `dashboard/app.py`, `.env`, `SETUP.md`

---

### 7. Database — Duplicate Project Cleanup

**Problem:** Dashboard showed two "ACI Scan Implementation" entries with different scores (40 and 100). Also CVS, Cigna, and Molina each had a clean-name row AND a suffix row (`- UAT Approved`, `- Phase 1 Complete`, `- Needs Client Review`) from email subject lines being used as project names. Additionally, 7 junk Slack onboarding tutorial emails had created garbage projects under "Unknown Customer".

**Fix — Merge duplicates:** One-off script merged updates from all suffix/duplicate rows into canonical rows, then deleted the extras:
- ACI Scan Implementation (×2, both Autonomize Internal) → merged into one (Delayed/25%)
- CVS Integration + CVS Integration - UAT Approved → CVS Integration
- Cigna Migration + Cigna Migration - Phase 1 Complete → Cigna Migration
- Molina Implementation + Molina Implementation - Needs Client Review → Molina Implementation

**Fix — Delete junk:** 7 Slack tutorial projects (IDs 9–15) and their 14 associated updates deleted.

**Fix — Prevent future duplicates:** `get_or_create_project()` now falls back to a project-name-only lookup before INSERT. If a project with that name already exists under any customer (e.g. a second email arrives for the same project but inference fails), it returns the existing row instead of creating a duplicate.

**Result:** DB now has exactly 4 clean projects, each with 5 merged updates.

**Files changed:** `database/schema.py` (runtime guard), DB patched in-place

---

### 8. Executive Brief — 3 Sentences, Executive Language

**Problem:** Report intro was 1 vague sentence. Executives need specific, actionable facts in 3 sentences max.  
**Fix:** Rewrote `_generate_ai_intro()` in `report_service.py`:
- GPT prompt updated: exactly 3 sentences, C-suite language, max 20 words each, no filler
  - Sentence 1: portfolio health as a crisp fact
  - Sentence 2: the most critical risk requiring leadership action
  - Sentence 3: top blocker or delivery milestone
- No-GPT fallback (`_executive_brief_fallback`) builds the same 3-sentence structure from raw data
- Extracted `_flagged_project_names()` helper — removes duplicated `isinstance(p, dict)` loop that was in both `_executive_brief_fallback` and `_generate_ai_intro`
- `ai_brief` pre-computed once in `run_report_send()`, cached in `summary` dict — both email HTML and Slack read from it instead of each firing a separate GPT call

**Sample output (live data, no GPT key):**  
> "1 of 4 engagements across 4 clients are on track (25% portfolio health). 3 engagements — Cigna Migration, Molina Implementation, ACI Scan Implementation require immediate leadership review. Active blocker: Client approval on data model - expected by June 28."

**Files changed:** `services/report_service.py`, `services/slack_service.py`, `dashboard/app.py`

---

### 9. Recipients Tab — Optional Position Field

**Problem:** Recipients list showed name + email but no role context. Ujjwal needs to know who each person is when managing the list.  
**Fix:**
- `recipients` table: added `position TEXT` column (migration-safe via `ALTER TABLE` in startup migrations)
- `add_recipient(email, name, position)` — new optional arg
- `GET /api/recipients` now returns `position` field
- `POST /api/recipients` accepts optional `position` in request body
- Settings.jsx form: 3-column layout (Email required / Name optional / Position optional)
- Recipients list: position shown as a purple badge next to the name
- Footer: send time fetched from `/api/status` (`report_send_time` field) instead of hardcoded "9:00 AM"

**Files changed:** `database/schema.py`, `dashboard/app.py`, `frontend/src/pages/Settings.jsx`

---

### 10. Code Review Round 2 — 6 More Bugs Fixed

Second automated review pass surfaced and fixed:

| # | File | Bug | Fix |
|---|---|---|---|
| 1 | `config.py` | `REPORT_SEND_TIME=9am` or `0900` → `split(':')[1]` raises `IndexError` at module import, crashing Flask before it starts | Wrapped in `try/except`; malformed value prints clear warning and disables auto-report |
| 2 | `database/schema.py` | If inference changed `customer_id` on a 2nd scan but failed on the 1st, `INSERT` created a duplicate project under two different customers | Added name-only fallback `SELECT` before `INSERT` to return existing row regardless of customer |
| 3 | `slack_service.py` | `customer_status` dict had no `'completed'` key — Completed projects incremented `total` only, causing the snapshot signal to read "On Track" for customers with only completed projects | Added `'completed'` bucket and `elif s == 'Completed'` branch |
| 4 | `dashboard/app.py` + services | When OpenAI key is set, email send and Slack send each fired an independent `gpt-3.5-turbo` call — double cost and latency per report | `ai_brief` pre-computed once in `run_report_send()`, stored in `summary` dict, reused by both |
| 5 | `dashboard/app.py` + `Settings.jsx` | Footer text hardcoded "at 9:00 AM daily" — immediately wrong if `REPORT_SEND_TIME` env var changes | `/api/status` now returns `report_send_time`; Settings.jsx reads and displays it dynamically |
| 6 | `services/report_service.py` | Identical `isinstance(p, dict)` loop duplicated in `_executive_brief_fallback` and `_generate_ai_intro` | Extracted to `_flagged_project_names()` helper; both callers now use it |

**Files changed:** `config.py`, `database/schema.py`, `services/report_service.py`, `services/slack_service.py`, `dashboard/app.py`, `frontend/src/pages/Settings.jsx`

---

### 11. Scalability Confirmed

**How the system scales as Ujjwal receives more emails daily:**
- Gmail scan runs every 15 min, deduplicates by `gmail_id TEXT UNIQUE` — same email never processed twice
- Each scan appends new rows to `updates` table — no overwrites, no cap, no date filters
- `get_executive_summary()` queries all-time data: current status of all projects, 10 most recent accomplishments, 5 most recent blockers, top 50 project notes
- Daily report always reflects the full cumulative DB state — grows automatically as project count and email volume increase
- SQLite handles thousands of projects and tens of thousands of updates without issue at this scale

---

### 12. Known Open Issue — APScheduler Crash Loop

**Symptom:** `RuntimeError: cannot schedule new futures after shutdown` in `logs/server.log`. Auto-scan jobs are submitted to a shutdown thread pool executor and silently fail.  
**Impact:** Auto-scan still runs after service restart, but missed jobs during the crash window are not retried.  
**Status:** Not fixed in Session 3. Not blocking go-live (manual scan + manual send both work; launchd restarts the service on crash). **Fix before long-term prod use.**

---

## Final File State — After Session 3 (complete)

```
email-report-automation/
├── .env                          SENDER_EMAIL/PASSWORD/RECIPIENTS filled (Ethan's test creds)
│                                 REPORT_SEND_TIME=09:00 (replaces REPORT_SEND_HOURS)
│
├── config.py                     REPORT_SEND_TIME parsing with try/except crash guard
│                                 REPORT_SEND_HOUR / REPORT_SEND_MINUTE parsed fields
│
├── database/schema.py            + try/finally connection leak fix
│                                 + optional customer_name param (skip lookup)
│                                 + LIKE prefix inference (separator + min length 8)
│                                 + name-only fallback SELECT before INSERT (no duplicates)
│                                 + position column migration for recipients table
│                                 + get_recipients() / add_recipient() updated for position
│
├── services/
│   ├── report_service.py         Email-safe HTML (table layouts, system fonts, no emojis)
│   │                             _flagged_project_names() helper (deduplicates loop)
│   │                             _executive_brief_fallback() (3-sentence structured brief)
│   │                             _generate_ai_intro() (3-sentence GPT brief, C-suite language)
│   │                             generate_executive_report_html() reads ai_brief from summary
│   └── slack_service.py          Block Kit rewrite (no emojis, .get() safe access)
│                                 completed bucket in customer_status
│                                 reads ai_brief from summary (no duplicate GPT call)
│
├── dashboard/app.py              run_report_send() pre-computes ai_brief once
│                                 /api/status returns report_send_time
│                                 /api/recipients POST accepts position
│                                 cron scheduler at REPORT_SEND_HOUR:REPORT_SEND_MINUTE
│
└── frontend/src/pages/
    └── Settings.jsx              3-column form (email / name / position)
                                  position shown as purple badge in recipient list
                                  footer reads send time from /api/status dynamically
```

---

## Current Status — After Session 3 (complete)

**Service:** Running permanently at `http://localhost:5001` via launchd  
**Auto-scan:** Every 15 minutes (`SCAN_INTERVAL_MINUTES=15`)  
**Auto-report:** Daily at 9:00 AM (`REPORT_SEND_TIME=09:00`) — email confirmed working  
**Email delivery:** Confirmed (sent to ethann0530@gmail.com; Ujjwal added as recipient)  
**Terminal needed:** No — launchd runs independently, survives terminal close  
**Computer off:** Service stops — cloud deployment needed for true 24/7 uptime  
**GitHub:** Fully up to date  

**Still blocked on (Ujjwal to provide before go-live):**
- `OPENAI_API_KEY` — required for GPT extraction and AI brief quality
- `SLACK_BOT_TOKEN` + `SLACK_CHANNEL` — required for Slack delivery
- `SENDER_EMAIL` + `SENDER_PASSWORD` — replace Ethan's test creds in `.env`
- `GMAIL_QUERY` tuned to real project update senders/labels
- Cloud deployment (Railway / Render / DO) — if true always-on is required
- **APScheduler crash loop** — `RuntimeError: cannot schedule new futures after shutdown`

**Restart command:**
```
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist && launchctl load ~/Library/LaunchAgents/com.emailreport.plist
```

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

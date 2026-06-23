# Handoff — What Ujjwal Needs to Do Next

**From:** Ethan Nguyen  
**Date:** June 23, 2026  
**Repo:** github.com/ethannguyen0530/email-report-automation

---

## Where We Are

The full system is built and running on my machine. Here is exactly what is complete:

- Gmail is connected via OAuth2 and scans emails automatically **every 15 minutes**
- Email attachments (PDF, Word, Excel, PowerPoint) are extracted and fed to AI alongside the email body — nothing is missed
- OpenAI GPT extracts customer name, project name, status, progress %, milestone, blocker, owner, and a one-sentence summary from each email
- All data is stored in a local SQLite database
- A React dashboard runs at `http://localhost:5001` with:
  - Clickable metric cards (filter projects by status)
  - Portfolio health scores — per-project 0–100 scores with full breakdown modals (click any score circle to see why)
  - Click-through from accomplishments/blockers to the source email
  - Real-time dashboard updates via Server-Sent Events (no manual refresh needed)
  - Inline status editing — changing a status syncs all health scores, portfolio score, and alerts immediately
  - Customer management (auto-detect from emails, manual add/delete)
  - Red-flag alerts for projects that have gone silent 7+ days
- An executive HTML report is generated daily and sent automatically via email + Slack every 24 hours — also available on-demand from the Report tab
- File upload tab — drop in any PDF, Word doc, Excel report, or PowerPoint deck and the AI processes it exactly like an email
- Report recipients managed from the Settings tab in the UI — no `.env` editing needed
- The entire system runs as a permanent background service on macOS (no terminal needs to stay open, auto-restarts on crash, auto-starts on login)

**Estimate: 90%+ complete.** The engine is fully built. What is missing is the real credentials and the tuned email search criteria — which only Ujjwal can provide.

---

## What Ujjwal Needs to Provide

### 1. OpenAI API Key — Required for AI Extraction to Work

Without this, the system cannot extract project data from emails.

- Go to: platform.openai.com → API Keys → Create new secret key
- Add to `.env` as: `OPENAI_API_KEY=sk-...`
- **Cost estimate:** GPT-3.5 runs ~$0.001 per email. At 50 emails/day that is under $2/month.

---

### 2. Slack Bot Token + Channel — Required for Slack Report Delivery

- Go to: api.slack.com → Your Apps → Create New App → From Scratch
- App name: "Project Report Bot" (or whatever you want)
- Under "OAuth & Permissions" → Bot Token Scopes → add `chat:write`
- Install to workspace → copy the Bot User OAuth Token (`xoxb-...`)
- Add the bot to your target Slack channel (right-click channel → Add apps)
- Add to `.env`:
  ```
  SLACK_BOT_TOKEN=xoxb-...
  SLACK_CHANNEL=#channel-name
  ```

---

### 3. Gmail Sending Credentials — Required for Email Report Delivery

This is the Gmail account that **sends** the executive report (can be the same or different from the scanning account).

- Go to: myaccount.google.com → Security → 2-Step Verification → App Passwords
- Generate a password for "Mail" → 16-character code
- Add to `.env`:
  ```
  SENDER_EMAIL=you@gmail.com
  SENDER_PASSWORD=xxxx xxxx xxxx xxxx
  ```
- Add report recipients in the **Settings tab** in the dashboard, or as a fallback in `.env`:
  ```
  REPORT_RECIPIENTS=ujjwal@autonomize.ai,ethan@gmail.com
  ```

---

### 4. Gmail Search Query — Required to Target the Right Emails

Answer these questions, then update `GMAIL_QUERY` in `.env`:

- **Which Gmail account** gets scanned? (The one with project update emails in it)
- **Who sends the update emails?** List the exact email addresses of the program managers and delivery leads.
- **What subject line do they use?** e.g. "Weekly Update", "Project Status", "Sync Notes"
- **Is there a Gmail label** already applied to these emails? If so, use that — it's the most reliable filter.

Example of a well-tuned query:
```
GMAIL_QUERY=from:pm@autonomize.ai OR from:lead@autonomize.ai subject:update
```

---

### 5. Deployment Decision — Where Should This Live?

Right now the system runs on my MacBook. This means:
- Dashboard only accessible at `http://localhost:5001` from my machine
- If my MacBook is closed or off, auto-scans do not run

| Option | Cost | Effort | Who can access dashboard |
|---|---|---|---|
| My laptop only (current) | Free | Nothing to do | Just me |
| Shared on local network | Free | ~30 min | Anyone on same WiFi |
| Cloud (Railway / Render) | ~$5–20/month | ~2–4 hours | Anyone with the URL |
| Cloud + authentication | ~$5–20/month + auth | ~4–6 hours | Anyone you give a login to |

If you want the dashboard accessible to stakeholders or guaranteed uptime, cloud is the right call.

---

## Step-by-Step: Getting This Fully Running

Once Ujjwal has the credentials above, here is the exact sequence:

### Step 1 — Clone the repo

```bash
git clone https://github.com/ethannguyen0530/email-report-automation
cd email-report-automation
```

### Step 2 — Get `credentials.json` from Ethan

Ethan has the Gmail OAuth credentials file. Transfer `credentials.json` to the project root.  
*(Cannot be committed to GitHub for security reasons.)*

### Step 3 — Fill in `.env`

```bash
cp .env.example .env
# Open .env and fill in all the values listed above
```

The file should look like this when done:
```
GMAIL_CREDENTIALS_FILE=credentials.json
OPENAI_API_KEY=sk-...
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=#your-channel
SENDER_EMAIL=you@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
REPORT_RECIPIENTS=ujjwal@autonomize.ai
GMAIL_QUERY=from:pm@autonomize.ai subject:update
GMAIL_MAX_RESULTS=20
SCAN_INTERVAL_MINUTES=15
REPORT_SEND_HOURS=24
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_PORT=5001
USE_MOCK_DATA=False
```

### Step 4 — Install and start the service

```bash
bash install_service.sh
```

Installs all dependencies, builds the frontend, and starts the background service. Dashboard is live at `http://localhost:5001`.

### Step 5 — Authorize Gmail (one-time browser step)

```bash
python3 main.py
# Select option 2 (Process real emails)
```

A browser window opens asking you to sign in to Google and grant access. After you approve, `token.pickle` is saved. This step only happens once.

### Step 6 — Run your first real scan

```bash
python3 main.py
# Select option 2
```

Or: `curl -X POST http://localhost:5001/api/scan-now`

Check the dashboard at `http://localhost:5001` — real projects should appear.

### Step 7 — Add report recipients

Open the dashboard → Settings tab → add email addresses of everyone who should receive the daily executive report.

### Step 8 — Send a test report

Open the dashboard → click **Report** in the sidebar → click **Send via Email + Slack**.

Confirm:
- Email arrives in the configured recipient inboxes
- Slack message appears in the configured channel

### Step 9 — Verify auto-scan is working

```bash
tail -f ~/email-report-automation/logs/server.log
```

You should see:
```
Scheduler started: email scan every 15min, report every 24h
Scheduled email scan starting...
Scheduled email scan complete: X emails processed
```

---

## Quick Reference — Service Commands

```bash
# Restart (required after any .env change)
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist && \
launchctl load ~/Library/LaunchAgents/com.emailreport.plist

# Stop
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist

# Start
launchctl load ~/Library/LaunchAgents/com.emailreport.plist

# View live logs
tail -f ~/email-report-automation/logs/server.log

# Manual scan trigger
curl -X POST http://localhost:5001/api/scan-now
```

---

## Questions That Must Be Answered

Fill these in and update `.env` directly, or send back to Ethan:

```
Gmail account to scan: ___________________________________
Sender email addresses to filter for: ___________________________________
Subject keywords to filter for: ___________________________________
Slack workspace name: ___________________________________
Slack channel name: ___________________________________
Report recipients (full email list): ___________________________________
Deployment: laptop / cloud (which platform): ___________________________________
```

---

## What Happens After All Credentials Are Set

The full loop will work automatically:

1. Every 15 minutes — Gmail is scanned for new project update emails and attachments
2. Each email is processed by GPT; extracted data stored in the database
3. Dashboard updates in real time (via Server-Sent Events) when new emails come in
4. Every 24 hours — executive report is sent automatically to all recipients via email + Slack
5. Everything restarts automatically if the machine reboots

No terminal needs to stay open. No manual steps required after setup.

---

## Contact

Questions → Ethan Nguyen  
Repo → github.com/ethannguyen0530/email-report-automation  
Full technical reference → `REPO_COVERAGE_AND_QUESTIONS.md`  
Pipeline walkthrough → `~/email-report-automation-overview.md`

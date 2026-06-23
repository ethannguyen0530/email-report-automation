# Handoff — What Ujjwal Needs to Do Next

**From:** Ethan Nguyen  
**Date:** June 22, 2026  
**Repo:** github.com/ethannguyen0530/email-report-automation

---

## Where We Are

The full system is built and running on my machine. Here is exactly what is complete:

- Gmail is connected via OAuth2 and scans emails automatically every 6 hours
- OpenAI GPT extracts customer name, project name, status, progress %, milestone, blocker, and owner from each email
- All data is stored in a local SQLite database
- A React dashboard runs at `http://localhost:5001` showing all projects, metric cards, red-flag alerts for stale projects, and an email inbox view
- An executive HTML report is generated on demand with accomplishments, blockers, and a full project table — and can be sent to email + Slack with one click
- The entire system runs as a permanent background service on macOS (no terminal needs to stay open, auto-restarts on crash, auto-starts on login)

**Estimate: 80–90% complete.** The engine is built. What is missing is the real credentials, the tuned email search criteria, and answers to a few configuration questions — which only Ujjwal can provide.

---

## What Ujjwal Needs to Provide

### 1. OpenAI API Key — Required for AI Extraction to Work

Without this, the system cannot extract project data from emails (it will create blank or placeholder entries).

- Go to: platform.openai.com → API Keys → Create new secret key
- Add to `.env` as: `OPENAI_API_KEY=sk-...`
- **Cost estimate:** GPT-3.5 runs ~$0.001 per email. At 50 emails/day that is under $2/month.

---

### 2. Slack Bot Token + Channel — Required for Slack Report Delivery

- Go to: api.slack.com → Your Apps → Create New App → From Scratch
- App name: "Project Report Bot" (or whatever you want)
- Add the bot to your workspace
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

This is the Gmail account that **sends** the executive report (not the one that scans for updates — those can be the same or different).

- Go to: myaccount.google.com → Security → 2-Step Verification → App Passwords
- Generate a password for "Mail" → you will get a 16-character code
- Add to `.env`:
  ```
  SENDER_EMAIL=you@gmail.com
  SENDER_PASSWORD=xxxx xxxx xxxx xxxx
  REPORT_RECIPIENTS=ujjwal@autonomize.ai,ethan@gmail.com
  ```

---

### 4. Gmail Search Query — Required to Target the Right Emails

Right now the system uses a generic query. It needs to be tuned to only pull emails that contain real project status updates from the right people.

Answer these questions, then update `GMAIL_QUERY` in `.env`:

- **Which Gmail account** gets scanned? (The one with project update emails in it)
- **Who sends the update emails?** List the exact email addresses of the program managers and delivery leads who send project status emails. Example: `pm@autonomize.ai`, `lead@autonomize.ai`
- **What subject line do they use?** For example: "Weekly Update", "Project Status", "Sync Notes"
- **Is there a Gmail label** already applied to these emails? If so, use that — it is the most reliable filter.

Example of a well-tuned query:
```
GMAIL_QUERY=from:pm@autonomize.ai OR from:lead@autonomize.ai subject:update
```

---

### 5. Report Recipients — Who Gets the Executive Report

Provide a comma-separated list of email addresses that should receive the executive report when it is sent:

```
REPORT_RECIPIENTS=ujjwal@autonomize.ai,ethan@gmail.com
```

---

### 6. Deployment Decision — Where Should This Live?

Right now the system runs on my MacBook. This means:
- The dashboard is only accessible at `http://localhost:5001` from my machine
- If my MacBook is closed or off, auto-scans do not run

**What do you want?**

| Option | Cost | Effort | Who can access dashboard |
|---|---|---|---|
| My laptop only (current) | Free | Nothing to do | Just me |
| Shared on local network | Free | ~30 min | Anyone on same WiFi |
| Cloud (Railway / Render) | ~$5–20/month | ~2–4 hours | Anyone with the URL |
| Cloud + authentication | ~$5–20/month + auth setup | ~4–6 hours | Anyone you give a login to |

If you want the dashboard accessible to stakeholders or want guaranteed uptime, cloud is the right call.

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
*(This cannot be committed to GitHub for security reasons.)*

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
SCAN_INTERVAL_HOURS=6
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_PORT=5001
USE_MOCK_DATA=False
```

### Step 4 — Install and start the service

```bash
bash install_service.sh
```

This installs all dependencies, builds the frontend, and starts the background service. After this the dashboard is live at `http://localhost:5001`.

### Step 5 — Authorize Gmail (one-time browser step)

```bash
python3 main.py
# Select option 2 (Process real emails)
```

A browser window will open asking you to sign in to Google and grant access. After you approve, a `token.pickle` file is saved. Gmail will be authorized for future runs automatically — this step only happens once.

### Step 6 — Run your first real scan

```bash
python3 main.py
# Select option 2
```

Check the dashboard at `http://localhost:5001` — you should see real projects populated from the emails.

### Step 7 — Send a test report

Open the dashboard → click **Report** in the sidebar → click **Send via Email + Slack**.

Confirm:
- Email arrives in the `REPORT_RECIPIENTS` inboxes
- Slack message appears in the configured channel

### Step 8 — Verify auto-scan is working

The system is set to scan every 6 hours automatically. You can confirm it is running:

```bash
tail -f ~/email-report-automation/logs/server.log
```

You should see lines like:
```
Scheduler started: email scan every 6h
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
```

---

## Questions That Must Be Answered

Fill these in and send back to Ethan, or update `.env` directly:

```
Gmail account to scan: ___________________________________
Sender email addresses to filter for: ___________________________________
Subject keywords to filter for: ___________________________________
Slack workspace name: ___________________________________
Slack channel name: ___________________________________
Report recipients (full email list): ___________________________________
Report send frequency (manual / daily / weekly): ___________________________________
Deployment: laptop / cloud (which platform): ___________________________________
```

---

## What Happens After All Credentials Are Set

The full loop will work automatically:

1. Every 6 hours — Gmail is scanned for new project update emails
2. Each email is processed by GPT and extracted data is stored in the database
3. The dashboard updates in real time when you refresh
4. Click "Send via Email + Slack" in the Report tab to distribute the executive summary
5. Everything restarts automatically if the machine reboots

No terminal needs to stay open. No manual steps required after setup.

---

## Contact

Questions → Ethan Nguyen  
Repo → github.com/ethannguyen0530/email-report-automation  
Full technical reference → `REPO_COVERAGE_AND_QUESTIONS.md`

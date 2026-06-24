# Setup Guide

This document walks through getting the Email Report Automation system fully running from scratch — from a fresh clone to a live dashboard with real Gmail data.

**Estimated time:** 30–45 minutes (mostly waiting for installs)

---

## Prerequisites

- macOS (the background service uses macOS launchd)
- Python 3.9 or later — check with `python3 --version`
- Node.js 18 or later — check with `node --version`
- A Gmail account that receives project update emails
- Git access to `github.com/ethannguyen0530/email-report-automation`

---

## Step 1 — Clone the Repo

```bash
git clone https://github.com/ethannguyen0530/email-report-automation
cd email-report-automation
```

---

## Step 2 — Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

This installs Flask, Gunicorn, OpenAI, APScheduler, pdfplumber, python-docx, openpyxl, python-pptx, and all other dependencies.

---

## Step 3 — Get `credentials.json` from Ethan

The Gmail OAuth credentials file (`credentials.json`) cannot be committed to GitHub for security reasons. Get this file from Ethan and place it in the project root:

```
email-report-automation/
├── credentials.json    ← place it here
├── .env
├── ...
```

**If you need to create your own (alternative):**
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → APIs & Services → Enable **Gmail API**
3. Credentials → Create Credentials → OAuth 2.0 Client ID → Desktop app
4. Download the JSON → rename to `credentials.json` → place in project root

---

## Step 4 — Configure Your Credentials

Copy the template and fill in your values:

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in each value:

```
GMAIL_CREDENTIALS_FILE=credentials.json
OPENAI_API_KEY=sk-...
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=#your-channel
SENDER_EMAIL=you@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
REPORT_RECIPIENTS=ujjwal@autonomize.ai,ethan@gmail.com
GMAIL_QUERY=from:@autonomize.ai subject:update
GMAIL_MAX_RESULTS=20
DB_PATH=projects.db
SCAN_INTERVAL_MINUTES=15
REPORT_SEND_TIME=09:00
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_PORT=5001
USE_MOCK_DATA=False
```

### Where to get each credential

---

**OPENAI_API_KEY**

1. Go to [platform.openai.com](https://platform.openai.com) → Sign in
2. Click your profile (top right) → API Keys
3. Create new secret key → copy it
4. Paste as: `OPENAI_API_KEY=sk-...`

Cost: GPT-3.5 is ~$0.001 per email. At 50 emails/day that's under $2/month.

---

**SLACK_BOT_TOKEN + SLACK_CHANNEL**

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create New App → From Scratch → name it anything (e.g. "Project Report Bot")
3. Select your workspace → Create App
4. In the left sidebar → OAuth & Permissions
5. Under Scopes → Bot Token Scopes → Add `chat:write`
6. Click Install to Workspace → Allow
7. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
8. Go into Slack → right-click your target channel → Add apps → add your bot

```
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL=#project-updates
```

---

**SENDER_EMAIL + SENDER_PASSWORD**

This is the Gmail account that *sends* the executive report. It can be the same Gmail that scans for project emails.

1. Go to [myaccount.google.com](https://myaccount.google.com) → Security
2. Make sure 2-Step Verification is turned ON
3. Search for "App Passwords" → select it
4. Choose "Mail" → Generate
5. Copy the 16-character code (shown only once)

```
SENDER_EMAIL=you@gmail.com
SENDER_PASSWORD=abcd efgh ijkl mnop
```

---

**GMAIL_QUERY**

This controls which emails the system reads. Tune it to target exactly the emails that contain project status updates.

Examples:

```bash
# All emails from your company domain about updates or status
GMAIL_QUERY=from:@autonomize.ai subject:update OR subject:status

# Specific senders only
GMAIL_QUERY=from:pm@autonomize.ai OR from:lead@autonomize.ai

# By Gmail label (most reliable if you have labels set up)
GMAIL_QUERY=label:project-updates

# Combined
GMAIL_QUERY=from:@autonomize.ai subject:"weekly update" OR subject:"project status"
```

Start broad if you're unsure, then narrow it down after seeing what gets pulled in.

---

**REPORT_RECIPIENTS**

Comma-separated list of email addresses that receive the daily executive report:

```
REPORT_RECIPIENTS=ujjwal@autonomize.ai,cto@autonomize.ai
```

You can also manage recipients from the **Settings tab** in the dashboard after setup — that approach stores them in the database and doesn't require editing `.env`.

---

## Step 5 — Install the Background Service

Run the one-command installer:

```bash
bash install_service.sh
```

This does everything:
- Installs Python dependencies (again, to be sure)
- Builds the React frontend
- Writes `~/Library/LaunchAgents/com.emailreport.plist`
- Starts the service immediately

After this completes, visit **[http://localhost:5001](http://localhost:5001)** — the dashboard should be live.

---

## Step 6 — Authorize Gmail (One-Time)

The first time you scan Gmail, a browser window opens asking you to sign in to Google and grant access. This happens once and is never repeated.

```bash
python3 main.py
```

Select option **2 — Process real emails**

A browser window opens → sign in with the Gmail account that has the project emails → click Allow. A `token.pickle` file is saved automatically. All future scans use this saved token silently.

---

## Step 7 — Run Your First Scan

After Gmail is authorized:

```bash
python3 main.py
# Select option 2
```

Or trigger it from the API:

```bash
curl -X POST http://localhost:5001/api/scan-now
```

Check the dashboard at **http://localhost:5001** — projects should start appearing within a minute.

---

## Step 8 — Add Report Recipients (Optional UI Method)

Instead of editing `.env`, you can manage recipients from the dashboard:

1. Open **http://localhost:5001**
2. Click **Settings** in the left sidebar
3. Add recipient email addresses
4. They are saved to the database immediately

Recipients added here take priority over the `.env` `REPORT_RECIPIENTS` value.

---

## Step 9 — Send a Test Report

1. Open the dashboard → click **Report** in the sidebar
2. The executive report preview loads in the page
3. Click **Send via Email + Slack**
4. Confirm:
   - Email arrives in the recipient inboxes
   - Slack message appears in `SLACK_CHANNEL`

---

## Step 10 — Verify Everything Is Running

Check that the background service is active and scanning:

```bash
tail -f ~/email-report-automation/logs/server.log
```

You should see output like:

```
Scheduler started: email scan every 15min, report every 24h
Scheduled email scan starting...
Scheduled email scan complete: 3 emails processed
```

The dashboard also shows a live purple dot in the header when the Server-Sent Events connection is active.

---

## You're Done

From here, everything runs automatically:

| What | When |
|---|---|
| Gmail scanned for new emails | Every 15 minutes |
| Dashboard updates in real time | Immediately when scan finds new emails |
| Executive report sent via email + Slack | Every 24 hours |
| Service auto-restarts if it crashes | Within 10 seconds (launchd KeepAlive) |
| Service starts automatically on login | Every time macOS boots |

No terminal needs to stay open. No manual steps required.

---

## Service Commands (Quick Reference)

```bash
# Restart after changing .env or code
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist && \
launchctl load ~/Library/LaunchAgents/com.emailreport.plist

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.emailreport.plist

# Start the service
launchctl load ~/Library/LaunchAgents/com.emailreport.plist

# View live logs
tail -f ~/email-report-automation/logs/server.log

# Manually trigger a scan
curl -X POST http://localhost:5001/api/scan-now

# Manually trigger a report send
curl -X POST http://localhost:5001/api/send-report
```

---

## Troubleshooting

**Dashboard is blank / shows no projects**
- Check that the Gmail scan ran: `tail -f logs/server.log`
- Make sure `GMAIL_QUERY` matches emails that actually exist in your inbox
- Make sure `USE_MOCK_DATA=False` in `.env`
- Make sure `OPENAI_API_KEY` is set — without it, extraction produces blank data

**Gmail auth browser window didn't open**
- Run `python3 main.py → option 2` from the terminal directly
- Make sure `credentials.json` is in the project root
- Delete `token.pickle` if it exists and try again

**Slack message not delivering**
- Confirm the bot has `chat:write` scope
- Confirm the bot was added to the channel (right-click channel → Add apps)
- Check `SLACK_CHANNEL` matches exactly (with the `#`)

**Report email not arriving**
- Check `SENDER_PASSWORD` is the App Password (16 chars), not your regular Gmail password
- Confirm 2-Step Verification is enabled on the sender Gmail account
- Check spam/junk folders

**Service won't start**
- Check `logs/error.log` for the specific error
- Make sure the Python path in the plist is correct: `which python3`
- Re-run `bash install_service.sh` to regenerate the plist

**Port 5001 already in use**
```bash
lsof -i :5001          # find what's using it
kill -9 <PID>          # kill it
launchctl load ~/Library/LaunchAgents/com.emailreport.plist
```

---

## Questions

Contact Ethan Nguyen or see:
- `HANDOFF.md` — credential checklist and setup sequence
- `REPO_COVERAGE_AND_QUESTIONS.md` — full system coverage, open questions, production readiness checklist
- `~/email-report-automation-overview.md` — full technical pipeline walkthrough

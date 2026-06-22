# Email-to-Report Automation System

Automatically scan Gmail from multiple team members, extract project details, consolidate into executive reports, and distribute via email and Slack with a live progress dashboard.

## Features

- **Gmail Integration** — OAuth2, scan emails from program managers and delivery leads
- **AI-Powered Extraction** — Extracts customer, project, status, progress %, milestone, blocker, owner via OpenAI
- **Consolidated Executive Reports** — Single report via email + Slack simultaneously
- **Live Dashboard** — Executive summary, project drill-downs, accomplishments, blockers

## Quick Start

### 1. Install dependencies

```bash
cd email-report-automation
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run with mock data

```bash
python main.py
# Select option 5 to run the full pipeline
```

### 4. View the dashboard

```bash
python main.py
# Select option 4, then visit http://localhost:5000
```

## Adding Real Credentials

**Gmail API:**
1. Go to Google Cloud Console
2. Create a project and enable Gmail API
3. Create OAuth2 credentials (Desktop app)
4. Download `credentials.json` to the project root
5. Set `USE_MOCK_DATA=False` in `.env`

**Slack:**
1. Create a Slack bot in your workspace
2. Copy the Bot User Token (xoxb-...)
3. Add `SLACK_BOT_TOKEN` to `.env`
4. Add bot to the target channel

**Email SMTP:**
1. Use a Gmail app password
2. Set `SENDER_EMAIL`, `SENDER_PASSWORD`, `REPORT_RECIPIENTS` in `.env`

## Architecture

```
Gmail → Email Ingestion → AI Extraction → SQLite Database
                                               ↓
                              Report Service (Email + Slack)
                              Dashboard Web UI (Flask)
```

## Database Schema

- `customers` — company names
- `projects` — project details (status, progress, owner)
- `updates` — historical updates extracted from emails
- `emails` — raw email log

## Configuration

See `.env.example` for all options. Key settings:

| Variable | Description |
|---|---|
| `GMAIL_QUERY` | Gmail search query to filter emails |
| `SLACK_CHANNEL` | Slack channel for reports |
| `REPORT_RECIPIENTS` | Comma-separated email addresses |
| `USE_MOCK_DATA` | Set to `False` to use real Gmail |

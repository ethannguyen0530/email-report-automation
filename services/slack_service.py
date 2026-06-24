from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import config
from datetime import datetime, timedelta


class SlackService:
    def __init__(self):
        if config.SLACK_BOT_TOKEN:
            self.client = WebClient(token=config.SLACK_BOT_TOKEN)
        else:
            self.client = None

    def send_report(self, summary_data, report_type="daily"):
        if not self.client:
            print("Skipping Slack: SLACK_BOT_TOKEN not set in .env")
            return False

        blocks = self.build_slack_blocks(summary_data)

        try:
            self.client.chat_postMessage(
                channel=config.SLACK_CHANNEL,
                blocks=blocks,
                text="Autonomize AI — Project Intel Report"
            )
            print(f"Slack report sent to {config.SLACK_CHANNEL}")
            return True
        except SlackApiError as e:
            print(f"Slack error: {e}")
            return False

    def build_slack_blocks(self, data):
        now = datetime.now()
        week_start = (now - timedelta(days=7)).strftime('%b %d')
        week_end = now.strftime('%b %d, %Y')
        date_str = now.strftime('%B %d, %Y')
        email_sources = data.get('email_sources_count', 0)

        # ── Normalize projects ────────────────────────────────────────────────
        projects = data.get('projects', [])
        normalized = []
        for p in projects:
            if isinstance(p, dict):
                normalized.append(p)
            else:
                normalized.append({
                    'name': p[1], 'customer': p[2] or 'Other',
                    'status': p[3], 'progress': p[4], 'owner': p[5],
                })

        # ── Customer snapshot ─────────────────────────────────────────────────
        customer_status = {}
        for p in normalized:
            c = p.get('customer') or 'Other'
            if c not in customer_status:
                customer_status[c] = {'on_track': 0, 'at_risk': 0, 'delayed': 0, 'completed': 0, 'total': 0}
            s = p.get('status', '')
            if s == 'On Track': customer_status[c]['on_track'] += 1
            elif s == 'At Risk': customer_status[c]['at_risk'] += 1
            elif s == 'Delayed': customer_status[c]['delayed'] += 1
            elif s == 'Completed': customer_status[c]['completed'] += 1
            customer_status[c]['total'] += 1

        snapshot_lines = []
        for c_name in sorted(customer_status.keys()):
            cs = customer_status[c_name]
            if cs['delayed'] > 0:
                signal = '*Action Required*'
            elif cs['at_risk'] > 0:
                signal = 'Monitor Closely'
            else:
                signal = 'On Track'
            count = cs['total']
            snapshot_lines.append(f"{c_name}  —  {count} project{'s' if count != 1 else ''}  —  {signal}")

        # ── Actions required ──────────────────────────────────────────────────
        actions = []
        for n in data.get('project_notes', []):
            if n.get('type') == 'blocker':
                actions.append({'project': n.get('project', ''), 'customer': n.get('customer') or '—',
                                'note': n.get('note', ''), 'urgency': 'high'})
            elif n.get('status') in ('At Risk', 'Delayed'):
                actions.append({'project': n.get('project', ''), 'customer': n.get('customer') or '—',
                                'note': n.get('note') or n.get('status', ''), 'urgency': 'med'})

        shown = actions[:8]
        action_lines = []
        for a in shown:
            prefix = '!' if a['urgency'] == 'high' else '-'
            action_lines.append(f"{prefix}  *{a['project']}*  /  {a['customer']}  /  {a['note']}")
        if len(actions) > 8:
            action_lines.append(f"_... and {len(actions) - 8} more_")

        # ── Wins + Blockers ───────────────────────────────────────────────────
        wins = data.get('accomplishments', [])[:5]
        blockers = data.get('blockers', [])[:5]

        wins_text = '\n'.join(f"+  {w}" for w in wins) if wins else '_None recorded_'
        blockers_text = '\n'.join(f"!  {b}" for b in blockers) if blockers else '_None reported_'

        # ── Build blocks ──────────────────────────────────────────────────────
        blocks = []

        # Header
        blocks.append({
            "type": "header",
            "text": {"type": "plain_text", "text": "Autonomize AI  ·  Project Intel"}
        })

        # Date + context
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"Executive Summary  ·  {week_start} – {week_end}  ·  {email_sources} emails  ·  {now.strftime('%I:%M %p')}"
            }]
        })

        blocks.append({"type": "divider"})

        # Executive brief — use pre-computed brief if available, otherwise generate
        intro = data.get('ai_brief')
        if not intro:
            from services.report_service import ReportService
            intro = ReportService()._generate_ai_intro(data)
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_{intro}_"}
        })

        # Metric strip
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*{data.get('total_projects', len(normalized))}*\nProjects"},
                {"type": "mrkdwn", "text": f"*{data.get('on_track', 0)}*\nOn Track"},
                {"type": "mrkdwn", "text": f"*{data.get('at_risk', 0)}*\nAt Risk"},
                {"type": "mrkdwn", "text": f"*{data.get('delayed', 0)}*\nDelayed"},
                {"type": "mrkdwn", "text": f"*{data.get('completed', 0)}*\nCompleted"},
            ]
        })

        blocks.append({"type": "divider"})

        # Customer snapshot
        if snapshot_lines:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*CUSTOMER SNAPSHOT*\n\n" + "\n".join(snapshot_lines)
                }
            })
            blocks.append({"type": "divider"})

        # Actions required
        if action_lines:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ACTIONS REQUIRED  ({len(actions)})*\n\n" + "\n".join(action_lines)
                }
            })
            blocks.append({"type": "divider"})

        # Wins + Blockers side by side
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*WINS THIS WEEK*\n\n{wins_text}"},
                {"type": "mrkdwn", "text": f"*OPEN BLOCKERS*\n\n{blockers_text}"},
            ]
        })

        blocks.append({"type": "divider"})

        # Footer
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"Autonomize AI  ·  Confidential  ·  {date_str}  ·  Auto-generated from {email_sources} email source{'s' if email_sources != 1 else ''}"
            }]
        })

        return blocks

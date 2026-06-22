from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import config
from datetime import datetime

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
                text="Project Status Report"
            )
            print(f"Slack report sent to {config.SLACK_CHANNEL}")
            return True
        except SlackApiError as e:
            print(f"Slack error: {e}")
            return False

    def build_slack_blocks(self, data):
        accomplishments = [f"- {acc}" for acc in data['accomplishments'][:5]]
        blockers = [f"- {blocker}" for blocker in data['blockers'][:5]]

        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Project Status Report"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total Projects:*\n{data['total_projects']}"},
                    {"type": "mrkdwn", "text": f"*On Track:*\n{data['on_track']}"},
                    {"type": "mrkdwn", "text": f"*At Risk:*\n{data['at_risk']}"},
                    {"type": "mrkdwn", "text": f"*Delayed:*\n{data['delayed']}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Recent Accomplishments:*\n" + "\n".join(accomplishments or ["No accomplishments yet"])
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Open Blockers:*\n" + "\n".join(blockers or ["No blockers reported"])
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Report generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]

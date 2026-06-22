import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config

class ReportService:
    def generate_executive_report_html(self, summary_data):
        projects_html = ""
        for proj in summary_data['projects']:
            proj_id, proj_name, customer, status, progress, owner = proj
            status_color = {
                'On Track': '#28a745',
                'At Risk': '#ffc107',
                'Delayed': '#dc3545',
                'Completed': '#6c757d'
            }.get(status, '#007bff')

            projects_html += f"""
            <tr>
                <td>{proj_name}</td>
                <td>{customer or 'N/A'}</td>
                <td><span style="background: {status_color}; color: white; padding: 4px 8px; border-radius: 3px;">{status}</span></td>
                <td>{progress}%</td>
                <td>{owner}</td>
            </tr>
            """

        accomplishments_html = "".join([
            f"<li>{acc}</li>" for acc in summary_data['accomplishments']
        ])

        blockers_html = "".join([
            f"<li style='color: #dc3545;'>{blocker}</li>" for blocker in summary_data['blockers']
        ])

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; margin: 0; padding: 20px; background: #f9f9f9; }}
                .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #007bff; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
                h2 {{ color: #333; margin-top: 30px; border-left: 4px solid #007bff; padding-left: 10px; }}
                .metrics {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .metric {{ background: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; }}
                .metric-value {{ font-size: 28px; font-weight: bold; color: #007bff; }}
                .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th {{ background: #007bff; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #eee; }}
                ul {{ margin: 10px 0; padding-left: 20px; }}
                li {{ margin: 8px 0; }}
                .timestamp {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Executive Project Summary Report</h1>

                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{summary_data['total_projects']}</div>
                        <div class="metric-label">Total Projects</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary_data['on_track']}</div>
                        <div class="metric-label">On Track</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary_data['at_risk']}</div>
                        <div class="metric-label">At Risk</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary_data['delayed']}</div>
                        <div class="metric-label">Delayed</div>
                    </div>
                </div>

                <h2>Recent Accomplishments</h2>
                <ul>
                    {accomplishments_html}
                </ul>

                <h2>Open Blockers</h2>
                <ul>
                    {blockers_html if blockers_html else '<li>No blockers reported</li>'}
                </ul>

                <h2>All Projects</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Project Name</th>
                            <th>Customer</th>
                            <th>Status</th>
                            <th>Progress</th>
                            <th>Owner</th>
                        </tr>
                    </thead>
                    <tbody>
                        {projects_html}
                    </tbody>
                </table>

                <div class="timestamp">Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
        </body>
        </html>
        """
        return html

    def generate_report_text(self, summary_data):
        text = f"""
Executive Project Summary Report
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

METRICS:
- Total Projects: {summary_data['total_projects']}
- On Track: {summary_data['on_track']}
- At Risk: {summary_data['at_risk']}
- Delayed: {summary_data['delayed']}

RECENT ACCOMPLISHMENTS:
{chr(10).join([f'  - {acc}' for acc in summary_data['accomplishments']] or ['  No recent accomplishments'])}

OPEN BLOCKERS:
{chr(10).join([f'  - {blocker}' for blocker in summary_data['blockers']] or ['  No blockers reported'])}
        """
        return text.strip()

    def send_email_report(self, recipients, subject, html_content):
        if not config.SENDER_EMAIL or not config.SENDER_PASSWORD:
            print("Skipping email send: SENDER_EMAIL or SENDER_PASSWORD not set in .env")
            return False

        if not recipients or recipients == ['']:
            print("No email recipients configured")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = ", ".join(recipients)

            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
                server.sendmail(config.SENDER_EMAIL, recipients, msg.as_string())

            print(f"Email report sent to: {', '.join(recipients)}")
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False

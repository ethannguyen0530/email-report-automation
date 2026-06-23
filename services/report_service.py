import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config

STATUS_COLORS = {
    'On Track':   {'bg': '#dcfce7', 'text': '#15803d', 'dot': '#22c55e'},
    'At Risk':    {'bg': '#fef9c3', 'text': '#854d0e', 'dot': '#eab308'},
    'Delayed':    {'bg': '#fee2e2', 'text': '#991b1b', 'dot': '#ef4444'},
    'Completed':  {'bg': '#f1f5f9', 'text': '#475569', 'dot': '#94a3b8'},
    'In Progress':{'bg': '#ede9fe', 'text': '#5b21b6', 'dot': '#7c3aed'},
}

class ReportService:
    def generate_executive_report_html(self, summary_data):
        # Build project rows
        projects_html = ''
        for proj in summary_data['projects']:
            if isinstance(proj, dict):
                proj_id, proj_name, customer, status, progress, owner = proj['id'], proj['name'], proj.get('customer'), proj['status'], proj['progress'], proj['owner']
            else:
                proj_id, proj_name, customer, status, progress, owner = proj[0], proj[1], proj[2], proj[3], proj[4], proj[5]

            sc = STATUS_COLORS.get(status, {'bg': '#f1f5f9', 'text': '#475569', 'dot': '#94a3b8'})
            bar_color = sc['dot']
            projects_html += f"""
            <tr>
                <td style="padding:14px 16px;font-weight:600;color:#1e293b;max-width:260px">{proj_name}</td>
                <td style="padding:14px 16px;color:#475569">{customer or '—'}</td>
                <td style="padding:14px 16px">
                    <span style="display:inline-flex;align-items:center;gap:6px;background:{sc['bg']};color:{sc['text']};padding:4px 10px;border-radius:99px;font-size:11px;font-weight:700;letter-spacing:0.03em">
                        <span style="width:6px;height:6px;border-radius:50%;background:{sc['dot']};display:inline-block"></span>
                        {status}
                    </span>
                </td>
                <td style="padding:14px 16px;min-width:160px">
                    <div style="display:flex;align-items:center;gap:10px">
                        <div style="flex:1;height:6px;background:#e2e8f0;border-radius:99px;overflow:hidden">
                            <div style="width:{progress}%;height:100%;background:{bar_color};border-radius:99px"></div>
                        </div>
                        <span style="font-size:12px;color:#64748b;white-space:nowrap;font-weight:600">{progress}%</span>
                    </div>
                </td>
                <td style="padding:14px 16px;color:#64748b">{owner}</td>
            </tr>"""

        # Accomplishments
        acc_html = ''.join([f"""
            <div style="display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid #f1f5f9">
                <div style="width:20px;height:20px;border-radius:50%;background:#dcfce7;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">
                    <span style="color:#16a34a;font-size:11px;font-weight:700">✓</span>
                </div>
                <p style="margin:0;color:#334155;font-size:14px;line-height:1.6">{a}</p>
            </div>"""
            for a in summary_data['accomplishments']
        ]) or '<p style="color:#94a3b8;font-size:14px;margin:0;padding:12px 0">No accomplishments recorded yet.</p>'

        # Blockers
        blk_html = ''.join([f"""
            <div style="display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid #fff1f2">
                <div style="width:20px;height:20px;border-radius:50%;background:#fee2e2;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">
                    <span style="color:#dc2626;font-size:12px;font-weight:700">!</span>
                </div>
                <p style="margin:0;color:#334155;font-size:14px;line-height:1.6">{b}</p>
            </div>"""
            for b in summary_data['blockers']
        ]) or '<p style="color:#94a3b8;font-size:14px;margin:0;padding:12px 0">No blockers reported.</p>'

        # Project notes
        notes = summary_data.get('project_notes', [])
        notes_html = ''.join([f"""
            <div style="padding:16px;background:#f8fafc;border-radius:10px;border-left:3px solid #7c3aed;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
                    <div>
                        <span style="font-weight:700;color:#1e293b;font-size:13px">{n['project']}</span>
                        {f'<span style="color:#94a3b8;font-size:12px"> · {n["customer"]}</span>' if n.get("customer") else ''}
                    </div>
                    <span style="font-size:11px;color:#94a3b8;white-space:nowrap;margin-left:12px">{(n.get('date') or '')[:10]}</span>
                </div>
                <p style="margin:0;color:#475569;font-size:13px;line-height:1.6">{n['note']}</p>
                {f'<p style="margin:6px 0 0;font-size:11px;color:#94a3b8">— {n["owner"]}</p>' if n.get("owner") and n["owner"] != "Unknown" else ''}
            </div>"""
            for n in notes
        ]) or '<p style="color:#94a3b8;font-size:14px;margin:0;padding:12px 0">No project notes on record.</p>'

        # Metric cards
        def metric_card(value, label, color):
            return f"""
            <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:20px 24px;min-width:140px">
                <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-bottom:8px">{label}</div>
                <div style="font-size:34px;font-weight:800;color:{color};line-height:1;letter-spacing:-1px">{value}</div>
            </div>"""

        now = datetime.now()
        date_str = now.strftime('%B %d, %Y')
        time_str = now.strftime('%I:%M %p')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Executive Report — {date_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f1f5f9; color: #1e293b; }}
  table {{ border-collapse: collapse; width: 100%; }}
  tr:last-child td {{ border-bottom: none !important; }}
  tr:hover td {{ background: #f8fafc; }}
</style>
</head>
<body>
<div style="max-width:900px;margin:0 auto;padding:32px 20px 60px">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#4c1d95 100%);border-radius:16px;padding:40px 48px;margin-bottom:28px;position:relative;overflow:hidden">
    <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,0.04)"></div>
    <div style="position:absolute;bottom:-60px;right:60px;width:300px;height:300px;border-radius:50%;background:rgba(255,255,255,0.03)"></div>
    <p style="font-size:11px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:0.15em;font-weight:600;margin-bottom:12px">CONFIDENTIAL · EXECUTIVE SUMMARY</p>
    <h1 style="font-size:30px;font-weight:800;color:white;letter-spacing:-0.5px;line-height:1.2;margin-bottom:10px">Executive Project Report</h1>
    <p style="font-size:15px;color:rgba(255,255,255,0.65)">{date_str} &nbsp;·&nbsp; Generated at {time_str}</p>
  </div>

  <!-- Metrics -->
  <div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:28px">
    {metric_card(summary_data['total_projects'], 'Total Projects', '#7c3aed')}
    {metric_card(summary_data['on_track'],       'On Track',       '#16a34a')}
    {metric_card(summary_data['at_risk'],        'At Risk',        '#d97706')}
    {metric_card(summary_data['delayed'],        'Delayed',        '#dc2626')}
    {metric_card(summary_data.get('completed',0),'Completed',      '#64748b')}
  </div>

  <!-- Two column: accomplishments + blockers -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px">

    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
      <div style="padding:18px 24px 14px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:8px">
        <div style="width:3px;height:16px;background:#22c55e;border-radius:99px"></div>
        <h2 style="font-size:13px;font-weight:700;color:#1e293b;text-transform:uppercase;letter-spacing:0.05em">Recent Accomplishments</h2>
      </div>
      <div style="padding:4px 24px 12px">{acc_html}</div>
    </div>

    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
      <div style="padding:18px 24px 14px;border-bottom:1px solid #fff1f2;display:flex;align-items:center;gap:8px">
        <div style="width:3px;height:16px;background:#ef4444;border-radius:99px"></div>
        <h2 style="font-size:13px;font-weight:700;color:#1e293b;text-transform:uppercase;letter-spacing:0.05em">Open Blockers</h2>
      </div>
      <div style="padding:4px 24px 12px">{blk_html}</div>
    </div>
  </div>

  <!-- Project Notes -->
  <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;margin-bottom:28px">
    <div style="padding:18px 24px 14px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:8px">
      <div style="width:3px;height:16px;background:#7c3aed;border-radius:99px"></div>
      <h2 style="font-size:13px;font-weight:700;color:#1e293b;text-transform:uppercase;letter-spacing:0.05em">Project Notes</h2>
    </div>
    <div style="padding:16px 24px">{notes_html}</div>
  </div>

  <!-- Projects Table -->
  <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;margin-bottom:28px">
    <div style="padding:18px 24px 14px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:8px">
      <div style="width:3px;height:16px;background:#3b82f6;border-radius:99px"></div>
      <h2 style="font-size:13px;font-weight:700;color:#1e293b;text-transform:uppercase;letter-spacing:0.05em">All Projects</h2>
    </div>
    <table>
      <thead>
        <tr style="background:#f8fafc">
          <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Project</th>
          <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Customer</th>
          <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Status</th>
          <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Progress</th>
          <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Owner</th>
        </tr>
      </thead>
      <tbody>
        {projects_html}
      </tbody>
    </table>
  </div>

  <!-- Footer -->
  <div style="text-align:center;padding-top:20px">
    <p style="font-size:12px;color:#94a3b8">Confidential · For internal use only · {date_str}</p>
  </div>

</div>
</body>
</html>"""
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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import config

STATUS_COLORS = {
    'On Track':   {'bg': '#dcfce7', 'text': '#15803d', 'dot': '#22c55e'},
    'At Risk':    {'bg': '#fef9c3', 'text': '#854d0e', 'dot': '#eab308'},
    'Delayed':    {'bg': '#fee2e2', 'text': '#991b1b', 'dot': '#ef4444'},
    'Completed':  {'bg': '#f1f5f9', 'text': '#475569', 'dot': '#94a3b8'},
    'In Progress':{'bg': '#ede9fe', 'text': '#5b21b6', 'dot': '#7c3aed'},
}

class ReportService:

    def _generate_ai_intro(self, summary_data):
        """Generate a single executive summary sentence via GPT."""
        if not config.OPENAI_API_KEY:
            total = summary_data['total_projects']
            on_track = summary_data['on_track']
            at_risk = summary_data['at_risk']
            delayed = summary_data['delayed']
            problem = f"{at_risk + delayed} project(s) need attention" if (at_risk or delayed) else "all projects are on track"
            return f"{total} active projects across {len(set(self._project_customer(p) for p in summary_data['projects']))} customers — {problem}."

        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            notes = summary_data.get('project_notes', [])
            at_risk_items = [n for n in notes if n['status'] in ('At Risk', 'Delayed')]
            blockers = summary_data.get('blockers', [])
            context = (
                f"Total: {summary_data['total_projects']} projects, "
                f"{summary_data['on_track']} on track, "
                f"{summary_data['at_risk']} at risk, "
                f"{summary_data['delayed']} delayed. "
            )
            if at_risk_items:
                context += f"Flagged: {', '.join(n['project'] for n in at_risk_items[:3])}. "
            if blockers:
                context += f"Blockers: {blockers[0]}. "
            prompt = (
                "Write exactly 1 sentence (max 25 words) for an executive project status report. "
                "State the portfolio status and the single most important concern. Direct, no fluff. "
                f"Data: {context}"
            )
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=60,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            total = summary_data['total_projects']
            at_risk = summary_data['at_risk']
            return (f"{total} active projects monitored — "
                    f"{'immediate attention required on ' + str(at_risk) + ' item(s).' if at_risk else 'portfolio is stable.'}")

    def _project_customer(self, proj):
        if isinstance(proj, dict):
            return proj.get('customer') or 'Other'
        return proj[2] or 'Other'

    def generate_executive_report_html(self, summary_data):
        now = datetime.now()
        week_start = (now - timedelta(days=7)).strftime('%b %d')
        week_end = now.strftime('%b %d, %Y')
        date_str = now.strftime('%B %d, %Y')
        time_str = now.strftime('%I:%M %p')
        email_sources = summary_data.get('email_sources_count', 0)

        ai_intro = self._generate_ai_intro(summary_data)

        # ── Normalize projects ─────────────────────────────────────────────────
        projects = []
        for proj in summary_data['projects']:
            if isinstance(proj, dict):
                projects.append({
                    'name': proj['name'],
                    'customer': proj.get('customer') or 'Other',
                    'status': proj['status'],
                    'progress': proj['progress'],
                    'owner': proj['owner'],
                })
            else:
                projects.append({
                    'name': proj[1],
                    'customer': proj[2] or 'Other',
                    'status': proj[3],
                    'progress': proj[4],
                    'owner': proj[5],
                })

        # ── Customer snapshot (traffic lights) ────────────────────────────────
        customer_status = {}
        for p in projects:
            c = p['customer']
            if c not in customer_status:
                customer_status[c] = {'on_track': 0, 'at_risk': 0, 'delayed': 0, 'completed': 0, 'other': 0}
            s = p['status']
            if s == 'On Track': customer_status[c]['on_track'] += 1
            elif s == 'At Risk': customer_status[c]['at_risk'] += 1
            elif s == 'Delayed': customer_status[c]['delayed'] += 1
            elif s == 'Completed': customer_status[c]['completed'] += 1
            else: customer_status[c]['other'] += 1

        snapshot_rows = ''
        for c_name in sorted(customer_status.keys()):
            cs = customer_status[c_name]
            total_c = sum(cs.values())
            # Overall signal: red if any delayed, yellow if any at_risk, green otherwise
            if cs['delayed'] > 0:
                signal_color = '#dc2626'
                signal_bg = '#fee2e2'
                signal_label = 'Action Required'
            elif cs['at_risk'] > 0:
                signal_color = '#d97706'
                signal_bg = '#fef9c3'
                signal_label = 'Monitor Closely'
            else:
                signal_color = '#16a34a'
                signal_bg = '#dcfce7'
                signal_label = 'On Track'

            status_chips = ''
            if cs['on_track']:
                status_chips += f'<span style="font-size:11px;color:#16a34a;margin-right:6px">✓ {cs["on_track"]} on track</span>'
            if cs['at_risk']:
                status_chips += f'<span style="font-size:11px;color:#d97706;margin-right:6px">⚠ {cs["at_risk"]} at risk</span>'
            if cs['delayed']:
                status_chips += f'<span style="font-size:11px;color:#dc2626;margin-right:6px">✗ {cs["delayed"]} delayed</span>'
            if cs['completed']:
                status_chips += f'<span style="font-size:11px;color:#94a3b8;margin-right:6px">● {cs["completed"]} done</span>'

            snapshot_rows += f"""
            <tr style="border-bottom:1px solid #f1f5f9">
              <td style="padding:11px 20px;font-weight:600;font-size:13px;color:#1e293b">{c_name}</td>
              <td style="padding:11px 16px;font-size:12px;color:#64748b">{total_c} project{'s' if total_c != 1 else ''}</td>
              <td style="padding:11px 16px">{status_chips}</td>
              <td style="padding:11px 16px;text-align:right">
                <span style="font-size:11px;font-weight:700;color:{signal_color};background:{signal_bg};padding:3px 10px;border-radius:99px">{signal_label}</span>
              </td>
            </tr>"""

        # ── Key Actions ────────────────────────────────────────────────────────
        actions = []
        for n in summary_data.get('project_notes', []):
            if n['type'] == 'blocker':
                actions.append({'project': n['project'], 'customer': n['customer'] or '—', 'note': n['note'], 'urgency': 'high'})
            elif n['status'] in ('At Risk', 'Delayed'):
                actions.append({'project': n['project'], 'customer': n['customer'] or '—', 'note': n['note'] or n['status'], 'urgency': 'med'})

        if actions:
            actions_rows = ''
            for a in actions[:8]:
                color = '#dc2626' if a['urgency'] == 'high' else '#d97706'
                icon = '⚠' if a['urgency'] == 'high' else '↗'
                actions_rows += f"""
                <tr style="border-bottom:1px solid #f8f8f8">
                  <td style="padding:10px 20px;width:28px;color:{color};font-size:13px">{icon}</td>
                  <td style="padding:10px 0 10px 0;font-weight:600;font-size:13px;color:#1e293b;white-space:nowrap;padding-right:16px">{a['project']}</td>
                  <td style="padding:10px 0;font-size:12px;color:#94a3b8;white-space:nowrap;padding-right:16px">{a['customer']}</td>
                  <td style="padding:10px 0 10px 0;font-size:13px;color:#64748b">{a['note']}</td>
                </tr>"""
            actions_section = f"""
  <div style="background:white;border:2px solid #fed7aa;border-radius:14px;overflow:hidden;margin-bottom:20px">
    <div style="padding:14px 20px 10px;border-bottom:1px solid #fff7ed;background:#fffbf5;display:flex;align-items:center;gap:8px">
      <div style="width:3px;height:14px;background:#F86442;border-radius:99px"></div>
      <span style="font-size:12px;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:0.08em">Actions Required</span>
      <span style="font-size:11px;background:#fef3c7;color:#d97706;padding:2px 8px;border-radius:99px;font-weight:600">{len(actions)}</span>
    </div>
    <table style="width:100%"><tbody>{actions_rows}</tbody></table>
  </div>"""
        else:
            actions_section = ''

        # ── All projects compact table ─────────────────────────────────────────
        # Build blocker lookup from notes
        blocker_map = {}
        for n in summary_data.get('project_notes', []):
            if n['type'] == 'blocker' and n['note']:
                blocker_map[n['project']] = n['note']

        proj_rows = ''
        last_customer = None
        for p in sorted(projects, key=lambda x: (x['customer'], x['name'])):
            sc = STATUS_COLORS.get(p['status'], {'bg': '#f1f5f9', 'text': '#475569', 'dot': '#94a3b8'})
            prog = p['progress']
            bar_fill = sc['dot']
            blocker_text = blocker_map.get(p['name'], '')

            # Insert customer separator only when customer changes
            if p['customer'] != last_customer:
                last_customer = p['customer']
                proj_rows += f"""
            <tr>
              <td colspan="5" style="padding:8px 20px 4px;background:#fafafa;border-top:1px solid #e8e2f4">
                <span style="font-size:10px;font-weight:700;color:#731FE3;text-transform:uppercase;letter-spacing:0.12em">{p['customer']}</span>
              </td>
            </tr>"""

            proj_rows += f"""
            <tr style="border-bottom:1px solid #f8fafc">
              <td style="padding:10px 20px 10px 28px;font-size:13px;font-weight:500;color:#1e293b">
                {p['name']}
                {f'<div style="font-size:11px;color:#ef4444;margin-top:2px">⚠ {blocker_text[:60]}{"..." if len(blocker_text)>60 else ""}</div>' if blocker_text else ''}
              </td>
              <td style="padding:10px 12px;white-space:nowrap">
                <span style="display:inline-flex;align-items:center;gap:5px;background:{sc['bg']};color:{sc['text']};padding:3px 9px;border-radius:99px;font-size:11px;font-weight:700">
                  <span style="width:5px;height:5px;border-radius:50%;background:{sc['dot']};display:inline-block"></span>
                  {p['status']}
                </span>
              </td>
              <td style="padding:10px 16px;min-width:120px">
                <div style="display:flex;align-items:center;gap:8px">
                  <div style="flex:1;height:5px;background:#e2e8f0;border-radius:99px;overflow:hidden;min-width:60px">
                    <div style="width:{prog}%;height:100%;background:{bar_fill};border-radius:99px"></div>
                  </div>
                  <span style="font-size:11px;color:#64748b;font-weight:600;min-width:28px">{prog}%</span>
                </div>
              </td>
              <td style="padding:10px 20px;font-size:12px;color:#94a3b8;white-space:nowrap">{p['owner']}</td>
            </tr>"""

        # ── Blockers compact list ──────────────────────────────────────────────
        blockers_html = ''
        for i, b in enumerate(summary_data['blockers'][:5]):
            is_last = i == len(summary_data['blockers'][:5]) - 1
            blockers_html += f'<div style="padding:8px 0;border-bottom:{'' if is_last else '1px solid #fff1f2'};display:flex;gap:10px;align-items:flex-start"><span style="color:#dc2626;font-weight:700;font-size:12px;flex-shrink:0;margin-top:1px">!</span><span style="font-size:13px;color:#334155;line-height:1.5">{b}</span></div>'

        # ── Accomplishments compact ────────────────────────────────────────────
        acc_html = ''
        for i, a in enumerate(summary_data['accomplishments'][:5]):
            is_last = i == len(summary_data['accomplishments'][:5]) - 1
            acc_html += f'<div style="padding:8px 0;border-bottom:{'' if is_last else '1px solid #f1f5f9'};display:flex;gap:10px;align-items:flex-start"><span style="color:#16a34a;font-weight:700;font-size:12px;flex-shrink:0;margin-top:1px">✓</span><span style="font-size:13px;color:#334155;line-height:1.5">{a}</span></div>'

        if not blockers_html:
            blockers_html = '<p style="color:#94a3b8;font-size:13px;padding:10px 0;margin:0">No blockers reported.</p>'
        if not acc_html:
            acc_html = '<p style="color:#94a3b8;font-size:13px;padding:10px 0;margin:0">No accomplishments recorded yet.</p>'

        # ── Metric strip ──────────────────────────────────────────────────────
        def metric(value, label, color):
            return f"""<div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;flex:1;min-width:100px;text-align:center">
              <div style="font-size:26px;font-weight:700;color:{color};font-family:'Inter Tight',sans-serif;line-height:1">{value}</div>
              <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-top:5px">{label}</div>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Executive Report — {date_str}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Inter+Tight:wght@600;700&display=swap" rel="stylesheet">
<style>* {{ box-sizing:border-box;margin:0;padding:0 }} body {{ font-family:'Inter',-apple-system,sans-serif;background:#F9F7F6;color:#0D061F;-webkit-font-smoothing:antialiased }}</style>
</head>
<body>
<div style="max-width:820px;margin:0 auto;padding:28px 16px 52px">

  <!-- Header bar -->
  <div style="background:linear-gradient(135deg,#0A0545 0%,#731FE3 100%);border-radius:14px;padding:32px 40px;margin-bottom:18px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px">
      <div style="width:30px;height:30px;border-radius:7px;background:rgba(255,255,255,0.15);display:flex;align-items:center;justify-content:center;font-family:'Inter Tight',sans-serif;font-weight:700;font-size:16px;color:white">A</div>
      <span style="font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:0.1em;text-transform:uppercase;font-weight:600">Autonomize AI · Project Intel</span>
    </div>
    <p style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;font-weight:600;margin-bottom:6px">Executive Summary · {week_start} – {week_end}</p>
    <p style="font-size:16px;color:rgba(255,255,255,0.92);line-height:1.6;font-weight:400;max-width:680px;margin-bottom:16px">{ai_intro}</p>
    <div style="display:flex;gap:16px;flex-wrap:wrap">
      <span style="font-size:12px;color:rgba(255,255,255,0.5)">📧 {email_sources} emails processed</span>
      <span style="font-size:12px;color:rgba(255,255,255,0.5)">🏢 {len(customer_status)} customers</span>
      <span style="font-size:12px;color:rgba(255,255,255,0.5)">⏱ {time_str}</span>
    </div>
  </div>

  <!-- Metric strip -->
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px">
    {metric(summary_data['total_projects'], 'Projects', '#731FE3')}
    {metric(summary_data['on_track'], 'On Track', '#16a34a')}
    {metric(summary_data['at_risk'], 'At Risk', '#d97706')}
    {metric(summary_data['delayed'], 'Delayed', '#dc2626')}
    {metric(summary_data.get('completed', 0), 'Completed', '#94a3b8')}
  </div>

  <!-- Customer snapshot -->
  <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;margin-bottom:18px">
    <div style="padding:13px 20px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:8px">
      <div style="width:3px;height:13px;background:#731FE3;border-radius:99px"></div>
      <span style="font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em">Customer Snapshot</span>
    </div>
    <table style="width:100%"><tbody>{snapshot_rows}</tbody></table>
  </div>

  {actions_section}

  <!-- Full project list -->
  <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;margin-bottom:18px">
    <div style="padding:13px 20px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:8px">
      <div style="width:3px;height:13px;background:#3b82f6;border-radius:99px"></div>
      <span style="font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em">All Projects</span>
      <span style="font-size:11px;color:#94a3b8;background:#f1f5f9;padding:2px 8px;border-radius:99px">{len(projects)}</span>
    </div>
    <table style="width:100%">
      <thead>
        <tr style="background:#f8fafc">
          <th style="padding:8px 20px 8px 28px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Project</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Status</th>
          <th style="padding:8px 16px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Progress</th>
          <th style="padding:8px 20px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0">Owner</th>
        </tr>
      </thead>
      <tbody>{proj_rows}</tbody>
    </table>
  </div>

  <!-- Highlights + Blockers side by side -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px">
    <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden">
      <div style="padding:12px 16px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:7px">
        <div style="width:3px;height:12px;background:#22c55e;border-radius:99px"></div>
        <span style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em">Wins This Week</span>
      </div>
      <div style="padding:4px 16px 10px">{acc_html}</div>
    </div>
    <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden">
      <div style="padding:12px 16px;border-bottom:1px solid #fff1f2;display:flex;align-items:center;gap:7px">
        <div style="width:3px;height:12px;background:#ef4444;border-radius:99px"></div>
        <span style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em">Open Blockers</span>
      </div>
      <div style="padding:4px 16px 10px">{blockers_html}</div>
    </div>
  </div>

  <!-- Footer -->
  <div style="text-align:center;padding-top:20px;border-top:1px solid #e2e8f0">
    <p style="font-size:11px;color:#94a3b8">Autonomize AI · Confidential · {date_str} · Auto-generated from {email_sources} email source{'s' if email_sources != 1 else ''}</p>
  </div>

</div>
</body>
</html>"""
        return html

    def generate_report_text(self, summary_data):
        now = datetime.now()
        lines = [
            f"EXECUTIVE REPORT — {now.strftime('%B %d, %Y')}",
            f"Projects: {summary_data['total_projects']} total | {summary_data['on_track']} on track | {summary_data['at_risk']} at risk | {summary_data['delayed']} delayed",
            "",
            "WINS THIS WEEK:",
        ]
        for a in summary_data['accomplishments'] or ['No accomplishments recorded.']:
            lines.append(f"  ✓ {a}")
        lines += ["", "OPEN BLOCKERS:"]
        for b in summary_data['blockers'] or ['No blockers reported.']:
            lines.append(f"  ! {b}")
        lines += ["", "PROJECTS:"]
        for n in summary_data.get('project_notes', []):
            lines.append(f"  {n['project']} ({n['customer']}) — {n['status']} — {n['note'] or 'No notes'}")
        return '\n'.join(lines)

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

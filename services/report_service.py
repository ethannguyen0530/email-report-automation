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

    def _executive_brief_fallback(self, summary_data):
        """Build a 3-sentence executive brief from raw data (no GPT required)."""
        total = summary_data['total_projects']
        on_track = summary_data['on_track']
        at_risk = summary_data['at_risk']
        delayed = summary_data['delayed']
        completed = summary_data.get('completed', 0)
        blockers = summary_data.get('blockers', [])
        notes = summary_data.get('project_notes', [])
        n_customers = len(set(self._project_customer(p) for p in summary_data.get('projects', [])))

        # Sentence 1 — portfolio health
        health_pct = round(on_track / total * 100) if total else 0
        s1 = f"{on_track} of {total} engagements across {n_customers} clients are on track ({health_pct}% portfolio health)."

        # Sentence 2 — risk / delay (pull names directly from projects list for accuracy)
        all_projects = summary_data.get('projects', [])
        flagged_names = []
        for p in all_projects:
            if isinstance(p, dict):
                pname, pstatus = p.get('project_name', ''), p.get('status', '')
            else:
                pname, pstatus = p[1], p[3]
            if pstatus in ('At Risk', 'Delayed'):
                flagged_names.append(pname)
        issues = at_risk + delayed
        if issues:
            name_clause = f" — {', '.join(flagged_names)}" if flagged_names else ""
            verb = "require" if issues > 1 else "requires"
            s2 = f"{issues} engagement{'s' if issues > 1 else ''}{name_clause} {verb} immediate leadership review."
        else:
            s2 = "All engagements are progressing within expected parameters."

        # Sentence 3 — blocker or completion signal
        if blockers:
            brief_blocker = blockers[0][:90].rstrip('.,') + ('...' if len(blockers[0]) > 90 else '.')
            s3 = f"Active blocker: {brief_blocker}"
        elif completed:
            s3 = f"{completed} engagement{'s' if completed > 1 else ''} delivered this period — client close-out communication recommended."
        else:
            s3 = "No active blockers reported; maintain standard cadence."

        return f"{s1} {s2} {s3}"

    def _generate_ai_intro(self, summary_data):
        """Generate a 3-sentence executive brief via GPT, or fall back to structured data."""
        if not config.OPENAI_API_KEY:
            return self._executive_brief_fallback(summary_data)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            blockers = summary_data.get('blockers', [])
            all_projects = summary_data.get('projects', [])
            flagged = []
            for p in all_projects:
                if isinstance(p, dict):
                    pname, pstatus = p.get('project_name', ''), p.get('status', '')
                else:
                    pname, pstatus = p[1], p[3]
                if pstatus in ('At Risk', 'Delayed'):
                    flagged.append(pname)
            context = (
                f"Portfolio: {summary_data['total_projects']} projects, "
                f"{summary_data['on_track']} on track, "
                f"{summary_data['at_risk']} at risk, "
                f"{summary_data['delayed']} delayed, "
                f"{summary_data.get('completed', 0)} completed. "
            )
            if flagged:
                context += f"At-risk engagements: {', '.join(flagged[:3])}. "
            if blockers:
                context += f"Top blocker: {blockers[0][:120]}. "
            prompt = (
                "Write exactly 3 sentences for a C-suite executive project status report. "
                "Sentence 1: overall portfolio health as a single crisp fact. "
                "Sentence 2: the most critical risk or delay requiring leadership action. "
                "Sentence 3: the top blocker or a delivery milestone. "
                "Rules: executive business language, no filler words, max 20 words per sentence, "
                "no bullet points, no headers, plain prose only. "
                f"Data: {context}"
            )
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=120,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return self._executive_brief_fallback(summary_data)

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
        F = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

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
            if cs['delayed'] > 0:
                signal_color = '#dc2626'; signal_bg = '#fee2e2'; signal_label = 'Action Required'
            elif cs['at_risk'] > 0:
                signal_color = '#d97706'; signal_bg = '#fef9c3'; signal_label = 'Monitor Closely'
            else:
                signal_color = '#16a34a'; signal_bg = '#dcfce7'; signal_label = 'On Track'

            status_chips = ''
            if cs['on_track']:
                status_chips += f'<span style="font-size:11px;color:#16a34a;font-family:{F};margin-right:8px">{cs["on_track"]} on track</span>'
            if cs['at_risk']:
                status_chips += f'<span style="font-size:11px;color:#d97706;font-family:{F};margin-right:8px">{cs["at_risk"]} at risk</span>'
            if cs['delayed']:
                status_chips += f'<span style="font-size:11px;color:#dc2626;font-family:{F};margin-right:8px">{cs["delayed"]} delayed</span>'
            if cs['completed']:
                status_chips += f'<span style="font-size:11px;color:#94a3b8;font-family:{F}">{cs["completed"]} completed</span>'

            snapshot_rows += f"""
            <tr style="border-bottom:1px solid #f1f5f9">
              <td style="padding:11px 20px;font-weight:600;font-size:13px;color:#1e293b;font-family:{F}">{c_name}</td>
              <td style="padding:11px 16px;font-size:12px;color:#64748b;white-space:nowrap;font-family:{F}">{total_c} project{'s' if total_c != 1 else ''}</td>
              <td style="padding:11px 16px">{status_chips}</td>
              <td style="padding:11px 16px;text-align:right">
                <span style="font-size:11px;font-weight:700;color:{signal_color};background:{signal_bg};padding:3px 10px;border-radius:99px;white-space:nowrap;font-family:{F}">{signal_label}</span>
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
                icon = '!' if a['urgency'] == 'high' else '&rarr;'
                actions_rows += f"""
                <tr style="border-bottom:1px solid #f8f8f8">
                  <td style="padding:10px 20px;width:28px;color:{color};font-size:13px;font-family:{F}">{icon}</td>
                  <td style="padding:10px 16px 10px 0;font-weight:600;font-size:13px;color:#1e293b;white-space:nowrap;font-family:{F}">{a['project']}</td>
                  <td style="padding:10px 16px 10px 0;font-size:12px;color:#94a3b8;white-space:nowrap;font-family:{F}">{a['customer']}</td>
                  <td style="padding:10px 0;font-size:13px;color:#64748b;font-family:{F}">{a['note']}</td>
                </tr>"""
            actions_section = f"""
<tr><td height="18"></td></tr>
<tr><td style="background:white;border:2px solid #fed7aa;border-radius:14px;overflow:hidden">
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td style="padding:14px 20px;border-bottom:1px solid #fff7ed;background:#fffbf5">
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="3" style="background:#F86442;border-radius:99px;font-size:1px;line-height:1">&nbsp;</td>
          <td style="padding-left:8px;font-size:12px;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:0.08em;font-family:{F}">Actions Required</td>
          <td style="padding-left:8px"><span style="font-size:11px;background:#fef3c7;color:#d97706;padding:2px 8px;border-radius:99px;font-weight:600;font-family:{F}">{len(actions)}</span></td>
        </tr>
      </table>
    </td></tr>
    <tr><td><table width="100%" cellpadding="0" cellspacing="0" border="0"><tbody>{actions_rows}</tbody></table></td></tr>
  </table>
</td></tr>"""
        else:
            actions_section = ''

        # ── All projects compact table ─────────────────────────────────────────
        blocker_map = {}
        for n in summary_data.get('project_notes', []):
            if n['type'] == 'blocker' and n['note']:
                blocker_map[n['project']] = n['note']

        proj_rows = ''
        last_customer = None
        for p in sorted(projects, key=lambda x: (x['customer'], x['name'])):
            sc = STATUS_COLORS.get(p['status'], {'bg': '#f1f5f9', 'text': '#475569', 'dot': '#94a3b8'})
            prog = p['progress']
            blocker_text = blocker_map.get(p['name'], '')

            if p['customer'] != last_customer:
                last_customer = p['customer']
                proj_rows += f"""
            <tr>
              <td colspan="4" style="padding:8px 20px 4px;background:#fafafa;border-top:1px solid #e8e2f4">
                <span style="font-size:10px;font-weight:700;color:#731FE3;text-transform:uppercase;letter-spacing:0.12em;font-family:{F}">{p['customer']}</span>
              </td>
            </tr>"""

            pill = (f'<span style="display:inline-block;background:{sc["bg"]};color:{sc["text"]};'
                    f'padding:3px 9px;border-radius:99px;font-size:11px;font-weight:700;white-space:nowrap;font-family:{F}">'
                    f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
                    f'background:{sc["dot"]};vertical-align:middle;margin-right:4px"></span>'
                    f'{p["status"]}</span>')

            prog_bar = (f'<table cellpadding="0" cellspacing="0" border="0"><tr>'
                        f'<td style="width:70px;background:#e2e8f0;border-radius:99px;overflow:hidden;height:5px;vertical-align:middle">'
                        f'<div style="width:{prog}%;height:5px;background:{sc["dot"]};border-radius:99px;min-width:2px"></div></td>'
                        f'<td style="padding-left:8px;font-size:11px;color:#64748b;font-weight:600;white-space:nowrap;font-family:{F}">{prog}%</td>'
                        f'</tr></table>')

            blocker_div = (f'<div style="font-size:11px;color:#ef4444;margin-top:2px;font-family:{F}">'
                           f'! {blocker_text[:60]}{"..." if len(blocker_text) > 60 else ""}</div>') if blocker_text else ''

            proj_rows += f"""
            <tr style="border-bottom:1px solid #f8fafc">
              <td style="padding:10px 20px 10px 28px;font-size:13px;font-weight:500;color:#1e293b;font-family:{F}">{p['name']}{blocker_div}</td>
              <td style="padding:10px 12px;white-space:nowrap">{pill}</td>
              <td style="padding:10px 16px">{prog_bar}</td>
              <td style="padding:10px 20px;font-size:12px;color:#94a3b8;white-space:nowrap;font-family:{F}">{p['owner']}</td>
            </tr>"""

        # ── Blockers compact list ──────────────────────────────────────────────
        blockers_html = ''
        blockers_list = summary_data['blockers'][:5]
        for i, b in enumerate(blockers_list):
            border = '' if i == len(blockers_list) - 1 else '1px solid #fff1f2'
            blockers_html += (f'<div style="padding:8px 0;border-bottom:{border}">'
                              f'<table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>'
                              f'<td width="16" valign="top" style="color:#dc2626;font-weight:700;font-size:14px;font-family:{F};padding-right:10px;line-height:1.5">!</td>'
                              f'<td style="font-size:13px;color:#334155;line-height:1.5;font-family:{F}">{b}</td>'
                              f'</tr></table></div>')

        # ── Accomplishments compact ────────────────────────────────────────────
        acc_html = ''
        acc_list = summary_data['accomplishments'][:5]
        for i, a in enumerate(acc_list):
            border = '' if i == len(acc_list) - 1 else '1px solid #f1f5f9'
            acc_html += (f'<div style="padding:8px 0;border-bottom:{border}">'
                         f'<table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>'
                         f'<td width="16" valign="top" style="color:#16a34a;font-weight:700;font-size:14px;font-family:{F};padding-right:10px;line-height:1.5">+</td>'
                         f'<td style="font-size:13px;color:#334155;line-height:1.5;font-family:{F}">{a}</td>'
                         f'</tr></table></div>')

        if not blockers_html:
            blockers_html = f'<p style="color:#94a3b8;font-size:13px;padding:10px 0;margin:0;font-family:{F}">No blockers reported.</p>'
        if not acc_html:
            acc_html = f'<p style="color:#94a3b8;font-size:13px;padding:10px 0;margin:0;font-family:{F}">No accomplishments recorded yet.</p>'

        # ── Helpers ───────────────────────────────────────────────────────────
        def metric_td(value, label, color, last=False):
            pad = '' if last else 'padding-right:10px;'
            return (f'<td style="{pad}vertical-align:top">'
                    f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                    f'<td style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;text-align:center">'
                    f'<div style="font-size:26px;font-weight:700;color:{color};line-height:1;font-family:{F}">{value}</div>'
                    f'<div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-top:5px;font-family:{F}">{label}</div>'
                    f'</td></tr></table></td>')

        def section_hdr(color, label, badge=None):
            badge_html = (f'<td style="padding-left:8px"><span style="font-size:11px;color:#94a3b8;'
                          f'background:#f1f5f9;padding:2px 8px;border-radius:99px;font-family:{F}">{badge}</span></td>') if badge is not None else ''
            return (f'<table cellpadding="0" cellspacing="0" border="0"><tr>'
                    f'<td width="3" style="background:{color};border-radius:99px;font-size:1px;line-height:13px">&nbsp;</td>'
                    f'<td style="padding-left:8px;font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;font-family:{F}">{label}</td>'
                    f'{badge_html}</tr></table>')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Executive Report — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#F9F7F6">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F9F7F6">
<tr><td align="center" style="padding:28px 16px 52px">
<table cellpadding="0" cellspacing="0" border="0" style="max-width:820px;width:100%">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#0A0545 0%,#731FE3 100%);border-radius:14px;padding:32px 40px">
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td>
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="30" height="30" style="background:rgba(255,255,255,0.15);border-radius:7px;text-align:center;vertical-align:middle;font-weight:700;font-size:16px;color:white;font-family:{F}">A</td>
          <td style="padding-left:10px;font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:0.1em;text-transform:uppercase;font-weight:600;font-family:{F}">AUTONOMIZE AI &middot; PROJECT INTEL</td>
        </tr>
      </table>
    </td></tr>
    <tr><td height="18"></td></tr>
    <tr><td style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.12em;font-weight:600;font-family:{F};padding-bottom:6px">EXECUTIVE SUMMARY &middot; {week_start} &ndash; {week_end}</td></tr>
    <tr><td style="font-size:16px;color:rgba(255,255,255,0.92);line-height:1.6;font-weight:400;font-family:{F};padding-bottom:16px">{ai_intro}</td></tr>
    <tr><td>
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="font-size:12px;color:rgba(255,255,255,0.5);font-family:{F}">{email_sources} emails &nbsp;&middot;&nbsp; {len(customer_status)} customers &nbsp;&middot;&nbsp; {time_str}</td>
        </tr>
      </table>
    </td></tr>
  </table>
</td></tr>

<tr><td height="18"></td></tr>

<!-- Metric Strip -->
<tr><td>
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      {metric_td(summary_data['total_projects'], 'Projects', '#731FE3')}
      {metric_td(summary_data['on_track'], 'On Track', '#16a34a')}
      {metric_td(summary_data['at_risk'], 'At Risk', '#d97706')}
      {metric_td(summary_data['delayed'], 'Delayed', '#dc2626')}
      {metric_td(summary_data.get('completed', 0), 'Completed', '#94a3b8', last=True)}
    </tr>
  </table>
</td></tr>

<tr><td height="18"></td></tr>

<!-- Customer Snapshot -->
<tr><td style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td style="padding:13px 20px;border-bottom:1px solid #f1f5f9">{section_hdr('#731FE3', 'Customer Snapshot')}</td></tr>
    <tr><td><table width="100%" cellpadding="0" cellspacing="0" border="0"><tbody>{snapshot_rows}</tbody></table></td></tr>
  </table>
</td></tr>

{actions_section}

<tr><td height="18"></td></tr>

<!-- All Projects -->
<tr><td style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td style="padding:13px 20px;border-bottom:1px solid #f1f5f9">{section_hdr('#3b82f6', 'All Projects', len(projects))}</td></tr>
    <tr><td>
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <thead>
          <tr style="background:#f8fafc">
            <th style="padding:8px 20px 8px 28px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0;font-family:{F}">Project</th>
            <th style="padding:8px 12px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0;font-family:{F}">Status</th>
            <th style="padding:8px 16px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0;font-family:{F}">Progress</th>
            <th style="padding:8px 20px;text-align:left;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e2e8f0;font-family:{F}">Owner</th>
          </tr>
        </thead>
        <tbody>{proj_rows}</tbody>
      </table>
    </td></tr>
  </table>
</td></tr>

<tr><td height="20"></td></tr>

<!-- Wins + Blockers side by side -->
<tr><td>
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td width="49%" valign="top" style="background:white;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr><td style="padding:12px 16px;border-bottom:1px solid #f1f5f9">{section_hdr('#22c55e', 'Wins This Week')}</td></tr>
          <tr><td style="padding:4px 16px 10px">{acc_html}</td></tr>
        </table>
      </td>
      <td width="2%">&nbsp;</td>
      <td width="49%" valign="top" style="background:white;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr><td style="padding:12px 16px;border-bottom:1px solid #fff1f2">{section_hdr('#ef4444', 'Open Blockers')}</td></tr>
          <tr><td style="padding:4px 16px 10px">{blockers_html}</td></tr>
        </table>
      </td>
    </tr>
  </table>
</td></tr>

<tr><td height="20"></td></tr>

<!-- Footer -->
<tr><td style="text-align:center;padding-top:20px;border-top:1px solid #e2e8f0">
  <p style="font-size:11px;color:#94a3b8;font-family:{F};margin:0">Autonomize AI &middot; Confidential &middot; {date_str} &middot; Auto-generated from {email_sources} email source{'s' if email_sources != 1 else ''}</p>
</td></tr>

</table>
</td></tr>
</table>
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

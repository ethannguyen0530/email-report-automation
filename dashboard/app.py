import os
import json
import logging
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from database.schema import DatabaseManager
import config

log = logging.getLogger(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist'))
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'csv', 'xlsx', 'pptx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder='templates')
CORS(app)
db = DatabaseManager(config.DB_PATH)

# ── SSE broadcast ───────────────────────────────────────────────────────────
_sse_clients = []
_sse_lock = threading.Lock()
_last_scan_result = {'time': None, 'new_emails': 0, 'total': 0}

def _sse_broadcast(data):
    with _sse_lock:
        for q in list(_sse_clients):
            try:
                q.put_nowait(data)
            except Exception:
                pass


# ── Scheduler ──────────────────────────────────────────────────────────────
def run_email_scan():
    """Background job: fetch new emails and extract project data."""
    log.info("Scheduled email scan starting...")
    try:
        from services.gmail_service import GmailService
        from services.extraction_service import ExtractionService
        gmail = GmailService(config.GMAIL_CREDENTIALS_FILE)
        if not gmail.service:
            log.warning("Scheduled scan skipped: Gmail auth failed")
            _sse_broadcast({'type': 'scan_complete', 'new_emails': 0, 'error': 'Gmail auth failed',
                            'time': datetime.now().isoformat()})
            return
        extraction = ExtractionService()
        emails = gmail.get_emails(query=config.GMAIL_QUERY, max_results=config.GMAIL_MAX_RESULTS)
        new_count = 0
        flagged_count = 0
        for email in emails:
            is_new = db.insert_email(email['id'], email['from'], email['subject'], email['body'], email['date'])
            if not is_new:
                continue  # already processed in a previous scan — hard rule: never re-process
            extracted = extraction.extract_project_info(email['body'], email['subject'])
            is_project = extracted.get('is_project_related', True)
            confidence = extracted.get('confidence', 50)

            if is_project and confidence >= 40:
                cust_id = db.get_or_create_customer(extracted.get('customer'))
                if cust_id:
                    proj_id = db.get_or_create_project(
                        cust_id,
                        extracted.get('project', email['subject'][:60]),
                        extracted.get('status', 'In Progress'),
                        extracted.get('progress', 0),
                        extracted.get('owner', 'Unknown'),
                    )
                    db.insert_update(
                        proj_id,
                        email['date'],
                        extracted.get('summary') or extracted.get('milestone') or email['subject'][:120],
                        extracted.get('blocker'),
                        extracted.get('milestone'),
                        extracted.get('owner', 'Unknown'),
                        gmail_id=email['id'],
                        confidence=confidence,
                    )

            if not is_project or confidence < 60:
                reason = extracted.get('confidence_note') or (
                    'Not identified as project update' if not is_project else f'Low confidence ({confidence}/100)'
                )
                db.mark_email_flagged(email['id'], reason)
                flagged_count += 1

            db.mark_email_processed(email['id'])
            new_count += 1
        conn = db.get_connection()
        total_emails = conn.execute('SELECT COUNT(*) FROM emails').fetchone()[0]
        conn.close()
        now = datetime.now().isoformat()
        _last_scan_result.update({'time': now, 'new_emails': new_count, 'total': total_emails})
        _sse_broadcast({'type': 'scan_complete', 'new_emails': new_count, 'total': total_emails,
                        'flagged': flagged_count, 'time': now})
        log.info("Scheduled email scan complete: %d new emails processed (%d flagged) of %d fetched",
                 new_count, flagged_count, len(emails))
    except Exception as e:
        log.error("Scheduled scan error: %s", e)
        _sse_broadcast({'type': 'scan_complete', 'new_emails': 0, 'error': str(e),
                        'time': datetime.now().isoformat()})


def run_report_send():
    """Background job: generate and send the executive report."""
    log.info("Scheduled report send starting...")
    try:
        from services.report_service import ReportService
        from services.slack_service import SlackService
        summary = db.get_executive_summary()
        rs = ReportService()
        ss = SlackService()
        summary['ai_brief'] = rs._generate_ai_intro(summary)  # generate once; reused by email + Slack
        html = rs.generate_executive_report_html(summary)
        # Use DB recipients, fall back to .env
        recipients = db.get_recipient_emails() or config.REPORT_RECIPIENTS
        email_ok = rs.send_email_report(
            recipients,
            f"Executive Project Summary - {datetime.now().strftime('%Y-%m-%d')}",
            html,
        )
        slack_ok = ss.send_report(summary)
        log.info("Scheduled report send complete: email=%s slack=%s", email_ok, slack_ok)
    except Exception as e:
        log.error("Scheduled report send error: %s", e)


def start_scheduler():
    if config.SCAN_INTERVAL_MINUTES <= 0 and not config.REPORT_SEND_TIME:
        return
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True)
    if config.SCAN_INTERVAL_MINUTES > 0:
        scheduler.add_job(run_email_scan, 'interval', minutes=config.SCAN_INTERVAL_MINUTES,
                          id='email_scan', replace_existing=True)
        log.info("Scheduler: email scan every %d min", config.SCAN_INTERVAL_MINUTES)
    if config.REPORT_SEND_TIME:
        scheduler.add_job(run_report_send, 'cron',
                          hour=config.REPORT_SEND_HOUR, minute=config.REPORT_SEND_MINUTE,
                          id='report_send', replace_existing=True)
        log.info("Scheduler: report send daily at %s", config.REPORT_SEND_TIME)
    scheduler.start()


# Start scheduler once when the module loads (gunicorn imports this once per worker)
# Guard against double-start in Flask debug reloader (second process sets WERKZEUG_RUN_MAIN)
_is_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
_is_main_process = not config.FLASK_DEBUG or _is_reloader_child
if _is_main_process:
    start_scheduler()


# ── Legacy HTML routes ──────────────────────────────────────────────────────
@app.route('/html')
def executive_dashboard():
    summary = db.get_executive_summary()
    return render_template('executive_dashboard.html', data=summary)

@app.route('/html/customer/<int:customer_id>')
def customer_view(customer_id):
    customers = db.get_all_customers()
    customer = next((c for c in customers if c[0] == customer_id), None)
    if not customer:
        return "Customer not found", 404
    projects = db.get_customer_projects(customer_id)
    return render_template('customer_view.html', customer=customer, projects=projects)

@app.route('/html/project/<int:project_id>')
def project_view(project_id):
    all_projects = db.get_all_projects()
    project = next((p for p in all_projects if p[0] == project_id), None)
    if not project:
        return "Project not found", 404
    updates = db.get_project_updates(project_id)
    return render_template('project_view.html', project=project, updates=updates)


# ── JSON API ────────────────────────────────────────────────────────────────
@app.route('/api/summary')
def api_summary():
    data = db.get_executive_summary()
    data['projects'] = [
        {'id': r[0], 'name': r[1], 'customer': r[2], 'status': r[3],
         'progress': r[4], 'owner': r[5], 'last_updated': r[6]}
        for r in data['projects']
    ]
    return jsonify(data)

@app.route('/api/report')
def api_report():
    from services.report_service import ReportService
    summary = db.get_executive_summary()
    rs = ReportService()
    return rs.generate_executive_report_html(summary), 200, {'Content-Type': 'text/html'}

@app.route('/api/send-report', methods=['POST'])
def send_report():
    from services.report_service import ReportService
    from services.slack_service import SlackService
    summary = db.get_executive_summary()
    rs = ReportService()
    ss = SlackService()
    html = rs.generate_executive_report_html(summary)
    recipients = db.get_recipient_emails() or config.REPORT_RECIPIENTS
    email_ok = rs.send_email_report(
        recipients,
        f"Executive Project Summary - {datetime.now().strftime('%Y-%m-%d')}",
        html,
    )
    slack_ok = ss.send_report(summary)
    return jsonify({'ok': True, 'email': email_ok, 'slack': slack_ok, 'recipients': len(recipients)})

@app.route('/api/customers')
def api_customers():
    rows = db.get_all_customers()
    return jsonify([{'id': r[0], 'name': r[1]} for r in rows if r[1] not in ('Unknown', 'Unknown Customer')])

@app.route('/api/customers/<int:customer_id>')
def api_customer(customer_id):
    customers = db.get_all_customers()
    customer = next((c for c in customers if c[0] == customer_id), None)
    if not customer:
        return jsonify({'error': 'Not found'}), 404
    projects = db.get_customer_projects(customer_id)
    return jsonify({
        'id': customer[0], 'name': customer[1],
        'projects': [{'id': p[0], 'name': p[1], 'status': p[2], 'progress': p[3], 'owner': p[4]}
                     for p in projects]
    })

@app.route('/api/projects')
def api_projects():
    rows = db.get_all_projects()
    return jsonify([
        {'id': r[0], 'name': r[1], 'customer': r[2], 'status': r[3],
         'progress': r[4], 'owner': r[5], 'last_updated': r[6]}
        for r in rows
    ])

@app.route('/api/projects/<int:project_id>')
def api_project(project_id):
    all_projects = db.get_all_projects()
    project = next((p for p in all_projects if p[0] == project_id), None)
    if not project:
        return jsonify({'error': 'Not found'}), 404
    updates = db.get_project_updates(project_id)
    return jsonify({
        'id': project[0], 'name': project[1], 'customer': project[2],
        'status': project[3], 'progress': project[4], 'owner': project[5],
        'updates': [{'id': u[0], 'date': u[1], 'summary': u[2], 'blocker': u[3],
                     'milestone': u[4], 'owner': u[5]}
                    for u in updates]
    })

@app.route('/api/projects/<int:project_id>', methods=['PATCH'])
def update_project(project_id):
    data = request.get_json()
    conn = db.get_connection()
    cursor = conn.cursor()
    allowed = {'status', 'progress_percent', 'owner'}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        conn.close()
        return jsonify({'error': 'No valid fields'}), 400
    sets = ', '.join(f'{k} = ?' for k in updates)
    cursor.execute(f'UPDATE projects SET {sets} WHERE id = ?', list(updates.values()) + [project_id])
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/email-stats')
def api_email_stats():
    """Email counts: all-time, weekly, monthly, and per customer."""
    conn = db.get_connection()
    total = conn.execute('SELECT COUNT(*) FROM emails').fetchone()[0]
    weekly = conn.execute(
        "SELECT COUNT(*) FROM emails WHERE received_at >= datetime('now', '-7 days')"
    ).fetchone()[0]
    monthly = conn.execute(
        "SELECT COUNT(*) FROM emails WHERE received_at >= datetime('now', '-30 days')"
    ).fetchone()[0]
    # Count distinct emails per customer (via gmail_id link in updates).
    # COALESCE fallback handles legacy rows without gmail_id.
    per_customer_rows = conn.execute("""
        SELECT c.name,
               COUNT(DISTINCT CASE WHEN u.gmail_id IS NOT NULL THEN u.gmail_id
                                   ELSE CAST(u.id AS TEXT) END) as email_count
        FROM updates u
        JOIN projects p ON p.id = u.project_id
        JOIN customers c ON c.id = p.customer_id
        WHERE c.name NOT IN ('Unknown', 'Unknown Customer')
        GROUP BY c.name
        ORDER BY email_count DESC
        LIMIT 20
    """).fetchall()
    flagged = conn.execute('SELECT COUNT(*) FROM emails WHERE flagged=1').fetchone()[0]
    conn.close()
    return jsonify({
        'total': total,
        'weekly': weekly,
        'monthly': monthly,
        'flagged': flagged,
        'per_customer': [{'name': r[0], 'count': r[1]} for r in per_customer_rows],
    })

@app.route('/api/emails')
def api_emails():
    customer = request.args.get('customer', '').strip()
    conn = db.get_connection()
    if customer:
        rows = conn.execute("""
            SELECT DISTINCT e.id, e.gmail_id, e.sender, e.subject, e.body,
                   e.received_at, e.processed, e.processed_at,
                   COALESCE(e.flagged, 0), e.flag_reason,
                   (SELECT u2.summary FROM updates u2 WHERE u2.gmail_id = e.gmail_id ORDER BY u2.created_at DESC LIMIT 1)
            FROM emails e
            JOIN updates u ON u.gmail_id = e.gmail_id
            JOIN projects p ON u.project_id = p.id
            JOIN customers c ON c.id = p.customer_id
            WHERE c.name = ?
            ORDER BY e.received_at DESC LIMIT 50
        """, (customer,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT e.id, e.gmail_id, e.sender, e.subject, e.body,
                   e.received_at, e.processed, e.processed_at,
                   COALESCE(e.flagged, 0), e.flag_reason,
                   (SELECT u.summary FROM updates u WHERE u.gmail_id = e.gmail_id ORDER BY u.created_at DESC LIMIT 1)
            FROM emails e ORDER BY e.received_at DESC LIMIT 50
        """).fetchall()
    conn.close()
    return jsonify([
        {'id': r[0], 'gmail_id': r[1], 'sender': r[2], 'subject': r[3],
         'body': r[4], 'date': r[5], 'processed': bool(r[6]), 'processed_at': r[7],
         'flagged': bool(r[8]), 'flag_reason': r[9], 'ai_summary': r[10]}
        for r in rows
    ])

@app.route('/api/email-detail/<gmail_id>')
def email_detail(gmail_id):
    conn = db.get_connection()
    row = conn.execute(
        'SELECT id, gmail_id, sender, subject, body, received_at, processed, processed_at, '
        'COALESCE(flagged, 0), flag_reason FROM emails WHERE gmail_id = ?',
        (gmail_id,)
    ).fetchone()
    update_row = conn.execute(
        'SELECT summary, milestone, blocker, COALESCE(confidence, 0) FROM updates WHERE gmail_id = ? ORDER BY created_at DESC LIMIT 1',
        (gmail_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Email not found — this item may be from before email tracking was enabled'}), 404
    return jsonify({
        'id': row[0], 'gmail_id': row[1], 'sender': row[2], 'subject': row[3],
        'body': row[4], 'date': row[5], 'processed': bool(row[6]), 'processed_at': row[7],
        'flagged': bool(row[8]), 'flag_reason': row[9],
        'ai_summary': update_row[0] if update_row else None,
        'milestone': update_row[1] if update_row else None,
        'blocker': update_row[2] if update_row else None,
        'confidence': update_row[3] if update_row else None,
    })

@app.route('/api/health')
def api_health():
    data = db.get_project_health_scores()
    data['projects'] = [p for p in data['projects'] if p.get('customer') not in (None, 'Unknown', 'Unknown Customer')]
    if data['projects']:
        data['portfolio_score'] = int(sum(p['score'] for p in data['projects']) / len(data['projects']))
    return jsonify(data)

@app.route('/api/alerts')
def api_alerts():
    stale = db.get_stale_customers(days=7)
    conn = db.get_connection()
    flagged = conn.execute('SELECT COUNT(*) FROM emails WHERE flagged=1').fetchone()[0]
    conn.close()
    return jsonify({'stale_customers': stale, 'flagged_emails': flagged})

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400
    cid, is_new = db.add_customer(name)
    if cid is None:
        return jsonify({'error': 'Invalid customer name'}), 400
    return jsonify({'ok': True, 'id': cid, 'is_new': is_new})

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    db.delete_customer(customer_id)
    return jsonify({'ok': True})

@app.route('/api/process-file', methods=['POST'])
def process_file():
    """Process an uploaded file through the same extraction pipeline as emails."""
    data = request.get_json()
    filename = data.get('filename', '')
    if not filename:
        return jsonify({'error': 'filename required'}), 400
    import os
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    def _process():
        try:
            from services.extraction_service import ExtractionService
            from services.file_extractor import extract_text_from_bytes
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            with open(filepath, 'rb') as fh:
                raw_bytes = fh.read()
            text = extract_text_from_bytes(raw_bytes, ext, filename)

            extraction = ExtractionService()
            subject = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
            extracted = extraction.extract_project_info(text, subject)
            is_project = extracted.get('is_project_related', True)
            confidence = extracted.get('confidence', 50)

            # Use a synthetic gmail_id for dedup — file uploads are idempotent per filename
            synthetic_id = f"file:{filename}"
            is_new = db.insert_email(synthetic_id, f"Upload: {filename}", filename, text[:2000], datetime.now().isoformat())

            if not is_new:
                _sse_broadcast({'type': 'file_processed', 'filename': filename, 'status': 'duplicate'})
                return

            if is_project and confidence >= 40:
                cust_id = db.get_or_create_customer(extracted.get('customer'))
                if cust_id:
                    proj_id = db.get_or_create_project(
                        cust_id,
                        extracted.get('project', subject[:60]),
                        extracted.get('status', 'In Progress'),
                        extracted.get('progress', 0),
                        extracted.get('owner', 'Unknown'),
                    )
                    db.insert_update(
                        proj_id, datetime.now().isoformat(),
                        extracted.get('summary') or extracted.get('milestone') or subject[:120],
                        extracted.get('blocker'), extracted.get('milestone'),
                        extracted.get('owner', 'Unknown'),
                        gmail_id=synthetic_id, confidence=confidence,
                    )

            if not is_project or confidence < 60:
                db.mark_email_flagged(synthetic_id, extracted.get('confidence_note') or 'Low confidence file extraction')

            db.mark_email_processed(synthetic_id)
            _sse_broadcast({'type': 'file_processed', 'filename': filename,
                            'customer': extracted.get('customer'), 'project': extracted.get('project'),
                            'confidence': confidence, 'status': 'ok'})
        except Exception as e:
            log.error("File processing error: %s", e)
            _sse_broadcast({'type': 'file_processed', 'filename': filename, 'status': 'error', 'error': str(e)})

    threading.Thread(target=_process, daemon=True).start()
    return jsonify({'ok': True, 'message': 'Processing started'})

@app.route('/api/scan-now', methods=['POST'])
def scan_now():
    t = threading.Thread(target=run_email_scan, daemon=True)
    t.start()
    return jsonify({'ok': True, 'message': 'Scan started in background'})

@app.route('/api/status')
def api_status():
    conn = db.get_connection()
    total = conn.execute('SELECT COUNT(*) FROM emails').fetchone()[0]
    processed = conn.execute('SELECT COUNT(*) FROM emails WHERE processed=1').fetchone()[0]
    flagged = conn.execute('SELECT COUNT(*) FROM emails WHERE flagged=1').fetchone()[0]
    conn.close()
    return jsonify({
        'total_emails': total,
        'processed_emails': processed,
        'flagged_emails': flagged,
        'last_scan': _last_scan_result.get('time'),
        'scan_interval_minutes': config.SCAN_INTERVAL_MINUTES,
        'report_send_time': config.REPORT_SEND_TIME or None,
    })

@app.route('/api/stream')
def sse_stream():
    """Server-Sent Events — pushes scan_complete events to connected dashboards."""
    def event_gen():
        q = queue.Queue()
        with _sse_lock:
            _sse_clients.append(q)
        try:
            # Send current status immediately on connect
            yield f"data: {json.dumps({'type': 'connected', **_last_scan_result})}\n\n"
            while True:
                try:
                    msg = q.get(timeout=25)
                    yield f"data: {json.dumps(msg)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            with _sse_lock:
                try:
                    _sse_clients.remove(q)
                except ValueError:
                    pass

    return Response(event_gen(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
                             'Connection': 'keep-alive'})

@app.route('/api/recipients', methods=['GET'])
def get_recipients():
    return jsonify(db.get_recipients())

@app.route('/api/recipients', methods=['POST'])
def add_recipient():
    data = request.get_json()
    email = (data.get('email') or '').strip().lower()
    name = (data.get('name') or '').strip()
    position = (data.get('position') or '').strip()
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email required'}), 400
    rid = db.add_recipient(email, name, position)
    if rid is None:
        return jsonify({'error': 'Email already exists'}), 409
    return jsonify({'ok': True, 'id': rid})

@app.route('/api/recipients/<int:recipient_id>', methods=['DELETE'])
def remove_recipient(recipient_id):
    db.remove_recipient(recipient_id)
    return jsonify({'ok': True})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Empty filename'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': 'File type not allowed'}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return jsonify({'filename': filename, 'url': f'/api/uploads/{filename}'})

@app.route('/api/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(os.path.abspath(UPLOAD_FOLDER), secure_filename(filename))


# ── React static file serving (production) ─────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    from flask import send_file
    if not os.path.isdir(FRONTEND_DIST):
        return jsonify({'error': 'Frontend not built. Run: cd frontend && npm run build'}), 503
    # Serve actual files (JS, CSS, images, favicon)
    if path:
        full = os.path.join(FRONTEND_DIST, path)
        if os.path.isfile(full):
            return send_from_directory(FRONTEND_DIST, path)
    # All other routes → React SPA (client-side routing)
    return send_file(os.path.join(FRONTEND_DIST, 'index.html'))


if __name__ == '__main__':
    app.run(debug=config.FLASK_DEBUG, port=config.FLASK_PORT, use_reloader=False)

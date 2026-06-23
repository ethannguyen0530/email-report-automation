import os
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from database.schema import DatabaseManager
import config

log = logging.getLogger(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist'))
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'csv', 'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder='templates')
CORS(app)
db = DatabaseManager(config.DB_PATH)


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
            return
        extraction = ExtractionService()
        emails = gmail.get_emails(query=config.GMAIL_QUERY, max_results=config.GMAIL_MAX_RESULTS)
        for email in emails:
            db.insert_email(email['id'], email['from'], email['subject'], email['body'], email['date'])
            extracted = extraction.extract_project_info(email['body'], email['subject'])
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
                )
            db.mark_email_processed(email['id'])
        log.info("Scheduled email scan complete: %d emails processed", len(emails))
    except Exception as e:
        log.error("Scheduled scan error: %s", e)


def start_scheduler():
    if config.SCAN_INTERVAL_HOURS <= 0:
        return
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_email_scan, 'interval', hours=config.SCAN_INTERVAL_HOURS,
                      id='email_scan', replace_existing=True)
    scheduler.start()
    log.info("Scheduler started: email scan every %dh", config.SCAN_INTERVAL_HOURS)


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
    from datetime import datetime
    summary = db.get_executive_summary()
    rs = ReportService()
    ss = SlackService()
    html = rs.generate_executive_report_html(summary)
    email_ok = rs.send_email_report(
        config.REPORT_RECIPIENTS,
        f"Executive Project Summary - {datetime.now().strftime('%Y-%m-%d')}",
        html,
    )
    slack_ok = ss.send_report(summary)
    return jsonify({'ok': True, 'email': email_ok, 'slack': slack_ok})

@app.route('/api/customers')
def api_customers():
    rows = db.get_all_customers()
    return jsonify([{'id': r[0], 'name': r[1]} for r in rows])

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

@app.route('/api/emails')
def api_emails():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, gmail_id, sender, subject, body, received_at, processed, created_at '
        'FROM emails ORDER BY received_at DESC LIMIT 50'
    )
    rows = cursor.fetchall()
    conn.close()
    return jsonify([
        {'id': r[0], 'gmail_id': r[1], 'sender': r[2], 'subject': r[3],
         'body': r[4], 'date': r[5], 'processed': bool(r[6]), 'processed_at': r[7]}
        for r in rows
    ])

@app.route('/api/scan-now', methods=['POST'])
def scan_now():
    """Manually trigger an email scan from the dashboard."""
    import threading
    t = threading.Thread(target=run_email_scan, daemon=True)
    t.start()
    return jsonify({'ok': True, 'message': 'Scan started in background'})

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

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from database.schema import DatabaseManager
import config

app = Flask(__name__, template_folder='templates')
CORS(app)
db = DatabaseManager(config.DB_PATH)

# Legacy HTML routes
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

# JSON API for React frontend
@app.route('/api/summary')
def api_summary():
    return jsonify(db.get_executive_summary())

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
        'id': customer[0],
        'name': customer[1],
        'projects': [
            {'id': p[0], 'name': p[1], 'status': p[2], 'progress': p[3], 'owner': p[4]}
            for p in projects
        ]
    })

@app.route('/api/projects')
def api_projects():
    rows = db.get_all_projects()
    return jsonify([
        {'id': r[0], 'name': r[1], 'customer': r[2], 'status': r[3], 'progress': r[4], 'owner': r[5]}
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
        'id': project[0],
        'name': project[1],
        'customer': project[2],
        'status': project[3],
        'progress': project[4],
        'owner': project[5],
        'updates': [
            {'id': u[0], 'date': u[1], 'summary': u[2], 'blocker': u[3], 'milestone': u[4], 'owner': u[5]}
            for u in updates
        ]
    })

if __name__ == '__main__':
    app.run(debug=config.FLASK_DEBUG, port=5000)

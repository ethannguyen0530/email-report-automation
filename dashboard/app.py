from flask import Flask, render_template, jsonify
from database.schema import DatabaseManager
import config

app = Flask(__name__, template_folder='templates')
db = DatabaseManager(config.DB_PATH)

@app.route('/')
def executive_dashboard():
    summary = db.get_executive_summary()
    return render_template('executive_dashboard.html', data=summary)

@app.route('/customer/<int:customer_id>')
def customer_view(customer_id):
    customers = db.get_all_customers()
    customer = next((c for c in customers if c[0] == customer_id), None)

    if not customer:
        return "Customer not found", 404

    projects = db.get_customer_projects(customer_id)
    return render_template('customer_view.html',
                           customer=customer,
                           projects=projects)

@app.route('/project/<int:project_id>')
def project_view(project_id):
    all_projects = db.get_all_projects()
    project = next((p for p in all_projects if p[0] == project_id), None)

    if not project:
        return "Project not found", 404

    updates = db.get_project_updates(project_id)
    return render_template('project_view.html',
                           project=project,
                           updates=updates)

@app.route('/api/summary')
def api_summary():
    return jsonify(db.get_executive_summary())

if __name__ == '__main__':
    app.run(debug=config.FLASK_DEBUG, port=5000)

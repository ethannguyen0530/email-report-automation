import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="projects.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                status TEXT DEFAULT 'In Progress',
                progress_percent INTEGER DEFAULT 0,
                owner TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                update_date TIMESTAMP,
                summary TEXT,
                blocker TEXT,
                milestone TEXT,
                owner_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gmail_id TEXT UNIQUE,
                sender TEXT,
                subject TEXT,
                body TEXT,
                received_at TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_or_create_customer(self, name):
        if not name or name == "Unknown":
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM customers WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]
        try:
            cursor.execute("INSERT INTO customers (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return cursor.execute("SELECT id FROM customers WHERE name = ?", (name,)).fetchone()[0]
        finally:
            conn.close()

    def get_or_create_project(self, customer_id, project_name, status="In Progress", progress=0, owner="Unknown"):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM projects WHERE customer_id = ? AND project_name = ?",
            (customer_id, project_name)
        )
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]
        cursor.execute(
            "INSERT INTO projects (customer_id, project_name, status, progress_percent, owner) VALUES (?, ?, ?, ?, ?)",
            (customer_id, project_name, status, progress, owner)
        )
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        return project_id

    def insert_update(self, project_id, update_date, summary, blocker=None, milestone=None, owner_name="Unknown"):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO updates
            (project_id, update_date, summary, blocker, milestone, owner_name)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, update_date, summary, blocker, milestone, owner_name)
        )
        conn.commit()
        conn.close()

    def insert_email(self, gmail_id, sender, subject, body, received_at):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO emails (gmail_id, sender, subject, body, received_at)
                VALUES (?, ?, ?, ?, ?)""",
                (gmail_id, sender, subject, body, received_at)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def mark_email_processed(self, gmail_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE emails SET processed = 1 WHERE gmail_id = ?", (gmail_id,))
        conn.commit()
        conn.close()

    def get_unprocessed_emails(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, gmail_id, sender, subject, body FROM emails WHERE processed = 0 ORDER BY id DESC")
        result = cursor.fetchall()
        conn.close()
        return result

    def get_all_projects(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.project_name, c.name, p.status, p.progress_percent, p.owner,
                   MAX(u.created_at) as last_updated
            FROM projects p
            LEFT JOIN customers c ON p.customer_id = c.id
            LEFT JOIN updates u ON u.project_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """)
        result = cursor.fetchall()
        conn.close()
        return result

    def get_all_customers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        result = cursor.fetchall()
        conn.close()
        return result

    def get_customer_projects(self, customer_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, project_name, status, progress_percent, owner
            FROM projects WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,))
        result = cursor.fetchall()
        conn.close()
        return result

    def get_project_updates(self, project_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, update_date, summary, blocker, milestone, owner_name
            FROM updates WHERE project_id = ?
            ORDER BY update_date DESC LIMIT 20
        """, (project_id,))
        result = cursor.fetchall()
        conn.close()
        return result

    def get_executive_summary(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]

        cursor.execute("SELECT status, COUNT(*) FROM projects GROUP BY status")
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT u.owner_name, u.milestone, u.update_date
            FROM updates u
            ORDER BY u.update_date DESC LIMIT 10
        """)
        accomplishments = [f"{row[0]} completed {row[1]} on {row[2][:10]}" for row in cursor.fetchall()]

        cursor.execute("SELECT blocker FROM updates WHERE blocker IS NOT NULL ORDER BY update_date DESC LIMIT 5")
        blockers = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT p.project_name, c.name, u.summary, u.update_date, u.owner_name
            FROM updates u
            JOIN projects p ON u.project_id = p.id
            LEFT JOIN customers c ON p.customer_id = c.id
            WHERE u.summary IS NOT NULL AND u.summary != ''
            ORDER BY u.update_date DESC LIMIT 20
        """)
        project_notes = [
            {'project': r[0], 'customer': r[1], 'note': r[2], 'date': r[3], 'owner': r[4]}
            for r in cursor.fetchall()
        ]

        conn.close()

        return {
            'total_projects': total_projects,
            'on_track': status_counts.get('On Track', 0),
            'at_risk': status_counts.get('At Risk', 0),
            'delayed': status_counts.get('Delayed', 0),
            'completed': status_counts.get('Completed', 0),
            'accomplishments': accomplishments,
            'blockers': blockers,
            'project_notes': project_notes,
            'projects': self.get_all_projects()
        }

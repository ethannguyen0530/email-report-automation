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
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Migrations for existing DBs
        migrations = [
            "ALTER TABLE emails ADD COLUMN processed_at TIMESTAMP",
            "ALTER TABLE emails ADD COLUMN flagged BOOLEAN DEFAULT 0",
            "ALTER TABLE emails ADD COLUMN flag_reason TEXT",
            "ALTER TABLE updates ADD COLUMN gmail_id TEXT",
            "ALTER TABLE updates ADD COLUMN confidence INTEGER",
            "ALTER TABLE recipients ADD COLUMN position TEXT",
        ]
        for sql in migrations:
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception:
                pass

        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_or_create_customer(self, name):
        if not name or name in ("Unknown", "Unknown Customer"):
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

    def get_or_create_project(self, customer_id, project_name, initial_status="In Progress", initial_progress=0, owner="Unknown", customer_name=None):
        """Return project ID, creating it if it doesn't exist.

        initial_status and initial_progress are only applied on first creation —
        subsequent calls never overwrite them, preserving user-set values.
        owner is updated on existing projects when a non-placeholder value is provided.
        customer_name can be passed by the caller to skip the extra lookup.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # If this landed under Unknown Customer, try to infer the real customer
            # by finding a known project whose name is a strict prefix of this one
            # (separated by space, dash, or colon to avoid short-name false matches).
            if customer_name is None:
                row = cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
                customer_name = row[0] if row else ''
            if customer_name in ('Unknown Customer', 'Unknown', ''):
                inferred = cursor.execute("""
                    SELECT p.customer_id FROM projects p
                    JOIN customers c ON p.customer_id = c.id
                    WHERE c.name NOT IN ('Unknown Customer', 'Unknown', '')
                    AND length(p.project_name) >= 8
                    AND (
                        ? LIKE p.project_name || ' %'
                        OR ? LIKE p.project_name || ' - %'
                        OR ? LIKE p.project_name || ': %'
                    )
                    ORDER BY length(p.project_name) DESC
                    LIMIT 1
                """, (project_name, project_name, project_name)).fetchone()
                if inferred:
                    customer_id = inferred[0]

            result = cursor.execute(
                "SELECT id FROM projects WHERE customer_id = ? AND project_name = ?",
                (customer_id, project_name)
            ).fetchone()
            if result:
                project_id = result[0]
                if owner and owner not in ('Unknown', 'TBD', ''):
                    cursor.execute("UPDATE projects SET owner = ? WHERE id = ?", (owner, project_id))
                    conn.commit()
                return project_id
            cursor.execute(
                "INSERT INTO projects (customer_id, project_name, status, progress_percent, owner) VALUES (?, ?, ?, ?, ?)",
                (customer_id, project_name, initial_status, initial_progress, owner)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_update(self, project_id, update_date, summary, blocker=None, milestone=None, owner_name="Unknown", gmail_id=None, confidence=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO updates
            (project_id, update_date, summary, blocker, milestone, owner_name, gmail_id, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, update_date, summary, blocker, milestone, owner_name, gmail_id, confidence)
        )
        conn.commit()
        conn.close()

    def mark_email_flagged(self, gmail_id, reason=None):
        conn = self.get_connection()
        conn.execute(
            "UPDATE emails SET flagged = 1, flag_reason = ? WHERE gmail_id = ?",
            (reason, gmail_id)
        )
        conn.commit()
        conn.close()

    def insert_email(self, gmail_id, sender, subject, body, received_at):
        """Returns True if newly inserted, False if already existed."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO emails (gmail_id, sender, subject, body, received_at)
                VALUES (?, ?, ?, ?, ?)""",
                (gmail_id, sender, subject, body, received_at)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def mark_email_processed(self, gmail_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE emails SET processed = 1, processed_at = CURRENT_TIMESTAMP WHERE gmail_id = ?",
            (gmail_id,)
        )
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

    def get_recipients(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, position, created_at FROM recipients ORDER BY created_at ASC")
        result = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'email': r[1], 'name': r[2], 'position': r[3], 'created_at': r[4]} for r in result]

    def add_recipient(self, email, name=None, position=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO recipients (email, name, position) VALUES (?, ?, ?)",
                           (email, name or '', position or ''))
            conn.commit()
            rid = cursor.lastrowid
            conn.close()
            return rid
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def remove_recipient(self, recipient_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM recipients WHERE id = ?", (recipient_id,))
        conn.commit()
        conn.close()

    def get_recipient_emails(self):
        """Returns flat list of email strings for report sending."""
        return [r['email'] for r in self.get_recipients()]

    def get_executive_summary(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]

        cursor.execute("SELECT status, COUNT(*) FROM projects GROUP BY status")
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT u.id, u.owner_name, u.summary, u.milestone, p.project_name, u.update_date, u.gmail_id
            FROM updates u
            JOIN projects p ON u.project_id = p.id
            WHERE u.summary IS NOT NULL AND u.summary != '' AND u.summary != 'TBD'
            ORDER BY u.update_date DESC LIMIT 10
        """)
        accomplishments = []
        accomplishments_rich = []
        seen_acc = set()
        for row in cursor.fetchall():
            update_id, owner_raw, summary, milestone_raw, project, date_raw, gmail_id = row
            owner = owner_raw if owner_raw and owner_raw not in ('Unknown', 'TBD', '') else None
            milestone = milestone_raw if milestone_raw and milestone_raw not in ('TBD', '') else None
            date = (date_raw or '')[:10]
            if owner and milestone:
                acc = f"{owner} — {milestone} on {project} ({date})"
            elif owner:
                acc = f"{owner}: {summary[:120]}"
            else:
                acc = f"{project}: {summary[:120]}"
            if acc in seen_acc:
                continue
            seen_acc.add(acc)
            accomplishments.append(acc)
            accomplishments_rich.append({
                'text': acc, 'update_id': update_id, 'gmail_id': gmail_id,
                'raw_summary': summary, 'project': project, 'date': date,
            })

        cursor.execute("""
            SELECT blocker, MAX(gmail_id) as gmail_id, MAX(id) as update_id
            FROM updates
            WHERE blocker IS NOT NULL AND blocker != '' AND blocker != 'TBD'
            GROUP BY blocker
            ORDER BY MAX(update_date) DESC LIMIT 5
        """)
        blockers = []
        blockers_rich = []
        for row in cursor.fetchall():
            blockers.append(row[0])
            blockers_rich.append({'text': row[0], 'gmail_id': row[1], 'update_id': row[2]})

        # Key project highlights: one note per project — milestone or blocker only, no filler
        cursor.execute("""
            SELECT p.project_name, c.name, p.status, u.milestone, u.blocker, u.summary, u.update_date, u.owner_name
            FROM updates u
            JOIN projects p ON u.project_id = p.id
            LEFT JOIN customers c ON p.customer_id = c.id
            WHERE (
                (u.milestone IS NOT NULL AND u.milestone != '' AND u.milestone != 'TBD')
                OR (u.blocker IS NOT NULL AND u.blocker != '' AND u.blocker != 'TBD')
                OR (u.summary IS NOT NULL AND length(u.summary) > 20
                    AND u.summary NOT LIKE 'Update from:%'
                    AND u.summary NOT LIKE 'No specific%'
                    AND u.summary NOT LIKE 'Unknown%'
                    AND u.summary != 'TBD')
            )
            ORDER BY u.update_date DESC LIMIT 50
        """)
        project_notes = []
        seen_projects = set()
        for r in cursor.fetchall():
            proj_name = r[0]
            if proj_name in seen_projects:
                continue
            status = r[2]
            milestone = r[3] if r[3] and r[3] not in ('TBD', '') else None
            blocker = r[4] if r[4] and r[4] not in ('TBD', '') else None
            summary = r[5] if r[5] and len(r[5]) > 20 and not r[5].startswith('Update from:') else None
            # Priority: blocker (most urgent) > milestone > summary
            note = blocker if blocker else (milestone if milestone else summary)
            note_type = 'blocker' if blocker else ('milestone' if milestone else 'note')
            if note:
                project_notes.append({
                    'project': proj_name, 'customer': r[1], 'status': status,
                    'note': note, 'type': note_type, 'date': r[6], 'owner': r[7]
                })
                seen_projects.add(proj_name)

        email_sources_count = conn.execute('SELECT COUNT(*) FROM emails WHERE processed=1').fetchone()[0]

        conn.close()

        return {
            'total_projects': total_projects,
            'on_track': status_counts.get('On Track', 0),
            'at_risk': status_counts.get('At Risk', 0),
            'delayed': status_counts.get('Delayed', 0),
            'completed': status_counts.get('Completed', 0),
            'accomplishments': accomplishments,
            'accomplishments_rich': accomplishments_rich,
            'blockers': blockers,
            'blockers_rich': blockers_rich,
            'project_notes': project_notes,
            'email_sources_count': email_sources_count,
            'projects': self.get_all_projects()
        }

    def get_project_health_scores(self):
        """Returns health score (0-100) for each project and a portfolio score."""
        from datetime import datetime
        conn = self.get_connection()
        rows = conn.execute("""
            SELECT p.id, p.project_name, c.name, p.status, p.progress_percent,
                   MAX(u.update_date) as last_updated,
                   MAX(CASE WHEN u.blocker IS NOT NULL AND u.blocker != '' AND u.blocker != 'TBD' THEN 1 ELSE 0 END) as has_blocker
            FROM projects p
            LEFT JOIN customers c ON c.id = p.customer_id
            LEFT JOIN updates u ON u.project_id = p.id
            GROUP BY p.id
        """).fetchall()
        conn.close()

        scores = []
        for r in rows:
            proj_id, name, customer, status, progress, last_updated, has_blocker = r
            if last_updated:
                try:
                    days_ago = (datetime.now() - datetime.fromisoformat(str(last_updated))).days
                except Exception:
                    days_ago = 99
            else:
                days_ago = 99

            score = 100
            reasons = []

            if status == 'Completed':
                reasons.append({'factor': 'Project completed', 'impact': 0, 'type': 'ok'})
            elif status == 'Delayed':
                score -= 35
                reasons.append({'factor': 'Status is Delayed', 'impact': -35, 'type': 'bad'})
            elif status == 'At Risk':
                score -= 20
                reasons.append({'factor': 'Status is At Risk', 'impact': -20, 'type': 'warn'})
            elif status in ('On Track', 'In Progress'):
                reasons.append({'factor': f'Status is {status}', 'impact': 0, 'type': 'ok'})

            if has_blocker:
                score -= 25
                reasons.append({'factor': 'Active blocker reported', 'impact': -25, 'type': 'bad'})
            else:
                reasons.append({'factor': 'No active blockers', 'impact': 0, 'type': 'ok'})

            if days_ago > 14:
                score -= 20
                reasons.append({'factor': f'Last update was {days_ago} days ago', 'impact': -20, 'type': 'bad'})
            elif days_ago > 7:
                score -= 10
                reasons.append({'factor': f'Last update was {days_ago} days ago', 'impact': -10, 'type': 'warn'})
            else:
                label = 'today' if days_ago == 0 else f'{days_ago} day{"s" if days_ago != 1 else ""} ago'
                reasons.append({'factor': f'Updated recently ({label})', 'impact': 0, 'type': 'ok'})

            prog = progress or 0
            if prog < 20 and status not in ('Completed',):
                score -= 10
                reasons.append({'factor': f'Very low progress ({prog}%)', 'impact': -10, 'type': 'warn'})
            elif prog >= 75:
                reasons.append({'factor': f'Strong progress ({prog}%)', 'impact': 0, 'type': 'ok'})

            score = max(0, min(100, score))

            scores.append({
                'id': proj_id, 'name': name, 'customer': customer,
                'score': score, 'reasons': reasons, 'progress': prog, 'status': status,
                'health': 'critical' if score < 40 else ('warning' if score < 70 else 'good'),
                'last_updated': str(last_updated) if last_updated else None,
            })

        portfolio = int(sum(s['score'] for s in scores) / len(scores)) if scores else 100
        return {'projects': scores, 'portfolio_score': portfolio}

    def get_stale_customers(self, days=7):
        """Returns customers that previously had updates but have gone silent for N days.
        Excludes customers who have never had any updates (newly added or never emailed)
        to avoid false 'No update in 7+ days' alerts for customers with no email history."""
        threshold = f'-{days} days'
        conn = self.get_connection()
        rows = conn.execute("""
            SELECT c.name, MAX(u.update_date) as last_update
            FROM customers c
            LEFT JOIN projects p ON p.customer_id = c.id
            LEFT JOIN updates u ON u.project_id = p.id
            WHERE c.name NOT IN ('Unknown', 'Unknown Customer')
            GROUP BY c.name
            HAVING last_update IS NOT NULL AND last_update < datetime('now', ?)
            ORDER BY last_update ASC
        """, (threshold,)).fetchall()
        conn.close()
        return [{'name': r[0], 'last_update': r[1]} for r in rows]

    def add_customer(self, name):
        """Manually add a customer. Returns (id, is_new)."""
        if not name or name.strip() in ('', 'Unknown', 'Unknown Customer'):
            return None, False
        name = name.strip()
        conn = self.get_connection()
        try:
            conn.execute("INSERT INTO customers (name) VALUES (?)", (name,))
            conn.commit()
            cid = conn.execute("SELECT id FROM customers WHERE name=?", (name,)).fetchone()[0]
            conn.close()
            return cid, True
        except Exception:
            row = conn.execute("SELECT id FROM customers WHERE name=?", (name,)).fetchone()
            conn.close()
            return (row[0] if row else None), False

    def delete_customer(self, customer_id):
        """Delete a customer and all their projects/updates."""
        conn = self.get_connection()
        project_ids = [r[0] for r in conn.execute("SELECT id FROM projects WHERE customer_id=?", (customer_id,)).fetchall()]
        for pid in project_ids:
            conn.execute("DELETE FROM updates WHERE project_id=?", (pid,))
        conn.execute("DELETE FROM projects WHERE customer_id=?", (customer_id,))
        conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()
        conn.close()

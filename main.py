#!/usr/bin/env python3
"""
Email-to-Report Automation System
Main entry point - processes emails and generates reports
"""

import os
import sys
from datetime import datetime
import config
from database.schema import DatabaseManager
from services.gmail_service import GmailService
from services.extraction_service import ExtractionService
from services.report_service import ReportService
from services.slack_service import SlackService
from mock_data.sample_emails import MOCK_EMAILS, MOCK_PROCESSED_DATA


def seed_database_with_mock_data():
    db = DatabaseManager(config.DB_PATH)

    print("\nSeeding database with mock data...")

    for data in MOCK_PROCESSED_DATA:
        cust_id = db.get_or_create_customer(data['customer'])
        proj_id = db.get_or_create_project(
            cust_id,
            data['project'],
            data['status'],
            data['progress'],
            data['owner']
        )
        db.insert_update(
            proj_id,
            data['update_date'],
            data.get('milestone') or data.get('project', 'Update'),
            data['blocker'],
            data['milestone'],
            data['owner']
        )

    print("Database seeded with mock data")


def process_mock_emails():
    print("\nProcessing mock emails...")

    extraction = ExtractionService()
    db = DatabaseManager(config.DB_PATH)

    for email in MOCK_EMAILS:
        print(f"\n  Processing: {email['subject']}")

        db.insert_email(email['id'], email['from'], email['subject'], email['body'], email['date'])

        extracted = extraction.extract_project_info(email['body'], email['subject'])
        print(f"    Extracted: {extracted['project']} ({extracted['customer']})")

        cust_id = db.get_or_create_customer(extracted['customer'])
        if cust_id:
            proj_id = db.get_or_create_project(
                cust_id,
                extracted['project'],
                extracted['status'],
                extracted['progress'],
                extracted['owner']
            )
            db.insert_update(
                proj_id,
                email['date'],
                extracted.get('summary') or extracted.get('milestone') or email['subject'][:120],
                extracted.get('blocker'),
                extracted.get('milestone'),
                extracted.get('owner', 'Unknown')
            )

        db.mark_email_processed(email['id'])

    print(f"Processed {len(MOCK_EMAILS)} mock emails")


def process_real_emails():
    print("\nConnecting to Gmail...")

    gmail = GmailService(config.GMAIL_CREDENTIALS_FILE)
    if not gmail.service:
        print("Gmail authentication failed. Check credentials.json.")
        return

    extraction = ExtractionService()
    db = DatabaseManager(config.DB_PATH)

    print(f"Fetching emails with query: {config.GMAIL_QUERY}")
    emails = gmail.get_emails(query=config.GMAIL_QUERY, max_results=config.GMAIL_MAX_RESULTS)

    if not emails:
        print("No emails found matching the query.")
        return

    print(f"Found {len(emails)} emails. Processing...")

    new_count = 0
    for email in emails:
        print(f"\n  Processing: {email['subject']}")

        is_new = db.insert_email(email['id'], email['from'], email['subject'], email['body'], email['date'])
        if not is_new:
            print("    Already processed — skipping")
            continue

        extracted = extraction.extract_project_info(email['body'], email['subject'])
        confidence = extracted.get('confidence', 50)
        is_project = extracted.get('is_project_related', True)
        print(f"    Extracted: {extracted['project']} ({extracted['customer']}) confidence={confidence}")

        if is_project and confidence >= 40:
            cust_id = db.get_or_create_customer(extracted['customer'])
            if cust_id:
                proj_id = db.get_or_create_project(
                    cust_id,
                    extracted['project'],
                    extracted['status'],
                    extracted['progress'],
                    extracted['owner']
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

        db.mark_email_processed(email['id'])
        new_count += 1

    print(f"\nProcessed {new_count} new emails ({len(emails)} fetched)")


def generate_and_send_reports():
    print("\nGenerating executive report...")

    db = DatabaseManager(config.DB_PATH)
    report_service = ReportService()
    slack_service = SlackService()

    summary = db.get_executive_summary()

    html_report = report_service.generate_executive_report_html(summary)
    text_report = report_service.generate_report_text(summary)

    report_service.send_email_report(
        config.REPORT_RECIPIENTS,
        f"Executive Project Summary - {datetime.now().strftime('%Y-%m-%d')}",
        html_report
    )

    slack_service.send_report(summary)

    print("Reports generated and sent")
    print("\n" + "=" * 60)
    print(text_report)
    print("=" * 60)


def show_menu():
    while True:
        mode = "REAL Gmail" if not config.USE_MOCK_DATA else "Mock Data"
        print("\n" + "=" * 60)
        print(f"EMAIL-TO-REPORT AUTOMATION SYSTEM  [{mode}]")
        print("=" * 60)
        print("1. Seed database with mock data")
        print(f"2. Fetch & process emails ({mode})")
        print("3. Generate & send executive report (email + Slack)")
        print("4. Start dashboard (http://localhost:5001)")
        print("5. Run full pipeline (all of the above)")
        print("6. Exit")
        print("=" * 60)

        choice = input("Select option (1-6): ").strip()

        if choice == '1':
            seed_database_with_mock_data()
        elif choice == '2':
            if config.USE_MOCK_DATA:
                process_mock_emails()
            else:
                process_real_emails()
        elif choice == '3':
            generate_and_send_reports()
        elif choice == '4':
            from dashboard.app import app
            print("\nStarting dashboard on http://localhost:5001")
            print("Press Ctrl+C to stop")
            try:
                app.run(debug=config.FLASK_DEBUG, port=5001, use_reloader=False)
            except KeyboardInterrupt:
                print("\nDashboard stopped")
        elif choice == '5':
            if config.USE_MOCK_DATA:
                seed_database_with_mock_data()
                process_mock_emails()
            else:
                process_real_emails()
            generate_and_send_reports()
            print("\nFull pipeline complete!")
            print("Next: Start the dashboard (option 4) to view results")
        elif choice == '6':
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option. Try again.")


def main():
    print("\nEMAIL-TO-REPORT AUTOMATION SYSTEM")
    print("=" * 60)

    if config.USE_MOCK_DATA:
        print("Mode: MOCK DATA")
    else:
        if os.path.exists(config.GMAIL_CREDENTIALS_FILE):
            print("Mode: REAL Gmail (credentials.json found)")
        else:
            print("WARNING: USE_MOCK_DATA=False but credentials.json not found!")
            print("   Download credentials.json from Google Cloud Console.")
    print("=" * 60)

    show_menu()


if __name__ == "__main__":
    main()

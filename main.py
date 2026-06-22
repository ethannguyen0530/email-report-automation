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
from dashboard.app import app


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
            "Update from email",
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
                f"Update from: {email['subject']}",
                extracted['blocker'],
                extracted['milestone'],
                extracted['owner']
            )

        db.mark_email_processed(email['id'])

    print(f"Processed {len(MOCK_EMAILS)} mock emails")


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
        print("\n" + "=" * 60)
        print("EMAIL-TO-REPORT AUTOMATION SYSTEM")
        print("=" * 60)
        print("1. Seed database with mock data")
        print("2. Process mock emails & extract data")
        print("3. Generate & send executive report (email + Slack)")
        print("4. Start dashboard (http://localhost:5000)")
        print("5. Run full pipeline (all of the above)")
        print("6. Exit")
        print("=" * 60)

        choice = input("Select option (1-6): ").strip()

        if choice == '1':
            seed_database_with_mock_data()
        elif choice == '2':
            process_mock_emails()
        elif choice == '3':
            generate_and_send_reports()
        elif choice == '4':
            print("\nStarting dashboard on http://localhost:5000")
            print("Press Ctrl+C to stop")
            try:
                app.run(debug=config.FLASK_DEBUG, port=5000, use_reloader=False)
            except KeyboardInterrupt:
                print("\nDashboard stopped")
        elif choice == '5':
            seed_database_with_mock_data()
            process_mock_emails()
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
    print("Building with mock data. Add real credentials later.")
    print("=" * 60)

    if not os.path.exists(config.GMAIL_CREDENTIALS_FILE):
        print("\nGmail credentials.json not found")
        print("   To use real Gmail API:")
        print("   1. Download from Google Cloud Console")
        print("   2. Save as: credentials.json")
        print("   3. Run again")
        print("\n   For now, using mock emails for testing.")

    show_menu()


if __name__ == "__main__":
    main()

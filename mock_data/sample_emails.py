MOCK_EMAILS = [
    {
        "id": "email_1",
        "from": "kamala@autonomize.ai",
        "subject": "Cigna Migration - Phase 1 Complete",
        "date": "2026-06-22",
        "body": """
        Hi Team,

        Great news on the Cigna Migration project. We've successfully completed Phase 1.

        Project: Cigna Migration
        Customer: Cigna
        Status: On Track
        Progress: 60%
        Milestone Completed: Phase 1 UAT approval
        Owner: Kamala

        Next Steps: Phase 2 starts June 24th
        No blockers at this time.
        """
    },
    {
        "id": "email_2",
        "from": "sergio@autonomize.ai",
        "subject": "Molina Implementation - Needs Client Review",
        "date": "2026-06-21",
        "body": """
        Team,

        Molina Implementation has hit a small snag. We're waiting on the client to review
        and approve the data model before we can proceed.

        Project: Molina Implementation
        Customer: Molina Healthcare
        Status: At Risk
        Progress: 35%
        Current Focus: Data model review with client
        Blocker: Client approval on data model - expected by June 28
        Owner: Sergio

        We'll follow up Tuesday to accelerate approval.
        """
    },
    {
        "id": "email_3",
        "from": "laksh@autonomize.ai",
        "subject": "CVS Integration - UAT Approved",
        "date": "2026-06-20",
        "body": """
        Great update on CVS Integration:

        Project: CVS Integration
        Customer: CVS Health
        Status: On Track
        Progress: 80%
        Milestone: UAT completed and approved by client
        Owner: Laksh

        We're now moving to production deployment. Target go-live: July 5th.
        No issues to report.
        """
    },
    {
        "id": "email_4",
        "from": "kamala@autonomize.ai",
        "subject": "Project Update: ACI Scan Implementation",
        "date": "2026-06-19",
        "body": """
        Quick project update:

        Project: ACI Scan Implementation
        Customer: Autonomize Internal
        Status: Delayed
        Progress: 25%
        Blocker: Resource allocation - need 1 more engineer
        Milestone: Design phase (currently in progress)
        Owner: Kamala

        Need to discuss resource planning in this week's standup.
        """
    }
]

MOCK_PROCESSED_DATA = [
    {
        "customer": "Cigna",
        "project": "Cigna Migration",
        "status": "On Track",
        "progress": 60,
        "milestone": "Phase 1 UAT approval",
        "blocker": None,
        "owner": "Kamala",
        "update_date": "2026-06-22"
    },
    {
        "customer": "Molina Healthcare",
        "project": "Molina Implementation",
        "status": "At Risk",
        "progress": 35,
        "milestone": "Data model review with client",
        "blocker": "Client approval on data model - expected by June 28",
        "owner": "Sergio",
        "update_date": "2026-06-21"
    },
    {
        "customer": "CVS Health",
        "project": "CVS Integration",
        "status": "On Track",
        "progress": 80,
        "milestone": "UAT completed and approved by client",
        "blocker": None,
        "owner": "Laksh",
        "update_date": "2026-06-20"
    },
    {
        "customer": "Autonomize Internal",
        "project": "ACI Scan Implementation",
        "status": "Delayed",
        "progress": 25,
        "milestone": "Design phase (currently in progress)",
        "blocker": "Resource allocation - need 1 more engineer",
        "owner": "Kamala",
        "update_date": "2026-06-19"
    }
]

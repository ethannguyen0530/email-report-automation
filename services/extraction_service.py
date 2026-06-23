import json
import re
from openai import OpenAI
import config

class ExtractionService:
    def __init__(self):
        if config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        else:
            self.client = None

    def extract_project_info(self, email_text, email_subject=""):
        if not self.client:
            return self.get_placeholder_extraction(email_subject)

        prompt = f"""
        Extract project information from this email. Return ONLY a JSON object (no markdown, no extra text).

        Required fields:
        - customer: Customer/client name (string)
        - project: Project name (string)
        - status: One of exactly ['On Track', 'At Risk', 'Delayed', 'Completed', 'In Progress'] (string)
        - progress: Progress percentage 0-100 (integer)
        - summary: One sentence describing the current status or key update, e.g. "UAT testing scheduled for next week" or "Integration complete, awaiting client sign-off" (string)
        - milestone: Latest completed deliverable or upcoming milestone, e.g. "Phase 1 UAT approved" or "Data migration complete" — null if none mentioned (string or null)
        - blocker: Specific blocker or dependency, e.g. "Waiting for client approval on data model" — null if none (string or null)
        - owner: Person sending or responsible for this update (string)

        Email Subject: {email_subject}

        Email Body:
        {email_text[:3000]}

        Return valid JSON only:
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()
            result_text = result_text.replace('```json', '').replace('```', '')
            extracted = json.loads(result_text)

            required = ['customer', 'project', 'status', 'progress', 'milestone', 'blocker', 'owner']
            for field in required:
                if field not in extracted:
                    extracted[field] = None

            return extracted
        except Exception as e:
            print(f"Extraction error: {e}")
            return self.get_placeholder_extraction(email_subject)

    def get_placeholder_extraction(self, subject=""):
        return {
            "customer": "Unknown Customer",
            "project": self.extract_project_name(subject),
            "status": "In Progress",
            "progress": 50,
            "summary": None,
            "milestone": None,
            "blocker": None,
            "owner": "Unknown"
        }

    def extract_project_name(self, subject):
        cleaned = re.sub(r'^(Re:|FW:|Project Update:|Status:)', '', subject, flags=re.IGNORECASE).strip()
        return cleaned[:50] if cleaned else "Unknown Project"

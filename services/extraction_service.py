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
        - customer: Customer name (string)
        - project: Project name (string)
        - status: One of ['On Track', 'At Risk', 'Delayed', 'Completed'] (string)
        - progress: Progress percentage 0-100 (integer)
        - milestone: Latest milestone or current focus (string)
        - blocker: Any blockers mentioned, or null (string or null)
        - owner: Person sending/mentioned (string)

        Email Subject: {email_subject}

        Email Body:
        {email_text[:1000]}

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
            "milestone": "TBD",
            "blocker": None,
            "owner": "Unknown"
        }

    def extract_project_name(self, subject):
        cleaned = re.sub(r'^(Re:|FW:|Project Update:|Status:)', '', subject, flags=re.IGNORECASE).strip()
        return cleaned[:50] if cleaned else "Unknown Project"

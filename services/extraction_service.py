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
            return self.get_placeholder_extraction(email_subject, reason="OpenAI key not configured")

        prompt = f"""Analyze this email and extract project/work information. Return ONLY a JSON object (no markdown, no extra text).

Required fields:
- is_project_related: true or false — is this email a project status update, delivery report, or work status update from a program manager or delivery lead? If it's a meeting invite with no status content, newsletter, HR notice, system alert, or automated notification, return false. (boolean)
- confidence: 0 to 100 — how confident are you in the extracted data? 100 = explicitly stated clear project info; 70 = project email but some fields uncertain; 40 = loosely related to a project; 0 = could not extract reliably. (integer)
- confidence_note: one-sentence explanation if confidence < 70, otherwise null (string or null)
- customer: Customer/client organization name (string, or "Unknown Customer" if not mentioned)
- project: Project or initiative name (string, or "Unknown Project" if not mentioned)
- status: One of exactly ['On Track', 'At Risk', 'Delayed', 'Completed', 'In Progress'] (string)
- progress: Estimated progress percentage 0-100 (integer)
- summary: One sentence describing the current status or key update, e.g. "UAT testing scheduled for next week" (string or null)
- milestone: Latest completed deliverable or upcoming milestone — null if none mentioned (string or null)
- blocker: Specific blocker or dependency — null if none (string or null)
- owner: Person responsible for this update (string or "Unknown")

Email Subject: {email_subject}

Email Body:
{email_text[:3000]}

Return valid JSON only:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=600
            )

            result_text = response.choices[0].message.content.strip()
            result_text = result_text.replace('```json', '').replace('```', '')
            extracted = json.loads(result_text)

            for field in ['customer', 'project', 'status', 'progress', 'milestone', 'blocker', 'owner',
                          'is_project_related', 'confidence', 'confidence_note', 'summary']:
                if field not in extracted:
                    extracted[field] = None

            # Enforce boolean type
            extracted['is_project_related'] = bool(extracted.get('is_project_related', True))
            extracted['confidence'] = int(extracted.get('confidence') or 50)

            return extracted
        except Exception as e:
            print(f"Extraction error: {e}")
            return self.get_placeholder_extraction(email_subject, reason=f"Extraction failed: {e}")

    def get_placeholder_extraction(self, subject="", reason="GPT unavailable"):
        return {
            "is_project_related": False,
            "confidence": 0,
            "confidence_note": reason,
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

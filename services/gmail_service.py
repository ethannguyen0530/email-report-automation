import os
import io
import pickle
import base64
import re
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

SUPPORTED_ATTACHMENT_EXTS = {'pdf', 'docx', 'doc', 'xlsx', 'pptx', 'csv', 'txt', 'md'}

class GmailService:
    def __init__(self, credentials_file="credentials.json"):
        self.credentials_file = credentials_file
        self.token_file = "token.pickle"
        self.service = None
        if os.path.exists(credentials_file):
            self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('gmail', 'v1', credentials=creds)

    def get_emails(self, query="", max_results=10):
        if not self.service:
            return []
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            messages = results.get('messages', [])

            email_data = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()

                headers = msg['payload']['headers']
                body = self._get_body(msg)
                attachment_text = self._get_attachments_text(msg)
                if attachment_text:
                    body = body + '\n\n--- ATTACHMENTS ---\n' + attachment_text

                email_data.append({
                    'id': msg['id'],
                    'from': self._get_header(headers, 'From', 'Unknown'),
                    'subject': self._get_header(headers, 'Subject', 'No Subject'),
                    'date': self._get_header(headers, 'Date', ''),
                    'body': body,
                })
            return email_data
        except Exception as e:
            print(f"Gmail API error: {e}")
            return []

    def _get_header(self, headers, name, default=''):
        for h in headers:
            if h['name'] == name:
                return h['value']
        return default

    def _get_body(self, message):
        try:
            return self._extract_text(message['payload']) or ''
        except Exception:
            return ''

    def _extract_text(self, payload):
        mime = payload.get('mimeType', '')

        if mime == 'text/plain':
            data = payload.get('body', {}).get('data', '')
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace') if data else ''

        parts = payload.get('parts', [])
        if parts:
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    result = self._extract_text(part)
                    if result:
                        return result
            for part in parts:
                if part.get('mimeType', '').startswith('multipart/'):
                    result = self._extract_text(part)
                    if result:
                        return result
            for part in parts:
                if part.get('mimeType') == 'text/html':
                    result = self._extract_text(part)
                    if result:
                        return result

        if mime == 'text/html':
            data = payload.get('body', {}).get('data', '')
            if data:
                raw = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                return re.sub(r'<[^>]+>', ' ', raw)

        return ''

    def _get_attachments_text(self, message):
        """Extract and return text from all supported attachments in the email."""
        results = []
        try:
            self._extract_attachment_parts(message['payload'], message['id'], results)
        except Exception as e:
            print(f"Attachment extraction error: {e}")
        return '\n\n'.join(results)

    def _extract_attachment_parts(self, payload, msg_id, results):
        filename = payload.get('filename', '')
        mime = payload.get('mimeType', '')

        if filename:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in SUPPORTED_ATTACHMENT_EXTS:
                raw_bytes = self._get_attachment_bytes(payload, msg_id)
                if raw_bytes:
                    from services.file_extractor import extract_text_from_bytes
                    text = extract_text_from_bytes(raw_bytes, ext, filename)
                    if text:
                        results.append(f"[Attachment: {filename}]\n{text}")

        for part in payload.get('parts', []):
            self._extract_attachment_parts(part, msg_id, results)

    def _get_attachment_bytes(self, payload, msg_id):
        body = payload.get('body', {})
        data = body.get('data', '')
        attachment_id = body.get('attachmentId', '')

        if attachment_id:
            try:
                att = self.service.users().messages().attachments().get(
                    userId='me', messageId=msg_id, id=attachment_id
                ).execute()
                data = att.get('data', '')
            except Exception as e:
                print(f"Could not fetch attachment {attachment_id}: {e}")
                return None

        if data:
            try:
                return base64.urlsafe_b64decode(data)
            except Exception:
                return None
        return None


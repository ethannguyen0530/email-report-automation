import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
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
                email_obj = {
                    'id': msg['id'],
                    'from': self._get_header(headers, 'From', 'Unknown'),
                    'subject': self._get_header(headers, 'Subject', 'No Subject'),
                    'date': self._get_header(headers, 'Date', ''),
                    'body': self._get_body(msg)
                }
                email_data.append(email_obj)

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
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                data = message['payload']['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        except:
            pass
        return ''

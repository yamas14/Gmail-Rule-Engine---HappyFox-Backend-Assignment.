import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE
from datetime import datetime
import base64
import email
from functools import lru_cache
from time import sleep
from threading import Lock
import re

class GmailClient:
    def __init__(self):
        self.service = self._get_gmail_service()
        self.rate_limit_lock = Lock()
        self.api_calls = 0
        self.reset_time = datetime.now()
        self.MAX_CALLS_PER_SECOND = 5
        self._compile_date_patterns()
    
    def _compile_date_patterns(self):
        self.date_patterns = [
            (re.compile(r'\([^)]+\)$'), ''),
            (re.compile(r'\s+\(UTC\)$'), '')
        ]
        
        self.date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S GMT',
            '%a, %d %b %Y %H:%M:%S UTC',
            '%a, %d %b %Y %H:%M:%S +0000'
        ]
    
    @lru_cache(maxsize=1000)
    def _parse_date(self, date_str):
        cleaned_date = date_str
        for pattern, replacement in self.date_patterns:
            cleaned_date = pattern.sub(replacement, cleaned_date)
        
        for date_format in self.date_formats:
            try:
                return datetime.strptime(cleaned_date, date_format)
            except ValueError:
                continue
        
        return datetime.utcnow()
    
    def fetch_emails(self, batch_size=50):
        self._rate_limit()
        results = self.service.users().messages().list(userId='me').execute()
        messages = results.get('messages', [])
        
        emails = []
        for i in range(0, len(messages), batch_size):
            self._rate_limit()
            batch = messages[i:i + batch_size]
            batch_request = self.service.new_batch_http_request()
            
            def callback(request_id, response, exception):
                if exception is None:
                    email_data = self._parse_email(response)
                    emails.append(email_data)
            
            for message in batch:
                batch_request.add(
                    self.service.users().messages().get(userId='me', id=message['id'], format='full'),
                    callback=callback
                )
            
            batch_request.execute()
        
        return emails
    
    def _parse_email(self, msg):
        headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
        
        email_data = {
            'message_id': msg['id'],
            'from_address': headers.get('from', 'No Sender'),
            'to_address': headers.get('to', 'No Recipient'),
            'subject': headers.get('subject', 'No Subject'),
            'received_date': self._parse_date(headers.get('date', '')),
            'labels': ','.join(msg['labelIds'])
        }
        
        if 'parts' in msg['payload']:
            data = msg['payload']['parts'][0]['body'].get('data', '')
        else:
            data = msg['payload']['body'].get('data', '')
        
        if data:
            email_data['message_body'] = base64.urlsafe_b64decode(data).decode()
        else:
            email_data['message_body'] = ''
        
        return email_data
    
    def _get_gmail_service(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('gmail', 'v1', credentials=creds)
    
    def mark_as_read(self, message_id):
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
    
    def mark_as_unread(self, message_id):
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
    
    def create_label_if_not_exists(self, label_name):
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    return label['id']
            
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            return created_label['id']
        except Exception as e:
            print(f"Error creating label: {str(e)}")
            return None
    
    def move_message(self, message_id, label_name):
        system_labels = {'INBOX', 'SPAM', 'TRASH', 'IMPORTANT', 'SENT', 'DRAFT', 'UNREAD'}
        
        if label_name.upper() in system_labels:
            label_id = label_name.upper()
        else:
            label_id = self.create_label_if_not_exists(label_name)
            if not label_id:
                print(f"Failed to create/get label: {label_name}")
                return
        
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()

    def _rate_limit(self):
        with self.rate_limit_lock:
            current_time = datetime.now()
            if (current_time - self.reset_time).total_seconds() >= 1:
                self.api_calls = 0
                self.reset_time = current_time
            
            if self.api_calls >= self.MAX_CALLS_PER_SECOND:
                sleep_time = 1 - (current_time - self.reset_time).total_seconds()
                if sleep_time > 0:
                    sleep(sleep_time)
                self.api_calls = 0
                self.reset_time = datetime.now()
            
            self.api_calls += 1

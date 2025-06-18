import pytest
from unittest.mock import patch, Mock
from main import sync_emails, process_rules
from models import Email
from datetime import datetime

@pytest.fixture
def mock_gmail_client():
    with patch('main.GmailClient') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_session(db_session):
    with patch('main.Session') as mock:
        mock.return_value = db_session
        yield db_session

def test_sync_emails(mock_gmail_client, mock_session):
    # Setup mock data
    mock_emails = [
        {
            'message_id': 'test123',
            'from_address': 'sender@test.com',
            'subject': 'Test Email',
            'received_date': datetime.now()
        }
    ]
    mock_gmail_client.fetch_emails.return_value = mock_emails
    
    # Run sync
    sync_emails()
    
    # Verify email was stored
    saved_email = mock_session.query(Email).first()
    assert saved_email.message_id == 'test123'
    assert saved_email.from_address == 'sender@test.com'

def test_process_rules(mock_gmail_client, mock_session):
    # Setup test data
    email = Email(
        message_id='test123',
        from_address='boss@company.com',
        subject='URGENT: Meeting',
        received_date=datetime.now()
    )
    mock_session.add(email)
    mock_session.commit()
    
    # Run rule processing
    with patch('main.RuleProcessor') as mock_processor:
        processor = Mock()
        mock_processor.return_value = processor
        processor.rules = [{'conditions': [], 'actions': [{'type': 'mark_as_read'}]}]
        
        process_rules()
        
        # Verify actions were taken
        mock_gmail_client.mark_as_read.assert_called_once_with('test123')
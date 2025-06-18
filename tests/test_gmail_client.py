from datetime import datetime
import pytest
from unittest.mock import Mock, patch
from gmail_client import GmailClient

@pytest.fixture
def gmail_client():
    return GmailClient()

@pytest.fixture
def mock_gmail_service():
    mock_service = Mock()
    mock_service.users().messages().list().execute.return_value = {
        'messages': [
            {'id': '123', 'threadId': 't1'},
            {'id': '456', 'threadId': 't2'}
        ]
    }
    return mock_service

    def test_rate_limiting(gmail_client):
        # Test rate limiting mechanism
        with patch('time.sleep') as mock_sleep:
            # First MAX_CALLS_PER_SECOND calls should not trigger sleep
            for _ in range(gmail_client.MAX_CALLS_PER_SECOND):
                gmail_client._rate_limit()
            
            # Reset time should still be within 1 second, so next call should trigger sleep
            current_time = gmail_client.reset_time
            with patch('gmail_client.datetime') as mock_datetime:
                mock_now = Mock()
                mock_now.return_value = current_time.replace(
                    microsecond=current_time.microsecond + 500000  # Add 0.5 seconds
                )
                mock_datetime.now = mock_now
                gmail_client._rate_limit()
                mock_sleep.assert_called_once()

def test_create_label(gmail_client, mock_gmail_service):
    with patch.object(gmail_client, 'service', mock_gmail_service):
        # Test creating new label
        mock_gmail_service.users().labels().list().execute.return_value = {'labels': []}
        mock_gmail_service.users().labels().create().execute.return_value = {'id': 'label_123'}
        
        label_id = gmail_client.create_label_if_not_exists('TestLabel')
        assert label_id == 'label_123'
        
        # Test existing label
        mock_gmail_service.users().labels().list().execute.return_value = {
            'labels': [{'id': 'existing_123', 'name': 'TestLabel'}]
        }
        label_id = gmail_client.create_label_if_not_exists('TestLabel')
        assert label_id == 'existing_123'

def test_mark_as_read(gmail_client, mock_gmail_service):
    with patch.object(gmail_client, 'service', mock_gmail_service):
        gmail_client.mark_as_read('123')
        mock_gmail_service.users().messages().modify.assert_called_once_with(
            userId='me',
            id='123',
            body={'removeLabelIds': ['UNREAD']}
        )
"""Tests for jmap_get_email.py script."""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from jmap_get_email import (
    format_size,
    display_email_detail,
    get_email_by_id,
    main,
)


class TestFormatSize:
    """Tests for format_size function."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        assert format_size(500) == '500.0 B'

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1500) == '1.5 KB'

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1500000) == '1.4 MB'

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1500000000) == '1.4 GB'

    def test_format_zero(self):
        """Test formatting zero bytes."""
        assert format_size(0) == '0.0 B'


class TestDisplayEmailDetail:
    """Tests for display_email_detail function."""

    def test_display_basic_email(self, capsys):
        """Test displaying basic email details."""
        email = {
            'id': 'email_123',
            'subject': 'Test Subject',
            'from': [{'name': 'John Doe', 'email': 'john@example.com'}],
            'to': [{'name': 'Jane Smith', 'email': 'jane@example.com'}],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {'$seen': True},
            'bodyValues': {
                'part1': {
                    'value': 'This is the email body.',
                    'isTruncated': False,
                }
            },
            'hasAttachment': False,
        }

        display_email_detail(email)

        captured = capsys.readouterr()
        assert 'EMAIL DETAILS' in captured.out
        assert 'ID: email_123' in captured.out
        assert 'Subject: Test Subject' in captured.out
        assert 'John Doe <john@example.com>' in captured.out
        assert 'Jane Smith <jane@example.com>' in captured.out
        assert 'Status: READ' in captured.out
        assert 'This is the email body.' in captured.out

    def test_display_unread_email(self, capsys):
        """Test displaying unread email."""
        email = {
            'id': 'email_unread',
            'subject': 'Unread Email',
            'from': [],
            'to': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {},  # No $seen keyword
            'bodyValues': {},
            'hasAttachment': False,
        }

        display_email_detail(email)

        captured = capsys.readouterr()
        assert 'Status: UNREAD' in captured.out

    def test_display_flagged_email(self, capsys):
        """Test displaying flagged email."""
        email = {
            'id': 'email_flagged',
            'subject': 'Flagged Email',
            'from': [],
            'to': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {'$flagged': True},
            'bodyValues': {},
            'hasAttachment': False,
        }

        display_email_detail(email)

        captured = capsys.readouterr()
        assert 'FLAGGED' in captured.out

    def test_display_email_with_attachments(self, capsys):
        """Test displaying email with attachments."""
        email = {
            'id': 'email_att',
            'subject': 'Email with Attachment',
            'from': [],
            'to': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {},
            'bodyValues': {},
            'hasAttachment': True,
            'attachments': [
                {
                    'name': 'document.pdf',
                    'type': 'application/pdf',
                    'size': 1024000,
                    'disposition': 'attachment',
                }
            ],
        }

        display_email_detail(email)

        captured = capsys.readouterr()
        assert 'ATTACHMENTS' in captured.out
        assert 'document.pdf' in captured.out
        assert 'application/pdf' in captured.out
        assert 'KB' in captured.out  # Size formatted

    def test_display_email_with_cc_bcc(self, capsys):
        """Test displaying email with CC and BCC."""
        email = {
            'id': 'email_cc',
            'subject': 'Email with CC/BCC',
            'from': [],
            'to': [],
            'cc': [{'name': 'CC Person', 'email': 'cc@example.com'}],
            'bcc': [{'name': 'BCC Person', 'email': 'bcc@example.com'}],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {},
            'bodyValues': {},
            'hasAttachment': False,
        }

        display_email_detail(email)

        captured = capsys.readouterr()
        assert 'Cc:' in captured.out
        assert 'CC Person <cc@example.com>' in captured.out
        assert 'Bcc:' in captured.out
        assert 'BCC Person <bcc@example.com>' in captured.out

    def test_display_email_with_preview(self, capsys):
        """Test displaying email with preview."""
        email = {
            'id': 'email_preview',
            'subject': 'Email with Preview',
            'from': [],
            'to': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {},
            'preview': 'This is a preview of the email content.',
            'bodyValues': {},
            'hasAttachment': False,
        }

        display_email_detail(email)

        captured = capsys.readouterr()
        assert 'PREVIEW' in captured.out
        assert 'This is a preview of the email content.' in captured.out


class TestGetEmailById:
    """Tests for get_email_by_id function."""

    def test_get_email_success(self):
        """Test successfully retrieving an email by ID."""
        from jmap_common import JMAPClient

        # Setup mock email object
        mock_email = MagicMock()
        mock_email.id = 'email_123'
        mock_email.subject = 'Test Subject'
        mock_email.blob_id = 'blob_123'
        mock_email.thread_id = 'thread_123'
        mock_email.mailbox_ids = {'mb_inbox': True}
        mock_email.keywords = {'$seen': True}
        mock_email.size = 5000
        mock_email.received_at = datetime(2025, 1, 15, 10, 30, 0)
        mock_email.sent_at = datetime(2025, 1, 15, 10, 25, 0)
        mock_email.has_attachment = False
        mock_email.preview = 'Preview text'

        # Mock from/to addresses
        mock_from = MagicMock()
        mock_from.name = 'John Doe'
        mock_from.email = 'john@example.com'
        mock_email.mail_from = [mock_from]

        mock_to = MagicMock()
        mock_to.name = 'Jane Smith'
        mock_to.email = 'jane@example.com'
        mock_email.to = [mock_to]

        # Mock body values
        mock_body = MagicMock()
        mock_body.value = 'Email body text'
        mock_body.is_encoding_problem = False
        mock_body.is_truncated = False
        mock_email.body_values = {'part1': mock_body}

        # Setup response with proper structure
        # Use spec to limit attributes (prevents hasattr check from returning True for 'response')
        mock_response = MagicMock(spec=['data'])
        mock_response.data = [mock_email]

        # Create JMAPClient with mocked client.request
        client = JMAPClient('api.example.com', 'token')
        client.client = MagicMock()
        client.client.request.return_value = mock_response

        email = get_email_by_id(client, 'email_123')

        # Verify result
        assert email is not None
        assert email['id'] == 'email_123'
        assert email['subject'] == 'Test Subject'
        assert email['from'][0]['name'] == 'John Doe'
        assert email['to'][0]['email'] == 'jane@example.com'
        assert 'part1' in email['bodyValues']

    def test_get_email_not_found(self):
        """Test retrieving non-existent email."""
        from jmap_common import JMAPClient

        # Setup empty response with spec to limit attributes
        mock_response = MagicMock(spec=['data'])
        mock_response.data = []

        # Create JMAPClient with mocked client.request
        client = JMAPClient('api.example.com', 'token')
        client.client = MagicMock()
        client.client.request.return_value = mock_response

        email = get_email_by_id(client, 'nonexistent')

        assert email is None

    def test_get_email_not_connected(self):
        """Test get_email_by_id when client is not connected."""
        from jmap_common import JMAPClient

        client = JMAPClient('api.example.com', 'token')

        with pytest.raises(ValueError, match='Client not connected'):
            get_email_by_id(client, 'email_123')


class TestMain:
    """Tests for main function."""

    @patch('jmap_get_email.load_jmap_credentials')
    @patch('jmap_get_email.JMAPClient')
    @patch('jmap_get_email.get_email_by_id')
    def test_main_default_display(self, mock_get_email, mock_jmap_client, mock_load_creds, capsys):
        """Test main function with default display."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance

        mock_email = {
            'id': 'email_123',
            'subject': 'Test Email',
            'from': [],
            'to': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {},
            'bodyValues': {},
            'hasAttachment': False,
        }
        mock_get_email.return_value = mock_email

        # Mock sys.argv
        with patch('sys.argv', ['jmap_get_email.py', 'email_123']):
            main()

        # Verify email was retrieved
        mock_get_email.assert_called_once_with(mock_client_instance, 'email_123')

        # Verify output
        captured = capsys.readouterr()
        assert 'EMAIL DETAILS' in captured.out
        assert 'Test Email' in captured.out

    @patch('jmap_get_email.load_jmap_credentials')
    @patch('jmap_get_email.JMAPClient')
    @patch('jmap_get_email.get_email_by_id')
    def test_main_json_output(self, mock_get_email, mock_jmap_client, mock_load_creds, capsys):
        """Test main function with JSON output."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance

        mock_email = {
            'id': 'email_123',
            'subject': 'Test Email',
            'from': [],
            'to': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'keywords': {},
            'bodyValues': {},
            'hasAttachment': False,
        }
        mock_get_email.return_value = mock_email

        # Mock sys.argv
        with patch('sys.argv', ['jmap_get_email.py', 'email_123', '--json']):
            main()

        # Verify JSON output
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output['id'] == 'email_123'
        assert output['subject'] == 'Test Email'

    @patch('jmap_get_email.load_jmap_credentials')
    @patch('jmap_get_email.JMAPClient')
    @patch('jmap_get_email.get_email_by_id')
    def test_main_email_not_found(self, mock_get_email, mock_jmap_client, mock_load_creds, capsys):
        """Test main function when email is not found."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance
        mock_get_email.return_value = None

        # Mock sys.argv
        with patch('sys.argv', ['jmap_get_email.py', 'nonexistent']):
            main()

        # Verify error message
        captured = capsys.readouterr()
        assert "Error: Email with ID 'nonexistent' not found" in captured.out

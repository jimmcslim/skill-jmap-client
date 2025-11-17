"""Tests for jmap_common.py module."""

import pytest
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime

from jmap_common import (
    JMAPClient,
    load_jmap_credentials,
    format_email_address,
    format_datetime,
)


class TestJMAPClient:
    """Tests for JMAPClient class."""

    def test_init(self):
        """Test JMAPClient initialization."""
        client = JMAPClient('api.example.com', 'test_token')
        assert client.host == 'api.example.com'
        assert client.api_token == 'test_token'
        assert client.client is None

    def test_connect_success(self, capsys, mock_client_create):
        """Test successful connection to JMAP server."""
        mock_create, mock_client = mock_client_create

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        # Verify Client.create_with_api_token was called correctly
        mock_create.assert_called_once_with(
            host='api.example.com',
            api_token='test_token'
        )

        # Verify client was set
        assert client.client == mock_client

        # Verify output
        captured = capsys.readouterr()
        assert 'Connecting to JMAP server at api.example.com' in captured.out
        assert '✓ Connected successfully' in captured.out

    def test_connect_failure(self, capsys):
        """Test connection failure handling."""
        with patch('jmapc.Client.create_with_api_token', side_effect=Exception('Connection failed')):
            client = JMAPClient('api.example.com', 'test_token')

            with pytest.raises(SystemExit) as exc_info:
                client.connect()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert 'Error connecting to JMAP server' in captured.out

    def test_get_mailboxes_success(self, mock_client_create, mock_mailbox_get_response, sample_mailboxes):
        """Test successful retrieval of mailboxes."""
        mock_create, mock_client = mock_client_create
        mock_client.request.return_value = mock_mailbox_get_response

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        mailboxes = client.get_mailboxes()

        # Verify we got the right number of mailboxes
        assert len(mailboxes) == len(sample_mailboxes)

        # Verify first mailbox has correct structure and data
        assert mailboxes[0]['id'] == 'mb_inbox'
        assert mailboxes[0]['name'] == 'Inbox'
        assert mailboxes[0]['role'] == 'inbox'
        assert mailboxes[0]['totalEmails'] == 42

    def test_get_mailboxes_not_connected(self):
        """Test get_mailboxes without connection."""
        client = JMAPClient('api.example.com', 'test_token')

        with pytest.raises(ValueError, match='Client not connected'):
            client.get_mailboxes()

    def test_get_mailboxes_error(self, capsys, mock_client_create):
        """Test error handling in get_mailboxes."""
        mock_create, mock_client = mock_client_create
        mock_client.request.side_effect = Exception('API error')

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        with pytest.raises(SystemExit) as exc_info:
            client.get_mailboxes()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert 'Error retrieving mailboxes' in captured.out

    def test_get_mailbox_by_name_found(self, mock_client_create, mock_mailbox_get_response):
        """Test finding a mailbox by name."""
        mock_create, mock_client = mock_client_create
        mock_client.request.return_value = mock_mailbox_get_response

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        # Test case-insensitive search
        mailbox = client.get_mailbox_by_name('inbox')
        assert mailbox is not None
        assert mailbox['name'] == 'Inbox'
        assert mailbox['id'] == 'mb_inbox'

    def test_get_mailbox_by_name_not_found(self, mock_client_create, mock_mailbox_get_response):
        """Test mailbox not found by name."""
        mock_create, mock_client = mock_client_create
        mock_client.request.return_value = mock_mailbox_get_response

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        mailbox = client.get_mailbox_by_name('nonexistent')
        assert mailbox is None

    def test_get_mailbox_by_role_found(self, mock_client_create, mock_mailbox_get_response):
        """Test finding a mailbox by role."""
        mock_create, mock_client = mock_client_create
        mock_client.request.return_value = mock_mailbox_get_response

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        mailbox = client.get_mailbox_by_role('inbox')
        assert mailbox is not None
        assert mailbox['role'] == 'inbox'
        assert mailbox['name'] == 'Inbox'

    def test_get_mailbox_by_role_not_found(self, mock_client_create, mock_mailbox_get_response):
        """Test mailbox not found by role."""
        mock_create, mock_client = mock_client_create
        mock_client.request.return_value = mock_mailbox_get_response

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        mailbox = client.get_mailbox_by_role('nonexistent')
        assert mailbox is None

    def test_get_emails_success(self, mock_client_create, mock_email_response, sample_emails):
        """Test successful retrieval of emails."""
        mock_create, mock_client = mock_client_create
        mock_client.request.return_value = mock_email_response

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        emails = client.get_emails(mailbox_id='mb_inbox', limit=10)

        # Verify we got the right number of emails
        assert len(emails) == len(sample_emails)

        # Verify first email has correct structure
        assert emails[0]['id'] == 'email_1'
        assert emails[0]['subject'] == 'Test Email 1'
        assert emails[0]['from'][0]['name'] == 'John Doe'
        assert emails[0]['hasAttachment'] is False

    def test_get_emails_not_connected(self):
        """Test get_emails without connection."""
        client = JMAPClient('api.example.com', 'test_token')

        with pytest.raises(ValueError, match='Client not connected'):
            client.get_emails()

    def test_get_emails_with_filter(self, mock_client_create, mock_email_response):
        """Test get_emails with mailbox filter."""
        mock_create, mock_client = mock_client_create
        mock_client.request.return_value = mock_email_response

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        emails = client.get_emails(mailbox_id='mb_inbox', limit=5)

        # Verify request was made
        assert mock_client.request.called
        assert len(emails) == 2

    def test_get_emails_error(self, capsys, mock_client_create):
        """Test error handling in get_emails."""
        mock_create, mock_client = mock_client_create
        mock_client.request.side_effect = Exception('API error')

        client = JMAPClient('api.example.com', 'test_token')
        client.connect()

        with pytest.raises(SystemExit) as exc_info:
            client.get_emails()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert 'Error retrieving emails' in captured.out


class TestLoadJMAPCredentials:
    """Tests for load_jmap_credentials function."""

    def test_load_credentials_success(self, mock_env_vars):
        """Test successful loading of credentials."""
        host, api_token = load_jmap_credentials()

        assert host == 'api.example.com'
        assert api_token == 'readonly_token_123'

    def test_load_credentials_strips_https(self, monkeypatch, mock_load_dotenv):
        """Test that https:// prefix is stripped from host."""
        monkeypatch.setenv('JMAP_HOST', 'https://api.example.com')
        monkeypatch.setenv('JMAP_API_TOKEN_RO', 'test_token')

        host, api_token = load_jmap_credentials()

        assert host == 'api.example.com'
        assert api_token == 'test_token'

    def test_load_credentials_strips_http(self, monkeypatch, mock_load_dotenv):
        """Test that http:// prefix is stripped from host."""
        monkeypatch.setenv('JMAP_HOST', 'http://api.example.com')
        monkeypatch.setenv('JMAP_API_TOKEN_RO', 'test_token')

        host, api_token = load_jmap_credentials()

        assert host == 'api.example.com'

    def test_load_credentials_missing_host(self, capsys, mock_load_dotenv):
        """Test error when JMAP_HOST is missing."""
        with patch('os.getenv') as mock_getenv:
            # Return None for JMAP_HOST, but test_token for JMAP_API_TOKEN_RO
            def getenv_side_effect(key, default=None):
                if key == 'JMAP_HOST':
                    return None
                elif key == 'JMAP_API_TOKEN_RO':
                    return 'test_token'
                return default

            mock_getenv.side_effect = getenv_side_effect

            with pytest.raises(SystemExit) as exc_info:
                load_jmap_credentials()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert 'Missing JMAP credentials' in captured.out

    def test_load_credentials_missing_token(self, capsys, mock_load_dotenv):
        """Test error when JMAP_API_TOKEN_RO is missing."""
        with patch('os.getenv') as mock_getenv:
            # Return api.example.com for JMAP_HOST, but None for JMAP_API_TOKEN_RO
            def getenv_side_effect(key, default=None):
                if key == 'JMAP_HOST':
                    return 'api.example.com'
                elif key == 'JMAP_API_TOKEN_RO':
                    return None
                return default

            mock_getenv.side_effect = getenv_side_effect

            with pytest.raises(SystemExit) as exc_info:
                load_jmap_credentials()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert 'Missing JMAP credentials' in captured.out


class TestFormatEmailAddress:
    """Tests for format_email_address function."""

    def test_format_with_name_and_email(self):
        """Test formatting email address with name."""
        addr = {'name': 'John Doe', 'email': 'john@example.com'}
        result = format_email_address(addr)
        assert result == 'John Doe <john@example.com>'

    def test_format_with_email_only(self):
        """Test formatting email address without name."""
        addr = {'name': '', 'email': 'john@example.com'}
        result = format_email_address(addr)
        assert result == 'john@example.com'

    def test_format_with_missing_keys(self):
        """Test formatting with missing keys."""
        addr = {'email': 'john@example.com'}
        result = format_email_address(addr)
        assert result == 'john@example.com'


class TestFormatDatetime:
    """Tests for format_datetime function."""

    def test_format_iso_datetime(self):
        """Test formatting ISO datetime string."""
        dt_str = '2025-01-15T10:30:00Z'
        result = format_datetime(dt_str)
        assert '2025-01-15' in result
        assert '10:30:00' in result

    def test_format_iso_datetime_with_offset(self):
        """Test formatting ISO datetime with timezone offset."""
        dt_str = '2025-01-15T10:30:00+00:00'
        result = format_datetime(dt_str)
        assert '2025-01-15' in result

    def test_format_invalid_datetime(self):
        """Test formatting invalid datetime returns original string."""
        dt_str = 'invalid-datetime'
        result = format_datetime(dt_str)
        assert result == 'invalid-datetime'

    def test_format_empty_string(self):
        """Test formatting empty string."""
        dt_str = ''
        result = format_datetime(dt_str)
        assert result == ''

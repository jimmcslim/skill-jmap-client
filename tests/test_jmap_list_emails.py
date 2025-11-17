"""Tests for jmap_list_emails.py script."""

import pytest
import json
from unittest.mock import patch, MagicMock

from jmap_list_emails import (
    display_emails,
    display_emails_json,
    main,
)


class TestDisplayEmails:
    """Tests for display_emails function."""

    def test_display_emails_basic(self, capsys, sample_emails):
        """Test displaying emails in basic format."""
        display_emails(sample_emails, 'Inbox', show_ids=False)

        captured = capsys.readouterr()
        assert 'Folder: Inbox' in captured.out
        assert 'Found 2 email(s)' in captured.out
        assert 'Test Email 1' in captured.out
        assert 'John Doe <john@example.com>' in captured.out

    def test_display_emails_with_ids(self, capsys, sample_emails):
        """Test displaying emails with IDs."""
        display_emails(sample_emails, 'Inbox', show_ids=True)

        captured = capsys.readouterr()
        assert 'ID: email_1' in captured.out
        assert 'ID: email_2' in captured.out

    def test_display_emails_empty_list(self, capsys):
        """Test displaying empty email list."""
        display_emails([], 'Inbox')

        captured = capsys.readouterr()
        assert 'No emails found in Inbox' in captured.out

    def test_display_emails_unread_status(self, capsys, sample_emails):
        """Test displaying unread email status."""
        display_emails(sample_emails, 'Inbox', show_ids=False)

        captured = capsys.readouterr()
        # First email is read ($seen keyword)
        assert 'Status: READ' in captured.out
        # Second email is unread (no $seen keyword) and flagged
        output_lines = captured.out.split('\n')
        # Find the line for email 2
        email_2_section = '\n'.join([
            line for i, line in enumerate(output_lines)
            if 'Test Email 2' in line or (i > 0 and 'Test Email 2' in output_lines[i-1])
        ])
        # Email 2 should show UNREAD and FLAGGED
        assert 'UNREAD' in captured.out
        assert 'FLAGGED' in captured.out

    def test_display_emails_attachment_status(self, capsys, sample_emails):
        """Test displaying attachment status."""
        display_emails(sample_emails, 'Inbox', show_ids=False)

        captured = capsys.readouterr()
        assert 'ATTACHMENT' in captured.out

    def test_display_emails_truncated_preview(self, capsys):
        """Test that long preview is truncated."""
        long_email = {
            'id': 'email_long',
            'subject': 'Long Email',
            'from': [{'name': 'Test', 'email': 'test@example.com'}],
            'receivedAt': '2025-01-15T10:30:00Z',
            'preview': 'x' * 300,  # Very long preview
            'hasAttachment': False,
            'keywords': {},
            'bodyValues': {},
        }

        display_emails([long_email], 'Inbox')

        captured = capsys.readouterr()
        assert '...' in captured.out
        # Preview should be truncated to ~200 chars
        assert captured.out.count('x') < 250


class TestDisplayEmailsJson:
    """Tests for display_emails_json function."""

    def test_display_emails_json_basic(self, capsys, sample_emails):
        """Test displaying emails in JSON format."""
        display_emails_json(sample_emails, 'Inbox', show_ids=False)

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output['folder'] == 'Inbox'
        assert output['count'] == 2
        assert len(output['emails']) == 2
        assert output['emails'][0]['subject'] == 'Test Email 1'

    def test_display_emails_json_with_ids(self, capsys, sample_emails):
        """Test displaying emails in JSON format with IDs."""
        display_emails_json(sample_emails, 'Inbox', show_ids=True)

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output['emails'][0]['id'] == 'email_1'
        assert output['emails'][1]['id'] == 'email_2'

    def test_display_emails_json_without_ids(self, capsys, sample_emails):
        """Test displaying emails in JSON format without IDs."""
        display_emails_json(sample_emails, 'Inbox', show_ids=False)

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # IDs should not be present
        assert 'id' not in output['emails'][0]
        assert 'id' not in output['emails'][1]

    def test_display_emails_json_empty(self, capsys):
        """Test displaying empty email list in JSON format."""
        display_emails_json([], 'Inbox')

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output['folder'] == 'Inbox'
        assert output['count'] == 0
        assert output['emails'] == []


class TestMain:
    """Tests for main function."""

    @patch('jmap_list_emails.load_jmap_credentials')
    @patch('jmap_list_emails.JMAPClient')
    def test_main_default_args(self, mock_jmap_client, mock_load_creds, sample_mailboxes, sample_emails, capsys):
        """Test main function with default arguments."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[0]  # Inbox
        mock_client_instance.get_emails.return_value = sample_emails
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_emails.py']):
            main()

        # Verify credentials were loaded
        mock_load_creds.assert_called_once()

        # Verify client was created and connected
        mock_jmap_client.assert_called_once_with('api.example.com', 'test_token')
        mock_client_instance.connect.assert_called_once()

        # Verify mailbox was looked up
        mock_client_instance.get_mailbox_by_name.assert_called_once_with('Inbox')

        # Verify emails were retrieved
        mock_client_instance.get_emails.assert_called_once()

        # Verify output
        captured = capsys.readouterr()
        assert 'Test Email 1' in captured.out

    @patch('jmap_list_emails.load_jmap_credentials')
    @patch('jmap_list_emails.JMAPClient')
    def test_main_with_folder_arg(self, mock_jmap_client, mock_load_creds, sample_mailboxes, sample_emails):
        """Test main function with folder argument."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[1]  # Sent Items
        mock_client_instance.get_emails.return_value = sample_emails
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_emails.py', '--folder', 'Sent Items']):
            main()

        # Verify correct folder was requested
        mock_client_instance.get_mailbox_by_name.assert_called_once_with('Sent Items')

    @patch('jmap_list_emails.load_jmap_credentials')
    @patch('jmap_list_emails.JMAPClient')
    def test_main_with_limit_arg(self, mock_jmap_client, mock_load_creds, sample_mailboxes, sample_emails):
        """Test main function with limit argument."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[0]
        mock_client_instance.get_emails.return_value = sample_emails
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_emails.py', '--limit', '20']):
            main()

        # Verify correct limit was used
        call_args = mock_client_instance.get_emails.call_args
        assert call_args[1]['limit'] == 20

    @patch('jmap_list_emails.load_jmap_credentials')
    @patch('jmap_list_emails.JMAPClient')
    def test_main_json_output(self, mock_jmap_client, mock_load_creds, sample_mailboxes, sample_emails, capsys):
        """Test main function with JSON output."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[0]
        mock_client_instance.get_emails.return_value = sample_emails
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_emails.py', '--json']):
            main()

        # Verify output is valid JSON
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output['folder'] == 'Inbox'
        assert output['count'] == 2

    @patch('jmap_list_emails.load_jmap_credentials')
    @patch('jmap_list_emails.JMAPClient')
    def test_main_show_ids(self, mock_jmap_client, mock_load_creds, sample_mailboxes, sample_emails, capsys):
        """Test main function with show-ids flag."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[0]
        mock_client_instance.get_emails.return_value = sample_emails
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_emails.py', '--show-ids']):
            main()

        # Verify IDs are shown
        captured = capsys.readouterr()
        assert 'ID: email_1' in captured.out

    @patch('jmap_list_emails.load_jmap_credentials')
    @patch('jmap_list_emails.JMAPClient')
    def test_main_folder_not_found(self, mock_jmap_client, mock_load_creds, capsys):
        """Test main function when folder is not found."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = None
        mock_client_instance.get_mailbox_by_role.return_value = None
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_emails.py', '--folder', 'NonExistent']):
            main()

        # Verify error message
        captured = capsys.readouterr()
        assert "Error: Folder 'NonExistent' not found" in captured.out

    @patch('jmap_list_emails.load_jmap_credentials')
    @patch('jmap_list_emails.JMAPClient')
    def test_main_folder_by_role(self, mock_jmap_client, mock_load_creds, sample_mailboxes, sample_emails):
        """Test main function finds folder by role when name fails."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        # First try by name fails, then succeeds by role
        mock_client_instance.get_mailbox_by_name.return_value = None
        mock_client_instance.get_mailbox_by_role.return_value = sample_mailboxes[0]
        mock_client_instance.get_emails.return_value = sample_emails
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv with a role-mappable name
        with patch('sys.argv', ['jmap_list_emails.py', '--folder', 'inbox']):
            main()

        # Verify role lookup was attempted
        mock_client_instance.get_mailbox_by_role.assert_called_once_with('inbox')

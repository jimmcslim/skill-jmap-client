"""Tests for jmap_file_email.py script."""

import pytest
from unittest.mock import patch, MagicMock

from jmap_file_email import (
    find_folder_in_para,
    get_email_info,
    file_email,
    get_mailbox_name,
    main,
)


class TestFindFolderInPara:
    """Tests for find_folder_in_para function with depth support."""

    @patch('jmap_file_email.JMAPClient')
    def test_find_folder_direct_child(self, mock_jmap_client_class, sample_mailboxes):
        """Test finding a direct child folder."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        folder = find_folder_in_para(client, '2025-Q1_website-redesign')

        assert folder is not None
        assert folder['name'] == '2025-Q1_website-redesign'
        assert folder['paraParent'] == '100_projects'

    @patch('jmap_file_email.JMAPClient')
    def test_find_folder_with_max_depth(self, mock_jmap_client_class):
        """Test finding folder respects max_depth parameter."""
        # Create nested structure
        mailboxes = [
            {'id': 'mb_100_projects', 'name': '100_projects', 'parentId': None},
            {'id': 'mb_project', 'name': 'Project', 'parentId': 'mb_100_projects'},
            {'id': 'mb_deep', 'name': 'DeepFolder', 'parentId': 'mb_project'},
        ]

        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        # Should find with max_depth=1
        folder = find_folder_in_para(client, 'Project', max_depth=1)
        assert folder is not None

        # Should NOT find deep folder with max_depth=1
        folder = find_folder_in_para(client, 'DeepFolder', max_depth=1)
        assert folder is None

        # Should find deep folder with max_depth=2
        folder = find_folder_in_para(client, 'DeepFolder', max_depth=2)
        assert folder is not None

    @patch('jmap_file_email.JMAPClient')
    def test_find_folder_unlimited_depth(self, mock_jmap_client_class):
        """Test finding folder with unlimited depth."""
        # Create deeply nested structure
        mailboxes = [
            {'id': 'mb_100_projects', 'name': '100_projects', 'parentId': None},
            {'id': 'mb_level1', 'name': 'Level1', 'parentId': 'mb_100_projects'},
            {'id': 'mb_level2', 'name': 'Level2', 'parentId': 'mb_level1'},
            {'id': 'mb_level3', 'name': 'Level3', 'parentId': 'mb_level2'},
        ]

        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        # Should find with unlimited depth (None)
        folder = find_folder_in_para(client, 'Level3', max_depth=None)
        assert folder is not None
        assert folder['name'] == 'Level3'


class TestGetEmailInfo:
    """Tests for get_email_info function."""

    @patch('jmap_file_email.JMAPClient')
    def test_get_email_info_success(self, mock_jmap_client_class):
        """Test successfully retrieving email info."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        # Setup mock email response
        mock_email = MagicMock()
        mock_email.id = 'email_123'
        mock_email.subject = 'Test Subject'
        mock_email.mailbox_ids = {'mb_inbox': True}
        mock_email.received_at = MagicMock()
        mock_email.received_at.isoformat.return_value = '2025-01-15T10:30:00Z'

        mock_from = MagicMock()
        mock_from.name = 'John Doe'
        mock_from.email = 'john@example.com'
        mock_email.mail_from = [mock_from]

        mock_response = MagicMock()
        mock_response.data = [mock_email]
        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        email_info = get_email_info(client, 'email_123')

        assert email_info is not None
        assert email_info['id'] == 'email_123'
        assert email_info['subject'] == 'Test Subject'
        assert email_info['from'][0]['name'] == 'John Doe'

    @patch('jmap_file_email.JMAPClient')
    def test_get_email_info_not_found(self, mock_jmap_client_class):
        """Test get_email_info when email doesn't exist."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = []
        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        email_info = get_email_info(client, 'nonexistent')

        assert email_info is None

    def test_get_email_info_not_connected(self):
        """Test get_email_info when client is not connected."""
        from jmap_common import JMAPClient

        client = JMAPClient('api.example.com', 'token')

        with pytest.raises(ValueError, match='Client not connected'):
            get_email_info(client, 'email_123')


class TestFileEmail:
    """Tests for file_email function."""

    @patch('jmap_file_email.JMAPClient')
    @patch('jmap_file_email.get_email_info')
    def test_file_email_move(self, mock_get_email_info, mock_jmap_client_class):
        """Test moving an email (copy=False)."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.updated = {'email_123': True}
        mock_response.not_updated = {}
        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        result = file_email(client, 'email_123', 'target_mailbox_id', copy=False)

        assert result is True
        # Should NOT have called get_email_info for move
        mock_get_email_info.assert_not_called()

    @patch('jmap_file_email.JMAPClient')
    @patch('jmap_file_email.get_email_info')
    def test_file_email_copy(self, mock_get_email_info, mock_jmap_client_class):
        """Test copying an email (copy=True)."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        # Setup email info
        mock_get_email_info.return_value = {
            'id': 'email_123',
            'mailboxIds': {'mb_inbox': True},
        }

        mock_response = MagicMock()
        mock_response.updated = {'email_123': True}
        mock_response.not_updated = {}
        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        result = file_email(client, 'email_123', 'target_mailbox_id', copy=True)

        assert result is True
        # Should have called get_email_info for copy
        mock_get_email_info.assert_called_once()

    @patch('jmap_file_email.JMAPClient')
    def test_file_email_error(self, mock_jmap_client_class):
        """Test error when filing email fails."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.not_updated = {'email_123': {'type': 'error'}}
        mock_response.updated = {}
        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        with pytest.raises(ValueError, match='Failed to file email'):
            file_email(client, 'email_123', 'target_mailbox_id', copy=False)

    def test_file_email_not_connected(self):
        """Test file_email when client is not connected."""
        from jmap_common import JMAPClient

        client = JMAPClient('api.example.com', 'token')

        with pytest.raises(ValueError, match='Client not connected'):
            file_email(client, 'email_123', 'target_mailbox_id')


class TestGetMailboxName:
    """Tests for get_mailbox_name function."""

    @patch('jmap_file_email.JMAPClient')
    def test_get_mailbox_name_found(self, mock_jmap_client_class, sample_mailboxes):
        """Test getting mailbox name by ID."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        name = get_mailbox_name(client, 'mb_inbox')

        assert name == 'Inbox'

    @patch('jmap_file_email.JMAPClient')
    def test_get_mailbox_name_not_found(self, mock_jmap_client_class, sample_mailboxes):
        """Test getting mailbox name when ID not found."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        name = get_mailbox_name(client, 'nonexistent_id')

        # Should return the ID itself
        assert name == 'nonexistent_id'


class TestMain:
    """Tests for main function."""

    @patch('jmap_file_email.load_jmap_credentials_rw')
    @patch('jmap_file_email.JMAPClient')
    @patch('jmap_file_email.get_email_info')
    @patch('jmap_file_email.find_folder_in_para')
    @patch('jmap_file_email.file_email')
    @patch('jmap_file_email.get_mailbox_name')
    @patch('builtins.input', return_value='y')
    def test_main_move_success(
        self,
        mock_input,
        mock_get_mb_name,
        mock_file_email,
        mock_find_folder,
        mock_get_email_info,
        mock_jmap_client,
        mock_load_creds,
        capsys,
    ):
        """Test main function successfully moves an email."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance

        mock_get_email_info.return_value = {
            'id': 'email_123',
            'subject': 'Test Email',
            'from': [{'name': 'John', 'email': 'john@example.com'}],
            'receivedAt': '2025-01-15T10:30:00Z',
            'mailboxIds': {'mb_inbox': True},
        }

        mock_find_folder.return_value = {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'paraParent': '100_projects',
        }

        mock_file_email.return_value = True
        mock_get_mb_name.return_value = 'Inbox'

        # Mock sys.argv
        with patch('sys.argv', ['jmap_file_email.py', 'email_123', '2025-Q1_website-redesign']):
            main()

        # Verify email info was retrieved
        mock_get_email_info.assert_called()

        # Verify folder was found
        mock_find_folder.assert_called_once()

        # Verify email was filed
        mock_file_email.assert_called_once_with(mock_client_instance, 'email_123', 'mb_project_1', copy=False)

        # Verify success message
        captured = capsys.readouterr()
        assert 'SUCCESS: Email moved' in captured.out

    @patch('jmap_file_email.load_jmap_credentials_rw')
    @patch('jmap_file_email.JMAPClient')
    @patch('jmap_file_email.get_email_info')
    @patch('jmap_file_email.find_folder_in_para')
    @patch('jmap_file_email.file_email')
    @patch('jmap_file_email.get_mailbox_name')
    @patch('builtins.input', return_value='y')
    def test_main_copy_success(
        self,
        mock_input,
        mock_get_mb_name,
        mock_file_email,
        mock_find_folder,
        mock_get_email_info,
        mock_jmap_client,
        mock_load_creds,
        capsys,
    ):
        """Test main function successfully copies an email."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance

        mock_get_email_info.return_value = {
            'id': 'email_123',
            'subject': 'Test Email',
            'from': [{'name': 'John', 'email': 'john@example.com'}],
            'receivedAt': '2025-01-15T10:30:00Z',
            'mailboxIds': {'mb_inbox': True},
        }

        mock_find_folder.return_value = {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'paraParent': '100_projects',
        }

        mock_file_email.return_value = True
        mock_get_mb_name.return_value = 'Inbox'

        # Mock sys.argv with --copy flag
        with patch('sys.argv', ['jmap_file_email.py', 'email_123', '2025-Q1_website-redesign', '--copy']):
            main()

        # Verify email was copied (not moved)
        mock_file_email.assert_called_once_with(mock_client_instance, 'email_123', 'mb_project_1', copy=True)

        # Verify success message
        captured = capsys.readouterr()
        assert 'SUCCESS: Email copied' in captured.out

    @patch('jmap_file_email.load_jmap_credentials_rw')
    @patch('jmap_file_email.JMAPClient')
    @patch('jmap_file_email.get_email_info')
    def test_main_email_not_found(self, mock_get_email_info, mock_jmap_client, mock_load_creds, capsys):
        """Test main function when email is not found."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance

        mock_get_email_info.return_value = None

        # Mock sys.argv
        with patch('sys.argv', ['jmap_file_email.py', 'nonexistent', 'SomeFolder']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert "Error: Email 'nonexistent' not found" in captured.out

    @patch('jmap_file_email.load_jmap_credentials_rw')
    @patch('jmap_file_email.JMAPClient')
    @patch('jmap_file_email.get_email_info')
    @patch('jmap_file_email.find_folder_in_para')
    @patch('jmap_file_email.get_mailbox_name')
    def test_main_folder_not_found(
        self, mock_get_mb_name, mock_find_folder, mock_get_email_info, mock_jmap_client, mock_load_creds, capsys
    ):
        """Test main function when target folder is not found."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance

        mock_get_email_info.return_value = {
            'id': 'email_123',
            'subject': 'Test Email',
            'from': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'mailboxIds': {},
        }

        mock_find_folder.return_value = None
        mock_get_mb_name.return_value = 'Inbox'

        # Mock sys.argv
        with patch('sys.argv', ['jmap_file_email.py', 'email_123', 'NonExistent']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert "Error: Folder 'NonExistent' not found" in captured.out

    @patch('jmap_file_email.load_jmap_credentials_rw')
    @patch('jmap_file_email.JMAPClient')
    @patch('jmap_file_email.get_email_info')
    @patch('jmap_file_email.find_folder_in_para')
    @patch('jmap_file_email.get_mailbox_name')
    def test_main_with_max_depth(
        self, mock_get_mb_name, mock_find_folder, mock_get_email_info, mock_jmap_client, mock_load_creds
    ):
        """Test main function with --max-depth argument."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_jmap_client.return_value = mock_client_instance

        mock_get_email_info.return_value = {
            'id': 'email_123',
            'subject': 'Test Email',
            'from': [],
            'receivedAt': '2025-01-15T10:30:00Z',
            'mailboxIds': {},
        }

        mock_find_folder.return_value = {
            'id': 'mb_project_1',
            'name': 'Project',
            'paraParent': '100_projects',
        }

        mock_get_mb_name.return_value = 'Inbox'

        with patch('jmap_file_email.file_email') as mock_file:
            mock_file.return_value = True

            # Mock sys.argv with --max-depth
            with patch('sys.argv', ['jmap_file_email.py', 'email_123', 'Project', '--max-depth', '2', '--yes']):
                main()

            # Verify find_folder_in_para was called with max_depth=2
            mock_find_folder.assert_called_once_with(mock_client_instance, 'Project', max_depth=2)

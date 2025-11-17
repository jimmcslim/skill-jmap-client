"""Tests for jmap_archive_folder.py script."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from jmap_archive_folder import (
    load_jmap_credentials_rw,
    find_folder_in_para,
    move_folder_to_archive,
    main,
)


class TestFindFolderInPara:
    """Tests for find_folder_in_para function."""

    @patch('jmap_archive_folder.JMAPClient')
    def test_find_folder_in_projects(self, mock_jmap_client_class, sample_mailboxes):
        """Test finding a folder in 100_projects."""
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
        assert folder['paraParentId'] == 'mb_100_projects'

    @patch('jmap_archive_folder.JMAPClient')
    def test_find_folder_in_areas(self, mock_jmap_client_class, sample_mailboxes):
        """Test finding a folder in 200_areas."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        folder = find_folder_in_para(client, 'Team Management')

        assert folder is not None
        assert folder['name'] == 'Team Management'
        assert folder['paraParent'] == '200_areas'

    @patch('jmap_archive_folder.JMAPClient')
    def test_find_folder_not_found(self, mock_jmap_client_class, sample_mailboxes):
        """Test when folder is not found in PARA structure."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        folder = find_folder_in_para(client, 'NonExistent')

        assert folder is None

    @patch('jmap_archive_folder.JMAPClient')
    def test_find_folder_only_one_level_deep(self, mock_jmap_client_class):
        """Test that search only goes one level deep."""
        # Create mailboxes with nested structure
        mailboxes = [
            {'id': 'mb_100_projects', 'name': '100_projects', 'parentId': None},
            {'id': 'mb_project', 'name': 'Project', 'parentId': 'mb_100_projects'},
            {'id': 'mb_deep', 'name': 'DeepFolder', 'parentId': 'mb_project'},  # Two levels deep
        ]

        # Setup mock client
        mock_client = MagicMock()
        mock_client.get_mailboxes.return_value = mailboxes
        mock_jmap_client_class.return_value = mock_client

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.get_mailboxes = mock_client.get_mailboxes

        # Should find first level
        folder = find_folder_in_para(client, 'Project')
        assert folder is not None

        # Should NOT find second level (not searched)
        folder = find_folder_in_para(client, 'DeepFolder')
        assert folder is None


class TestMoveFolderToArchive:
    """Tests for move_folder_to_archive function."""

    @patch('jmap_archive_folder.JMAPClient')
    def test_move_folder_success(self, mock_jmap_client_class):
        """Test successfully moving a folder to archive."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        # Setup mock response
        mock_response = MagicMock()
        mock_response.updated = {'folder_id': True}
        mock_response.not_updated = {}

        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        result = move_folder_to_archive(client, 'folder_id', 'archive_id')

        assert result is True
        assert mock_client.client.request.called

    @patch('jmap_archive_folder.JMAPClient')
    def test_move_folder_error(self, mock_jmap_client_class):
        """Test error when moving folder fails."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        # Setup mock error response
        mock_response = MagicMock()
        mock_response.not_updated = {'folder_id': {'type': 'error', 'description': 'Cannot move'}}
        mock_response.updated = {}

        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        with pytest.raises(ValueError, match='Failed to move folder'):
            move_folder_to_archive(client, 'folder_id', 'archive_id')

    def test_move_folder_not_connected(self):
        """Test move_folder_to_archive when client is not connected."""
        from jmap_common import JMAPClient

        client = JMAPClient('api.example.com', 'token')

        with pytest.raises(ValueError, match='Client not connected'):
            move_folder_to_archive(client, 'folder_id', 'archive_id')


class TestMain:
    """Tests for main function."""

    @patch('jmap_archive_folder.load_jmap_credentials_rw')
    @patch('jmap_archive_folder.JMAPClient')
    @patch('jmap_archive_folder.find_folder_in_para')
    @patch('jmap_archive_folder.move_folder_to_archive')
    @patch('builtins.input', return_value='y')
    def test_main_success(
        self, mock_input, mock_move, mock_find, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys
    ):
        """Test main function successfully archives a folder."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[7]  # 400_archives
        mock_jmap_client.return_value = mock_client_instance

        mock_find.return_value = {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'paraParent': '100_projects',
            'paraParentId': 'mb_100_projects',
            'totalEmails': 15,
            'unreadEmails': 2,
        }

        mock_move.return_value = True

        # Mock sys.argv
        with patch('sys.argv', ['jmap_archive_folder.py', '2025-Q1_website-redesign']):
            main()

        # Verify archive folder was looked up
        mock_client_instance.get_mailbox_by_name.assert_called_with('400_archives')

        # Verify folder was found
        mock_find.assert_called_once_with(mock_client_instance, '2025-Q1_website-redesign')

        # Verify folder was moved
        mock_move.assert_called_once_with(mock_client_instance, 'mb_project_1', 'mb_400_archives')

        # Verify success message
        captured = capsys.readouterr()
        assert 'SUCCESS: Folder archived' in captured.out

    @patch('jmap_archive_folder.load_jmap_credentials_rw')
    @patch('jmap_archive_folder.JMAPClient')
    def test_main_archive_folder_not_found(self, mock_jmap_client, mock_load_creds, capsys):
        """Test main function when archive folder doesn't exist."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = None
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_archive_folder.py', 'SomeFolder']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert "Error: Archive folder '400_archives' not found" in captured.out

    @patch('jmap_archive_folder.load_jmap_credentials_rw')
    @patch('jmap_archive_folder.JMAPClient')
    @patch('jmap_archive_folder.find_folder_in_para')
    def test_main_folder_not_found(self, mock_find, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function when folder to archive is not found."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[7]
        mock_jmap_client.return_value = mock_client_instance

        mock_find.return_value = None

        # Mock sys.argv
        with patch('sys.argv', ['jmap_archive_folder.py', 'NonExistent']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert "Error: Folder 'NonExistent' not found" in captured.out

    @patch('jmap_archive_folder.load_jmap_credentials_rw')
    @patch('jmap_archive_folder.JMAPClient')
    @patch('jmap_archive_folder.find_folder_in_para')
    @patch('builtins.input', return_value='n')
    def test_main_user_cancels(self, mock_input, mock_find, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function when user cancels the operation."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[7]
        mock_jmap_client.return_value = mock_client_instance

        mock_find.return_value = {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'paraParent': '100_projects',
            'totalEmails': 15,
            'unreadEmails': 2,
        }

        # Mock sys.argv
        with patch('sys.argv', ['jmap_archive_folder.py', '2025-Q1_website-redesign']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

        # Verify cancelled message
        captured = capsys.readouterr()
        assert 'Cancelled' in captured.out

    @patch('jmap_archive_folder.load_jmap_credentials_rw')
    @patch('jmap_archive_folder.JMAPClient')
    @patch('jmap_archive_folder.find_folder_in_para')
    def test_main_dry_run(self, mock_find, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with dry-run flag."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[7]
        mock_jmap_client.return_value = mock_client_instance

        mock_find.return_value = {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'paraParent': '100_projects',
            'totalEmails': 15,
            'unreadEmails': 2,
        }

        # Mock sys.argv
        with patch('sys.argv', ['jmap_archive_folder.py', '2025-Q1_website-redesign', '--dry-run']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

        # Verify dry-run message
        captured = capsys.readouterr()
        assert 'DRY RUN MODE' in captured.out
        assert 'No changes will be made' in captured.out

    @patch('jmap_archive_folder.load_jmap_credentials_rw')
    @patch('jmap_archive_folder.JMAPClient')
    @patch('jmap_archive_folder.find_folder_in_para')
    @patch('jmap_archive_folder.move_folder_to_archive')
    def test_main_yes_flag(self, mock_move, mock_find, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with --yes flag to skip confirmation."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[7]
        mock_jmap_client.return_value = mock_client_instance

        mock_find.return_value = {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'paraParent': '100_projects',
            'totalEmails': 15,
            'unreadEmails': 2,
        }

        mock_move.return_value = True

        # Mock sys.argv
        with patch('sys.argv', ['jmap_archive_folder.py', '2025-Q1_website-redesign', '--yes']):
            main()

        # Verify auto-confirm message
        captured = capsys.readouterr()
        assert 'Auto-confirming' in captured.out

        # Verify move was called
        mock_move.assert_called_once()

    @patch('jmap_archive_folder.load_jmap_credentials_rw')
    @patch('jmap_archive_folder.JMAPClient')
    @patch('jmap_archive_folder.find_folder_in_para')
    @patch('jmap_archive_folder.move_folder_to_archive')
    @patch('builtins.input', return_value='y')
    def test_main_move_error(
        self, mock_input, mock_move, mock_find, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys
    ):
        """Test main function when move operation fails."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[7]
        mock_jmap_client.return_value = mock_client_instance

        mock_find.return_value = {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'paraParent': '100_projects',
            'totalEmails': 15,
            'unreadEmails': 2,
        }

        mock_move.side_effect = ValueError('Move failed')

        # Mock sys.argv
        with patch('sys.argv', ['jmap_archive_folder.py', '2025-Q1_website-redesign']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert 'Error: Move failed' in captured.out

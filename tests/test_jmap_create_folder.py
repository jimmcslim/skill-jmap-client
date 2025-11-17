"""Tests for jmap_create_folder.py script."""

import pytest
from unittest.mock import patch, MagicMock

from jmap_create_folder import (
    load_jmap_credentials_rw,
    create_folder,
    main,
)


class TestLoadJMAPCredentialsRW:
    """Tests for load_jmap_credentials_rw function."""

    def test_load_credentials_success(self, mock_env_vars):
        """Test successful loading of read-write credentials."""
        host, api_token = load_jmap_credentials_rw()

        assert host == 'api.example.com'
        assert api_token == 'readwrite_token_456'

    def test_load_credentials_strips_https(self, monkeypatch, mock_load_dotenv):
        """Test that https:// prefix is stripped from host."""
        monkeypatch.setenv('JMAP_HOST', 'https://api.example.com')
        monkeypatch.setenv('JMAP_API_TOKEN_RW', 'test_token')

        host, api_token = load_jmap_credentials_rw()

        assert host == 'api.example.com'
        assert api_token == 'test_token'

    def test_load_credentials_strips_http(self, monkeypatch, mock_load_dotenv):
        """Test that http:// prefix is stripped from host."""
        monkeypatch.setenv('JMAP_HOST', 'http://api.example.com')
        monkeypatch.setenv('JMAP_API_TOKEN_RW', 'test_token')

        host, api_token = load_jmap_credentials_rw()

        assert host == 'api.example.com'

    def test_load_credentials_missing_host(self, monkeypatch, mock_load_dotenv):
        """Test error when JMAP_HOST is missing."""
        monkeypatch.delenv('JMAP_HOST', raising=False)
        monkeypatch.setenv('JMAP_API_TOKEN_RW', 'test_token')

        with pytest.raises(ValueError, match='JMAP_HOST environment variable is required'):
            load_jmap_credentials_rw()

    def test_load_credentials_missing_token(self, monkeypatch, mock_load_dotenv):
        """Test error when JMAP_API_TOKEN_RW is missing."""
        monkeypatch.setenv('JMAP_HOST', 'api.example.com')
        monkeypatch.delenv('JMAP_API_TOKEN_RW', raising=False)

        with pytest.raises(ValueError, match='JMAP_API_TOKEN_RW environment variable is required'):
            load_jmap_credentials_rw()


class TestCreateFolder:
    """Tests for create_folder function."""

    @patch('jmap_create_folder.JMAPClient')
    def test_create_folder_success(self, mock_jmap_client_class):
        """Test successfully creating a folder."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        # Setup mock response
        mock_created_mailbox = MagicMock()
        mock_created_mailbox.id = 'new_folder_id'

        mock_response = MagicMock()
        mock_response.created = {'new-folder': mock_created_mailbox}
        mock_response.not_created = {}

        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        result = create_folder(client, 'parent_id', 'Test Folder')

        # Verify result
        assert result['id'] == 'new_folder_id'
        assert result['name'] == 'Test Folder'
        assert result['parentId'] == 'parent_id'

        # Verify request was made correctly
        assert mock_client.client.request.called

    @patch('jmap_create_folder.JMAPClient')
    def test_create_folder_error(self, mock_jmap_client_class):
        """Test error when creating folder fails."""
        # Setup mock client
        mock_client = MagicMock()
        mock_jmap_client_class.return_value = mock_client

        # Setup mock error response
        mock_response = MagicMock()
        mock_response.not_created = {'new-folder': {'type': 'error', 'description': 'Folder already exists'}}
        mock_response.created = {}

        mock_client.client.request.return_value = mock_response

        # Create JMAPClient and call function
        from jmap_common import JMAPClient
        client = JMAPClient('api.example.com', 'token')
        client.client = mock_client.client

        with pytest.raises(ValueError, match='Failed to create folder'):
            create_folder(client, 'parent_id', 'Test Folder')

    def test_create_folder_not_connected(self):
        """Test create_folder when client is not connected."""
        from jmap_common import JMAPClient

        client = JMAPClient('api.example.com', 'token')

        with pytest.raises(ValueError, match='Client not connected'):
            create_folder(client, 'parent_id', 'Test Folder')


class TestMain:
    """Tests for main function."""

    @patch('jmap_create_folder.load_jmap_credentials_rw')
    @patch('jmap_create_folder.JMAPClient')
    @patch('jmap_create_folder.create_folder')
    def test_main_success(self, mock_create_folder, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function successfully creates a folder."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[2]  # 100_projects
        mock_jmap_client.return_value = mock_client_instance

        mock_create_folder.return_value = {
            'id': 'new_folder_id',
            'name': 'New Project',
            'parentId': 'mb_100_projects',
        }

        # Mock sys.argv
        with patch('sys.argv', ['jmap_create_folder.py', '--parent', '100_projects', '--name', 'New Project']):
            main()

        # Verify credentials were loaded
        mock_load_creds.assert_called_once()

        # Verify client was created and connected
        mock_jmap_client.assert_called_once_with('api.example.com', 'test_token')
        mock_client_instance.connect.assert_called_once()

        # Verify parent folder was looked up
        mock_client_instance.get_mailbox_by_name.assert_called_once_with('100_projects')

        # Verify folder was created
        mock_create_folder.assert_called_once_with(mock_client_instance, 'mb_100_projects', 'New Project')

        # Verify success message
        captured = capsys.readouterr()
        assert 'SUCCESS: Folder created' in captured.out
        assert 'Name: New Project' in captured.out

    @patch('jmap_create_folder.load_jmap_credentials_rw')
    @patch('jmap_create_folder.JMAPClient')
    def test_main_parent_not_found(self, mock_jmap_client, mock_load_creds, capsys):
        """Test main function when parent folder is not found."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = None
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_create_folder.py', '--parent', '100_projects', '--name', 'New Project']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert "Error: Parent folder '100_projects' not found" in captured.out

    @patch('jmap_create_folder.load_jmap_credentials_rw')
    @patch('jmap_create_folder.JMAPClient')
    @patch('jmap_create_folder.create_folder')
    def test_main_create_error(self, mock_create_folder, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function when folder creation fails."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[2]
        mock_jmap_client.return_value = mock_client_instance

        mock_create_folder.side_effect = ValueError('Creation failed')

        # Mock sys.argv
        with patch('sys.argv', ['jmap_create_folder.py', '--parent', '100_projects', '--name', 'New Project']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert 'Error: Creation failed' in captured.out

    @patch('jmap_create_folder.load_jmap_credentials_rw')
    def test_main_missing_credentials(self, mock_load_creds, capsys):
        """Test main function when credentials are missing."""
        mock_load_creds.side_effect = ValueError('Missing credentials')

        # Mock sys.argv
        with patch('sys.argv', ['jmap_create_folder.py', '--parent', '100_projects', '--name', 'New Project']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        # Verify error message
        captured = capsys.readouterr()
        assert 'Error: Missing credentials' in captured.out

    @patch('jmap_create_folder.load_jmap_credentials_rw')
    @patch('jmap_create_folder.JMAPClient')
    def test_main_200_areas(self, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with 200_areas parent."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[4]  # 200_areas
        mock_jmap_client.return_value = mock_client_instance

        with patch('jmap_create_folder.create_folder') as mock_create:
            mock_create.return_value = {
                'id': 'new_area_id',
                'name': 'New Area',
                'parentId': 'mb_200_areas',
            }

            # Mock sys.argv
            with patch('sys.argv', ['jmap_create_folder.py', '--parent', '200_areas', '--name', 'New Area']):
                main()

            # Verify correct parent was used
            mock_client_instance.get_mailbox_by_name.assert_called_once_with('200_areas')

    @patch('jmap_create_folder.load_jmap_credentials_rw')
    @patch('jmap_create_folder.JMAPClient')
    def test_main_300_resources(self, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with 300_resources parent."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailbox_by_name.return_value = sample_mailboxes[6]  # 300_resources
        mock_jmap_client.return_value = mock_client_instance

        with patch('jmap_create_folder.create_folder') as mock_create:
            mock_create.return_value = {
                'id': 'new_resource_id',
                'name': 'New Resource',
                'parentId': 'mb_300_resources',
            }

            # Mock sys.argv
            with patch('sys.argv', ['jmap_create_folder.py', '--parent', '300_resources', '--name', 'New Resource']):
                main()

            # Verify correct parent was used
            mock_client_instance.get_mailbox_by_name.assert_called_once_with('300_resources')

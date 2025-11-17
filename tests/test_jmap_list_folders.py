"""Tests for jmap_list_folders.py script."""

from unittest.mock import patch, MagicMock

from jmap_list_folders import (
    build_folder_tree,
    display_folder,
    display_folders,
    main,
)


class TestBuildFolderTree:
    """Tests for build_folder_tree function."""

    def test_build_tree_with_root_folders(self, sample_mailboxes):
        """Test building folder tree with root folders."""
        tree = build_folder_tree(sample_mailboxes)

        # Check root folders
        assert 'root' in tree
        root_folders = tree['root']
        root_names = [f['name'] for f in root_folders]
        assert 'Inbox' in root_names
        assert '100_projects' in root_names

    def test_build_tree_with_children(self, sample_mailboxes):
        """Test building folder tree with children."""
        tree = build_folder_tree(sample_mailboxes)

        # Check children of 100_projects
        assert 'mb_100_projects' in tree
        children = tree['mb_100_projects']
        assert len(children) == 1
        assert children[0]['name'] == '2025-Q1_website-redesign'

    def test_build_tree_empty_list(self):
        """Test building tree with empty mailbox list."""
        tree = build_folder_tree([])
        # Empty mailbox list returns empty dict (no root key created)
        assert tree == {}


class TestDisplayFolder:
    """Tests for display_folder function."""

    def test_display_folder_basic(self, capsys, sample_mailboxes):
        """Test displaying a single folder."""
        mailbox = sample_mailboxes[0]  # Inbox
        children_map = build_folder_tree(sample_mailboxes)

        display_folder(mailbox, children_map, depth=0)

        captured = capsys.readouterr()
        assert 'Inbox [inbox]' in captured.out
        assert 'ID: mb_inbox' in captured.out
        assert 'Emails: 5 unread / 42 total' in captured.out

    def test_display_folder_with_children(self, capsys, sample_mailboxes):
        """Test displaying folder with children."""
        # Find 100_projects
        mailbox = next(mb for mb in sample_mailboxes if mb['name'] == '100_projects')
        children_map = build_folder_tree(sample_mailboxes)

        display_folder(mailbox, children_map, depth=0)

        captured = capsys.readouterr()
        assert '100_projects' in captured.out
        # Child should be indented
        assert '2025-Q1_website-redesign' in captured.out

    def test_display_folder_max_depth(self, capsys, sample_mailboxes):
        """Test displaying folder respects max_depth."""
        # Create nested structure for testing
        mailbox = next(mb for mb in sample_mailboxes if mb['name'] == '100_projects')
        children_map = build_folder_tree(sample_mailboxes)

        # Display with max_depth = 2 (show folder and first level of children)
        # current_depth=0 shows the folder, current_depth=1 shows children
        display_folder(mailbox, children_map, depth=0, max_depth=2, current_depth=0)

        captured = capsys.readouterr()
        assert '100_projects' in captured.out
        # First level child should appear with max_depth=2
        assert '2025-Q1_website-redesign' in captured.out

    def test_display_folder_no_role(self, capsys, sample_mailboxes):
        """Test displaying folder without role."""
        mailbox = next(mb for mb in sample_mailboxes if mb['name'] == '100_projects')
        children_map = build_folder_tree(sample_mailboxes)

        # Don't use max_depth to ensure folder is displayed
        display_folder(mailbox, children_map, depth=0, max_depth=None)

        captured = capsys.readouterr()
        # Should show folder name
        assert '100_projects' in captured.out
        # Should not show role brackets if no role (no " [" followed by role)
        lines = captured.out.split('\n')
        folder_line = [line for line in lines if '100_projects' in line][0]
        assert '[' not in folder_line or 'ID:' in folder_line  # Either no brackets or it's the ID line


class TestDisplayFolders:
    """Tests for display_folders function."""

    def test_display_all_folders(self, capsys, sample_mailboxes):
        """Test displaying all folders."""
        display_folders(sample_mailboxes)

        captured = capsys.readouterr()
        assert 'Folder Hierarchy' in captured.out
        assert f'Found {len(sample_mailboxes)} folder(s)' in captured.out
        assert 'Inbox' in captured.out

    def test_display_empty_folder_list(self, capsys):
        """Test displaying empty folder list."""
        display_folders([])

        captured = capsys.readouterr()
        assert 'No folders found' in captured.out

    def test_display_start_folder_found(self, capsys, sample_mailboxes):
        """Test displaying folders starting from specific folder."""
        display_folders(sample_mailboxes, start_folder='100_projects')

        captured = capsys.readouterr()
        assert 'Folder Hierarchy starting from: 100_projects' in captured.out
        assert '2025-Q1_website-redesign' in captured.out

    def test_display_start_folder_not_found(self, capsys, sample_mailboxes):
        """Test error when start folder not found."""
        display_folders(sample_mailboxes, start_folder='nonexistent')

        captured = capsys.readouterr()
        assert "Error: Folder 'nonexistent' not found" in captured.out

    def test_display_with_max_depth(self, capsys, sample_mailboxes):
        """Test displaying folders with max depth."""
        display_folders(sample_mailboxes, max_depth=1)

        captured = capsys.readouterr()
        assert 'Maximum depth: 1' in captured.out

    def test_display_case_insensitive_search(self, capsys, sample_mailboxes):
        """Test case-insensitive folder name search."""
        display_folders(sample_mailboxes, start_folder='INBOX')

        captured = capsys.readouterr()
        assert 'Folder Hierarchy starting from: Inbox' in captured.out


class TestMain:
    """Tests for main function."""

    @patch('jmap_list_folders.load_jmap_credentials')
    @patch('jmap_list_folders.JMAPClient')
    def test_main_default_args(self, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with default arguments."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_folders.py']):
            main()

        # Verify credentials were loaded
        mock_load_creds.assert_called_once()

        # Verify client was created and connected
        mock_jmap_client.assert_called_once_with('api.example.com', 'test_token')
        mock_client_instance.connect.assert_called_once()

        # Verify mailboxes were retrieved
        mock_client_instance.get_mailboxes.assert_called_once()

        # Verify output
        captured = capsys.readouterr()
        assert 'Folder Hierarchy' in captured.out

    @patch('jmap_list_folders.load_jmap_credentials')
    @patch('jmap_list_folders.JMAPClient')
    def test_main_with_start_folder(self, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with start folder argument."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_folders.py', '--start', 'Inbox']):
            main()

        # Verify output
        captured = capsys.readouterr()
        assert 'Folder Hierarchy starting from: Inbox' in captured.out

    @patch('jmap_list_folders.load_jmap_credentials')
    @patch('jmap_list_folders.JMAPClient')
    def test_main_with_max_depth(self, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with max-depth argument."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_folders.py', '--max-depth', '2']):
            main()

        # Verify output
        captured = capsys.readouterr()
        assert 'Maximum depth: 2' in captured.out

    @patch('jmap_list_folders.load_jmap_credentials')
    @patch('jmap_list_folders.JMAPClient')
    def test_main_combined_args(self, mock_jmap_client, mock_load_creds, sample_mailboxes, capsys):
        """Test main function with combined arguments."""
        # Setup mocks
        mock_load_creds.return_value = ('api.example.com', 'test_token')
        mock_client_instance = MagicMock()
        mock_client_instance.get_mailboxes.return_value = sample_mailboxes
        mock_jmap_client.return_value = mock_client_instance

        # Mock sys.argv
        with patch('sys.argv', ['jmap_list_folders.py', '--start', '100_projects', '--max-depth', '1']):
            main()

        # Verify output
        captured = capsys.readouterr()
        assert 'Folder Hierarchy starting from: 100_projects' in captured.out
        assert 'Maximum depth: 1' in captured.out

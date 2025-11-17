"""Shared pytest fixtures for JMAP client tests."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for JMAP credentials."""
    monkeypatch.setenv('JMAP_HOST', 'api.example.com')
    monkeypatch.setenv('JMAP_API_TOKEN_RO', 'readonly_token_123')
    monkeypatch.setenv('JMAP_API_TOKEN_RW', 'readwrite_token_456')


@pytest.fixture
def mock_jmapc_client():
    """Mock jmapc Client instance."""
    client = MagicMock()
    client.request = MagicMock()
    return client


@pytest.fixture
def sample_mailboxes():
    """Sample mailbox data for testing."""
    return [
        {
            'id': 'mb_inbox',
            'name': 'Inbox',
            'role': 'inbox',
            'sortOrder': 10,
            'parentId': None,
            'totalEmails': 42,
            'unreadEmails': 5,
            'totalThreads': 30,
            'unreadThreads': 4,
        },
        {
            'id': 'mb_sent',
            'name': 'Sent Items',
            'role': 'sent',
            'sortOrder': 20,
            'parentId': None,
            'totalEmails': 100,
            'unreadEmails': 0,
            'totalThreads': 85,
            'unreadThreads': 0,
        },
        {
            'id': 'mb_100_projects',
            'name': '100_projects',
            'role': None,
            'sortOrder': 100,
            'parentId': None,
            'totalEmails': 0,
            'unreadEmails': 0,
            'totalThreads': 0,
            'unreadThreads': 0,
        },
        {
            'id': 'mb_project_1',
            'name': '2025-Q1_website-redesign',
            'role': None,
            'sortOrder': 10,
            'parentId': 'mb_100_projects',
            'totalEmails': 15,
            'unreadEmails': 2,
            'totalThreads': 8,
            'unreadThreads': 1,
        },
        {
            'id': 'mb_200_areas',
            'name': '200_areas',
            'role': None,
            'sortOrder': 200,
            'parentId': None,
            'totalEmails': 0,
            'unreadEmails': 0,
            'totalThreads': 0,
            'unreadThreads': 0,
        },
        {
            'id': 'mb_area_1',
            'name': 'Team Management',
            'role': None,
            'sortOrder': 10,
            'parentId': 'mb_200_areas',
            'totalEmails': 30,
            'unreadEmails': 5,
            'totalThreads': 20,
            'unreadThreads': 3,
        },
        {
            'id': 'mb_300_resources',
            'name': '300_resources',
            'role': None,
            'sortOrder': 300,
            'parentId': None,
            'totalEmails': 0,
            'unreadEmails': 0,
            'totalThreads': 0,
            'unreadThreads': 0,
        },
        {
            'id': 'mb_400_archives',
            'name': '400_archives',
            'role': None,
            'sortOrder': 400,
            'parentId': None,
            'totalEmails': 500,
            'unreadEmails': 0,
            'totalThreads': 350,
            'unreadThreads': 0,
        },
    ]


@pytest.fixture
def sample_emails():
    """Sample email data for testing."""
    return [
        {
            'id': 'email_1',
            'subject': 'Test Email 1',
            'from': [{'name': 'John Doe', 'email': 'john@example.com'}],
            'to': [{'name': 'Jane Smith', 'email': 'jane@example.com'}],
            'receivedAt': '2025-01-15T10:30:00Z',
            'preview': 'This is a preview of the first email',
            'hasAttachment': False,
            'keywords': {'$seen': True},
            'bodyValues': {
                'part1': {
                    'value': 'This is the body of the first email.',
                    'isEncodingProblem': False,
                    'isTruncated': False,
                }
            },
        },
        {
            'id': 'email_2',
            'subject': 'Test Email 2 - Unread',
            'from': [{'name': 'Alice Cooper', 'email': 'alice@example.com'}],
            'to': [{'name': 'Bob Wilson', 'email': 'bob@example.com'}],
            'receivedAt': '2025-01-16T14:22:00Z',
            'preview': 'This is a preview of the second email',
            'hasAttachment': True,
            'keywords': {'$flagged': True},
            'bodyValues': {
                'part1': {
                    'value': 'This is the body of the second email with attachment.',
                    'isEncodingProblem': False,
                    'isTruncated': False,
                }
            },
        },
    ]


@pytest.fixture
def mock_mailbox_get_response(sample_mailboxes):
    """Mock MailboxGetResponse from jmapc."""
    from jmapc.methods import MailboxGetResponse

    response = MagicMock(spec=MailboxGetResponse)

    # Create mock Mailbox objects
    mock_mailboxes = []
    for mb_data in sample_mailboxes:
        mock_mb = MagicMock()
        mock_mb.id = mb_data['id']
        mock_mb.name = mb_data['name']
        mock_mb.role = mb_data['role']
        mock_mb.sort_order = mb_data['sortOrder']
        mock_mb.parent_id = mb_data['parentId']
        mock_mb.total_emails = mb_data['totalEmails']
        mock_mb.unread_emails = mb_data['unreadEmails']
        mock_mb.total_threads = mb_data['totalThreads']
        mock_mb.unread_threads = mb_data['unreadThreads']
        mock_mailboxes.append(mock_mb)

    response.data = mock_mailboxes
    return response


@pytest.fixture
def mock_email_response(sample_emails):
    """Mock EmailGet response from jmapc."""
    # Create the query response (first response)
    query_response = MagicMock()
    query_response.ids = ['email_1', 'email_2']

    # Create the get response (second response)
    get_response = MagicMock()

    # Create mock Email objects
    mock_emails = []
    for email_data in sample_emails:
        mock_email = MagicMock()
        mock_email.id = email_data['id']
        mock_email.subject = email_data['subject']

        # Mock from addresses
        from_addrs = []
        for addr in email_data['from']:
            mock_addr = MagicMock()
            mock_addr.name = addr['name']
            mock_addr.email = addr['email']
            from_addrs.append(mock_addr)
        mock_email.mail_from = from_addrs

        # Mock to addresses
        to_addrs = []
        for addr in email_data['to']:
            mock_addr = MagicMock()
            mock_addr.name = addr['name']
            mock_addr.email = addr['email']
            to_addrs.append(mock_addr)
        mock_email.to = to_addrs

        # Mock datetime
        mock_email.received_at = datetime.fromisoformat(email_data['receivedAt'].replace('Z', '+00:00'))
        mock_email.preview = email_data['preview']
        mock_email.has_attachment = email_data['hasAttachment']
        mock_email.keywords = email_data['keywords']

        # Mock body values
        body_values = {}
        for part_id, part_data in email_data['bodyValues'].items():
            mock_body = MagicMock()
            mock_body.value = part_data['value']
            mock_body.is_encoding_problem = part_data['isEncodingProblem']
            mock_body.is_truncated = part_data['isTruncated']
            body_values[part_id] = mock_body
        mock_email.body_values = body_values

        mock_emails.append(mock_email)

    get_response.data = mock_emails

    # Create invocation response wrapper
    invocation_response = MagicMock()
    invocation_response.response = get_response

    return [query_response, invocation_response]


@pytest.fixture
def mock_client_create():
    """Mock jmapc Client.create_with_api_token."""
    with patch('jmapc.Client.create_with_api_token') as mock:
        client = MagicMock()
        mock.return_value = client
        yield mock, client


@pytest.fixture
def mock_load_dotenv():
    """Mock load_dotenv function."""
    with patch('dotenv.load_dotenv') as mock:
        yield mock

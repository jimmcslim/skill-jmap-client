"""
JMAP Common Module

Shared code for JMAP email scripts including client setup,
formatting utilities, and configuration loading using jmapc library.
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from jmapc import Client
from jmapc.methods import MailboxGet, MailboxGetResponse, EmailQuery, EmailGet
from dotenv import load_dotenv


class JMAPClient:
    """JMAP client wrapper using jmapc library."""

    def __init__(self, host: str, api_token: str):
        self.host = host
        self.api_token = api_token
        self.client: Optional[Client] = None

    def connect(self) -> None:
        """Connect to JMAP server and initialize client."""
        print(f"Connecting to JMAP server at {self.host}...")

        try:
            self.client = Client.create_with_api_token(
                host=self.host,
                api_token=self.api_token
            )

            print(f"✓ Connected successfully")
            print(f"  API URL: https://{self.host}\n")

        except Exception as e:
            print(f"✗ Error connecting to JMAP server: {e}")
            sys.exit(1)

    def get_mailboxes(self) -> List[Dict[str, Any]]:
        """Retrieve all mailboxes."""
        if not self.client:
            raise ValueError("Client not connected. Call connect() first.")

        try:
            result = self.client.request(MailboxGet(ids=None))

            if isinstance(result, MailboxGetResponse):
                # Convert jmapc Mailbox objects to dicts for compatibility
                return [
                    {
                        'id': mb.id,
                        'name': mb.name,
                        'role': mb.role,
                        'sortOrder': mb.sort_order,
                        'parentId': mb.parent_id,
                        'totalEmails': mb.total_emails,
                        'unreadEmails': mb.unread_emails,
                        'totalThreads': mb.total_threads,
                        'unreadThreads': mb.unread_threads,
                    }
                    for mb in result.data
                ]
            return []

        except Exception as e:
            print(f"Error retrieving mailboxes: {e}")
            sys.exit(1)

    def get_mailbox_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a mailbox by name (case-insensitive)."""
        mailboxes = self.get_mailboxes()
        name_lower = name.lower()

        for mailbox in mailboxes:
            if mailbox.get('name', '').lower() == name_lower:
                return mailbox

        return None

    def get_mailbox_by_role(self, role: str) -> Optional[Dict[str, Any]]:
        """Find a mailbox by role (e.g., 'inbox', 'sent', 'trash')."""
        mailboxes = self.get_mailboxes()

        for mailbox in mailboxes:
            if mailbox.get('role') == role:
                return mailbox

        return None

    def get_emails(self, mailbox_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve emails, optionally filtered by mailbox."""
        if not self.client:
            raise ValueError("Client not connected. Call connect() first.")

        try:
            from jmapc import Comparator, EmailQueryFilterCondition, Ref

            # Build the filter
            email_filter = None
            if mailbox_id:
                email_filter = EmailQueryFilterCondition(in_mailbox=mailbox_id)

            # Create the query
            query_params = {
                'sort': [Comparator(property='receivedAt', is_ascending=False)],
                'limit': limit,
            }
            if email_filter:
                query_params['filter'] = email_filter

            # Request emails with query and get
            results = self.client.request([
                EmailQuery(**query_params),
                EmailGet(
                    ids=Ref('/ids'),
                    properties=[
                        'id',
                        'subject',
                        'from',
                        'to',
                        'receivedAt',
                        'preview',
                        'bodyValues',
                        'hasAttachment',
                        'keywords',
                    ],
                    fetch_text_body_values=True,
                    fetch_html_body_values=False,
                    max_body_value_bytes=5000,
                )
            ])

            # Extract email data from the second response (EmailGet)
            if len(results) >= 2:
                email_get_invocation = results[1]

                # Access the actual response from InvocationResponseOrError
                if hasattr(email_get_invocation, 'response'):
                    email_get_response = email_get_invocation.response
                else:
                    email_get_response = email_get_invocation

                # Convert jmapc Email objects to dicts for compatibility
                emails = []
                email_list = email_get_response.data if hasattr(email_get_response, 'data') else email_get_response.list

                for email in email_list:
                    # Handle from addresses
                    from_addrs = []
                    if hasattr(email, 'mail_from') and email.mail_from:
                        from_addrs = [{'name': addr.name or '', 'email': addr.email or ''} for addr in email.mail_from]

                    # Handle to addresses
                    to_addrs = []
                    if hasattr(email, 'to') and email.to:
                        to_addrs = [{'name': addr.name or '', 'email': addr.email or ''} for addr in email.to]

                    # Handle body values
                    body_values_dict = {}
                    if hasattr(email, 'body_values') and email.body_values:
                        for part_id, body_value in email.body_values.items():
                            if hasattr(body_value, 'value'):
                                body_values_dict[part_id] = {
                                    'value': body_value.value,
                                    'isEncodingProblem': getattr(body_value, 'is_encoding_problem', False),
                                    'isTruncated': getattr(body_value, 'is_truncated', False),
                                }
                            else:
                                body_values_dict[part_id] = {'value': str(body_value)}

                    email_dict = {
                        'id': email.id,
                        'subject': email.subject or '',
                        'from': from_addrs,
                        'to': to_addrs,
                        'receivedAt': email.received_at.isoformat() if hasattr(email, 'received_at') and email.received_at else None,
                        'preview': email.preview or '',
                        'hasAttachment': email.has_attachment if hasattr(email, 'has_attachment') else False,
                        'keywords': email.keywords if hasattr(email, 'keywords') and email.keywords else {},
                        'bodyValues': body_values_dict,
                    }
                    emails.append(email_dict)
                return emails

            return []

        except Exception as e:
            print(f"Error retrieving emails: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def load_jmap_credentials() -> tuple[str, str]:
    """Load JMAP credentials from environment variables."""
    load_dotenv()

    host = os.getenv('JMAP_HOST')
    api_token = os.getenv('JMAP_API_TOKEN')

    if not all([host, api_token]):
        print("Error: Missing JMAP credentials in .env file")
        print("\nRequired environment variables:")
        print("  JMAP_HOST         - JMAP server hostname (e.g., api.fastmail.com)")
        print("  JMAP_API_TOKEN    - API token or password")
        print("\nCreate a .env file with these variables.")
        sys.exit(1)

    # Remove protocol from host if present (jmapc expects just hostname)
    host = host.replace('https://', '').replace('http://', '')

    return host, api_token


def format_email_address(addr: Dict[str, str]) -> str:
    """Format an email address object."""
    name = addr.get('name', '')
    email = addr.get('email', '')
    if name:
        return f"{name} <{email}>"
    return email


def format_datetime(dt_str: str) -> str:
    """Format ISO datetime string to readable format."""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    except:
        return dt_str

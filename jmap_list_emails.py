#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jmapc>=0.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
JMAP Email Listing Script

Lists emails from a specific mailbox/folder.
Defaults to Inbox if no folder is specified.
"""

import argparse
from typing import List, Dict, Any
from jmap_common import (
    JMAPClient,
    load_jmap_credentials,
    format_email_address,
    format_datetime
)


def display_emails(emails: List[Dict[str, Any]], folder_name: str, show_ids: bool = False) -> None:
    """Display emails in a readable format."""
    if not emails:
        print(f"No emails found in {folder_name}.")
        return

    print(f"{'='*80}")
    print(f"Folder: {folder_name}")
    print(f"Found {len(emails)} email(s)")
    print(f"{'='*80}\n")

    for idx, email in enumerate(emails, 1):
        subject = email.get('subject', '(No subject)')
        from_addrs = email.get('from', [])
        from_str = ', '.join(format_email_address(addr) for addr in from_addrs)
        received_at = format_datetime(email.get('receivedAt', ''))
        preview = email.get('preview', '')
        has_attachment = email.get('hasAttachment', False)
        keywords = email.get('keywords', {})
        is_seen = '$seen' in keywords
        is_flagged = '$flagged' in keywords

        # Status indicators
        status = []
        if not is_seen:
            status.append('UNREAD')
        if is_flagged:
            status.append('FLAGGED')
        if has_attachment:
            status.append('ATTACHMENT')

        status_str = ' | '.join(status) if status else 'READ'

        print(f"[{idx}] {subject}")
        if show_ids:
            email_id = email.get('id', 'N/A')
            print(f"    ID: {email_id}")
        print(f"    From: {from_str}")
        print(f"    Date: {received_at}")
        print(f"    Status: {status_str}")
        if preview:
            # Truncate preview if too long
            preview_text = preview[:200] + '...' if len(preview) > 200 else preview
            print(f"    Preview: {preview_text}")

        # Try to get text body
        body_values = email.get('bodyValues', {})
        if body_values:
            # Get the first text body
            first_body = next(iter(body_values.values()), {})
            body_text = first_body.get('value', '')
            if body_text:
                # Show first 300 chars of body
                body_preview = body_text[:300].strip()
                if len(body_text) > 300:
                    body_preview += '...'
                print(f"    Body: {body_preview}")

        print(f"{'-'*80}\n")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='List emails from a JMAP mailbox/folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # List emails from Inbox
  %(prog)s --folder "Sent Items"    # List emails from Sent Items
  %(prog)s --folder Inbox --limit 20  # List 20 emails from Inbox
        """
    )
    parser.add_argument(
        '--folder',
        type=str,
        default='Inbox',
        help='Folder/mailbox name to list emails from (default: Inbox)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of emails to retrieve (default: 10)'
    )
    parser.add_argument(
        '--show-ids',
        action='store_true',
        help='Show email IDs in the output'
    )
    args = parser.parse_args()

    # Load credentials
    host, api_token = load_jmap_credentials()

    # Create client and connect
    client = JMAPClient(host, api_token)
    client.connect()

    # Find the mailbox
    mailbox = client.get_mailbox_by_name(args.folder)

    if not mailbox:
        # Try by role if it's a special folder
        role_map = {
            'inbox': 'inbox',
            'sent': 'sent',
            'sent items': 'sent',
            'trash': 'trash',
            'junk': 'junk',
            'junk mail': 'junk',
            'drafts': 'drafts',
            'archive': 'archive'
        }
        role = role_map.get(args.folder.lower())
        if role:
            mailbox = client.get_mailbox_by_role(role)

    if not mailbox:
        print(f"Error: Folder '{args.folder}' not found")
        print("\nUse jmap_list_folders.py to see available folders")
        return

    mailbox_name = mailbox.get('name', args.folder)
    mailbox_id = mailbox.get('id')

    print(f"Fetching {args.limit} most recent emails from '{mailbox_name}'...\n")

    # Get and display emails
    emails = client.get_emails(mailbox_id=mailbox_id, limit=args.limit)
    display_emails(emails, mailbox_name, show_ids=args.show_ids)


if __name__ == "__main__":
    main()

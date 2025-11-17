#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jmapc>=0.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
JMAP Email Filing Script

Files (moves) an email to a subfolder in the PARA structure:
- 100_projects subfolders
- 200_areas subfolders
- 300_resources subfolders

The email is moved from its current location(s) to the target folder.
Use --copy flag to copy instead of move (keeps email in original location).

Uses a read-write API token for modification operations.
"""

import argparse
import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from jmap_common import JMAPClient
from jmapc.methods import EmailSet, EmailGet


def load_jmap_credentials_rw() -> tuple[str, str]:
    """Load JMAP credentials with read-write access from environment variables."""
    load_dotenv()

    host = os.getenv('JMAP_HOST')
    api_token = os.getenv('JMAP_API_TOKEN_RW')

    if not host:
        raise ValueError("JMAP_HOST environment variable is required")
    if not api_token:
        raise ValueError("JMAP_API_TOKEN_RW environment variable is required")

    # Remove any https:// prefix if present
    if host.startswith('https://'):
        host = host.replace('https://', '')
    if host.startswith('http://'):
        host = host.replace('http://', '')

    return host, api_token


def find_folder_in_para(client: JMAPClient, folder_name: str, max_depth: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Search for a folder by name in the PARA structure.
    Searches in 100_projects, 200_areas, and 300_resources up to max_depth levels.

    Args:
        client: JMAPClient instance
        folder_name: Name of the folder to search for
        max_depth: Maximum depth to search (None = unlimited, 1 = direct children only)

    Returns the folder if found, None otherwise.
    """
    # Get all mailboxes
    all_mailboxes = client.get_mailboxes()

    # Find PARA parent folders
    para_parents = {
        '100_projects': None,
        '200_areas': None,
        '300_resources': None,
    }

    for mb in all_mailboxes:
        if mb['name'] in para_parents:
            para_parents[mb['name']] = mb['id']

    # Helper function to recursively search descendants
    def search_descendants(parent_id: str, current_depth: int, para_name: str) -> Optional[Dict[str, Any]]:
        """Recursively search descendants of a given parent."""
        # Check depth limit
        if max_depth is not None and current_depth > max_depth:
            return None

        # Find all children of this parent
        for mb in all_mailboxes:
            parent_id_mb = mb.get('parentId')
            if parent_id_mb == parent_id:
                # Check if this is the folder we're looking for
                if mb['name'] == folder_name:
                    mb['paraParent'] = para_name
                    mb['paraParentId'] = para_parents[para_name]
                    return mb

                # Recursively search this child's descendants
                result = search_descendants(mb['id'], current_depth + 1, para_name)
                if result:
                    return result

        return None

    # Search for the folder name in each PARA parent's descendants
    for para_name, para_id in para_parents.items():
        if para_id is None:
            continue

        # Search descendants starting at depth 1
        result = search_descendants(para_id, 1, para_name)
        if result:
            return result

    return None


def get_email_info(client: JMAPClient, email_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve basic information about an email by ID.

    Returns email info if found, None otherwise.
    """
    if not client.client:
        raise ValueError("Client not connected. Call connect() first.")

    try:
        result = client.client.request(
            EmailGet(
                ids=[email_id],
                properties=['id', 'subject', 'from', 'mailboxIds', 'receivedAt']
            )
        )

        if hasattr(result, 'data') and result.data:
            email = result.data[0]

            # Handle from addresses
            from_addrs = []
            if hasattr(email, 'mail_from') and email.mail_from:
                from_addrs = [
                    {'name': addr.name or '', 'email': addr.email or ''}
                    for addr in email.mail_from
                ]

            return {
                'id': email.id,
                'subject': email.subject or '(No subject)',
                'from': from_addrs,
                'mailboxIds': email.mailbox_ids if hasattr(email, 'mailbox_ids') else {},
                'receivedAt': email.received_at.isoformat() if hasattr(email, 'received_at') and email.received_at else None,
            }

        return None

    except Exception as e:
        raise ValueError(f"Error retrieving email: {e}")


def file_email(client: JMAPClient, email_id: str, target_mailbox_id: str, copy: bool = False) -> bool:
    """
    File (move or copy) an email to a target mailbox.

    If copy=False (default), the email is moved (removed from all other mailboxes).
    If copy=True, the email is copied (added to target while keeping in current mailboxes).

    Returns True if successful, False otherwise.
    """
    if not client.client:
        raise ValueError("Client not connected. Call connect() first.")

    try:
        # Prepare the mailboxIds update
        if copy:
            # For copy: get current mailboxIds and add the target
            email_info = get_email_info(client, email_id)
            if not email_info:
                raise ValueError("Email not found")

            new_mailbox_ids = email_info['mailboxIds'].copy()
            new_mailbox_ids[target_mailbox_id] = True
        else:
            # For move: replace all mailboxIds with just the target
            new_mailbox_ids = {target_mailbox_id: True}

        # Use EmailSet to update the email's mailboxIds
        result = client.client.request(
            EmailSet(
                update={
                    email_id: {
                        'mailboxIds': new_mailbox_ids
                    }
                }
            )
        )

        # Check for errors
        if hasattr(result, 'not_updated') and result.not_updated:
            error_info = result.not_updated.get(email_id, {})
            raise ValueError(f"Failed to file email: {error_info}")

        # Check if update was successful
        if hasattr(result, 'updated') and result.updated:
            if email_id in result.updated:
                return True

        raise ValueError("Email filing response did not contain expected data")

    except Exception as e:
        raise ValueError(f"Error filing email: {e}")


def get_mailbox_name(client: JMAPClient, mailbox_id: str) -> str:
    """Get the name of a mailbox by its ID."""
    all_mailboxes = client.get_mailboxes()
    for mb in all_mailboxes:
        if mb['id'] == mailbox_id:
            return mb['name']
    return mailbox_id  # Return ID if name not found


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='File an email to a PARA subfolder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s abc123 "2025-Q1_website-redesign"     # Move email to project folder
  %(prog)s abc123 "Team Management"              # Move email to area folder
  %(prog)s abc123 "Design Templates" --copy      # Copy email to resources folder
  %(prog)s abc123 "Archived" --max-depth 2       # Search up to 2 levels deep

The script will:
1. Search for the folder in 100_projects, 200_areas, and 300_resources
2. Search recursively through the entire hierarchy (unless --max-depth is specified)
3. Move the email to the found folder (or copy with --copy flag)

By default, the email is MOVED (removed from current location).
Use --copy to keep the email in its current location as well.
        """
    )
    parser.add_argument(
        'email_id',
        type=str,
        help='ID of the email to file'
    )
    parser.add_argument(
        'folder_name',
        type=str,
        help='Name of the target folder (exact match required)'
    )
    parser.add_argument(
        '--copy',
        action='store_true',
        help='Copy instead of move (keeps email in original location)'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt and proceed with filing'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=None,
        help='Maximum depth to search in PARA folders (default: unlimited)'
    )
    args = parser.parse_args()

    # Load credentials with read-write access
    try:
        host, api_token = load_jmap_credentials_rw()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure your .env file contains:")
        print("  JMAP_HOST=api.fastmail.com")
        print("  JMAP_API_TOKEN_RW=your-read-write-token")
        sys.exit(1)

    # Create client and connect
    try:
        client = JMAPClient(host, api_token)
        client.connect()
    except Exception as e:
        print(f"Error connecting to JMAP server: {e}")
        sys.exit(1)

    # Get email information
    print(f"Retrieving email {args.email_id}...")
    try:
        email_info = get_email_info(client, args.email_id)
        if not email_info:
            print(f"Error: Email '{args.email_id}' not found")
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"✓ Found email")
    print(f"  Subject: {email_info['subject']}")
    if email_info['from']:
        from_addr = email_info['from'][0]
        from_str = from_addr.get('name', from_addr.get('email', 'Unknown'))
        print(f"  From: {from_str}")
    print(f"  Received: {email_info['receivedAt']}")

    # Show current mailboxes
    current_mailboxes = list(email_info['mailboxIds'].keys())
    if current_mailboxes:
        print(f"  Current location(s):")
        for mb_id in current_mailboxes:
            mb_name = get_mailbox_name(client, mb_id)
            print(f"    - {mb_name}")
    print()

    # Search for the target folder
    print(f"Searching for folder '{args.folder_name}' in PARA structure...")
    depth_msg = f"max depth: {args.max_depth}" if args.max_depth is not None else "unlimited depth"
    print(f"  Searching: 100_projects, 200_areas, 300_resources ({depth_msg})")
    print()

    target_folder = find_folder_in_para(client, args.folder_name, max_depth=args.max_depth)

    if not target_folder:
        print(f"Error: Folder '{args.folder_name}' not found")
        if args.max_depth is not None:
            print(f"\nSearched up to {args.max_depth} level(s) deep in:")
        else:
            print("\nSearched all descendants of:")
        print("  - 100_projects")
        print("  - 200_areas")
        print("  - 300_resources")
        print("\nUse jmap_list_folders.py to see available folders")
        if args.max_depth is not None:
            print(f"Or try without --max-depth to search the entire hierarchy")
        sys.exit(1)

    target_id = target_folder['id']
    para_parent = target_folder['paraParent']

    print(f"✓ Found target folder: {args.folder_name}")
    print(f"  ID: {target_id}")
    print(f"  Location: {para_parent}")
    print()

    # Confirm the operation
    operation = "copy" if args.copy else "move"
    print(f"Ready to {operation} email")
    print(f"  Email: {email_info['subject'][:60]}")
    print(f"  To: {para_parent}/{args.folder_name}")
    if args.copy:
        print(f"  Note: Email will remain in current location(s)")
    else:
        print(f"  Note: Email will be removed from current location(s)")
    print()

    if not args.yes:
        response = input("Continue? [y/N]: ")
        if response.lower() not in ('y', 'yes'):
            print("Cancelled.")
            sys.exit(0)
    else:
        print("Auto-confirming (--yes flag provided)")
        print()

    # File the email
    print(f"\nFiling email...")
    try:
        success = file_email(client, args.email_id, target_id, copy=args.copy)
        if success:
            print(f"\n{'='*80}")
            # Format operation properly (move -> moved, copy -> copied)
            operation_past = 'copied' if args.copy else 'moved'
            print(f"SUCCESS: Email {operation_past}")
            print(f"{'='*80}")
            print(f"Email: {email_info['subject'][:60]}")
            print(f"Filed to: {para_parent}/{args.folder_name}")
            if args.copy:
                print(f"Operation: Copied (kept in original location)")
            else:
                print(f"Operation: Moved (removed from original location)")
            print(f"{'='*80}")
        else:
            print(f"\nError: Filing operation did not complete successfully")
            sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

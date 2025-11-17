#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jmapc>=0.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
JMAP Folder Archive Script

Searches for a folder in the PARA structure (100_projects, 200_areas, 300_resources)
and moves it to 400_archives. Searches one level deep only (immediate subfolders).

Uses a read-write API token for modification operations.
"""

import argparse
import os
import sys
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from jmap_common import JMAPClient
from jmapc.methods import MailboxSet


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


def find_folder_in_para(client: JMAPClient, folder_name: str) -> Optional[Dict[str, Any]]:
    """
    Search for a folder by name in the PARA structure.
    Searches one level deep in 100_projects, 200_areas, and 300_resources.

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

    # Search for the folder name in children of each PARA parent
    for para_name, para_id in para_parents.items():
        if para_id is None:
            continue

        # Find all children of this PARA folder
        for mb in all_mailboxes:
            parent_id = mb.get('parentId')
            if parent_id == para_id and mb['name'] == folder_name:
                # Found it!
                mb['paraParent'] = para_name
                mb['paraParentId'] = para_id
                return mb

    return None


def move_folder_to_archive(client: JMAPClient, folder_id: str, archive_parent_id: str) -> bool:
    """
    Move a folder to the archive by updating its parentId.

    Returns True if successful, False otherwise.
    """
    if not client.client:
        raise ValueError("Client not connected. Call connect() first.")

    try:
        # Use MailboxSet to update the folder's parentId
        result = client.client.request(
            MailboxSet(
                update={
                    folder_id: {
                        'parentId': archive_parent_id,
                    }
                }
            )
        )

        # Check for errors
        if hasattr(result, 'not_updated') and result.not_updated:
            error_info = result.not_updated.get(folder_id, {})
            raise ValueError(f"Failed to move folder: {error_info}")

        # Check if update was successful
        if hasattr(result, 'updated') and result.updated:
            if folder_id in result.updated:
                return True

        raise ValueError("Folder move response did not contain expected data")

    except Exception as e:
        raise ValueError(f"Error moving folder: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Archive a PARA folder by moving it to 400_archives',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "2024-Q4_website-redesign"     # Archive a completed project
  %(prog)s "Old Team Management"          # Archive an area
  %(prog)s "Outdated Templates"           # Archive resources

The script will:
1. Search for the folder in 100_projects, 200_areas, and 300_resources
2. Only search immediate subfolders (one level deep)
3. Move the found folder (and all its contents) to 400_archives
        """
    )
    parser.add_argument(
        'folder_name',
        type=str,
        help='Name of the folder to archive (exact match required)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be archived without actually moving anything'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt and proceed with archiving'
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

    # Find the archive folder
    print(f"Looking for archive folder '400_archives'...")
    archive_folder = client.get_mailbox_by_name('400_archives')

    if not archive_folder:
        print("Error: Archive folder '400_archives' not found")
        print("\nThe PARA structure requires a folder named '400_archives' to exist.")
        print("Use jmap_list_folders.py to see available folders")
        sys.exit(1)

    archive_id = archive_folder['id']
    print(f"✓ Found archive folder (ID: {archive_id})")
    print()

    # Search for the folder to archive
    print(f"Searching for folder '{args.folder_name}' in PARA structure...")
    print("  Searching: 100_projects, 200_areas, 300_resources (one level deep)")
    print()

    folder_to_archive = find_folder_in_para(client, args.folder_name)

    if not folder_to_archive:
        print(f"Error: Folder '{args.folder_name}' not found")
        print("\nSearched in immediate subfolders of:")
        print("  - 100_projects")
        print("  - 200_areas")
        print("  - 300_resources")
        print("\nUse jmap_list_folders.py to see available folders")
        sys.exit(1)

    folder_id = folder_to_archive['id']
    para_parent = folder_to_archive['paraParent']

    print(f"✓ Found folder: {args.folder_name}")
    print(f"  ID: {folder_id}")
    print(f"  Current location: {para_parent}")
    print(f"  Total emails: {folder_to_archive.get('totalEmails', 0)}")
    print(f"  Unread emails: {folder_to_archive.get('unreadEmails', 0)}")
    print()

    # Dry run check
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print(f"\nWould move '{args.folder_name}' from '{para_parent}' to '400_archives'")
        print("Run without --dry-run to perform the actual move")
        sys.exit(0)

    # Confirm the move
    print(f"Ready to archive '{args.folder_name}'")
    print(f"  From: {para_parent}")
    print(f"  To: 400_archives")
    print()

    if not args.yes:
        response = input("Continue? [y/N]: ")
        if response.lower() not in ('y', 'yes'):
            print("Cancelled.")
            sys.exit(0)
    else:
        print("Auto-confirming (--yes flag provided)")
        print()

    # Move the folder
    print(f"\nArchiving folder...")
    try:
        success = move_folder_to_archive(client, folder_id, archive_id)
        if success:
            print(f"\n{'='*80}")
            print("SUCCESS: Folder archived")
            print(f"{'='*80}")
            print(f"Folder: {args.folder_name}")
            print(f"Moved from: {para_parent}")
            print(f"Moved to: 400_archives")
            print(f"{'='*80}")
        else:
            print("\nError: Move operation did not complete successfully")
            sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

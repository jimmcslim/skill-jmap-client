#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jmapc>=0.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
JMAP Folder Creation Script

Creates a new subfolder in one of the PARA parent folders:
- 100_projects
- 200_areas
- 300_resources

Uses a read-write API token for modification operations.
"""

import argparse
import os
import sys
from typing import Optional, Dict, Any
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


def create_folder(client: JMAPClient, parent_id: str, folder_name: str) -> Dict[str, Any]:
    """Create a new folder as a child of the specified parent."""
    if not client.client:
        raise ValueError("Client not connected. Call connect() first.")

    try:
        # Use MailboxSet to create a new mailbox
        result = client.client.request(
            MailboxSet(
                create={
                    'new-folder': {
                        'name': folder_name,
                        'parentId': parent_id,
                    }
                }
            )
        )

        # Check for errors
        if hasattr(result, 'not_created') and result.not_created:
            error_info = result.not_created.get('new-folder', {})
            raise ValueError(f"Failed to create folder: {error_info}")

        # Get the created mailbox info
        if hasattr(result, 'created') and result.created:
            created_mailbox = result.created.get('new-folder')
            if created_mailbox:
                return {
                    'id': created_mailbox.id,
                    'name': folder_name,
                    'parentId': parent_id,
                }

        raise ValueError("Folder creation response did not contain expected data")

    except Exception as e:
        raise ValueError(f"Error creating folder: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Create a new subfolder in a PARA parent folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --parent 100_projects --name "2025-Q1_website-redesign"
  %(prog)s --parent 200_areas --name "Team Management"
  %(prog)s --parent 300_resources --name "Design Templates"
        """
    )
    parser.add_argument(
        '--parent',
        type=str,
        required=True,
        choices=['100_projects', '200_areas', '300_resources'],
        help='Parent PARA folder (100_projects, 200_areas, or 300_resources)'
    )
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Name of the new subfolder to create'
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

    # Find the parent folder
    print(f"Looking for parent folder '{args.parent}'...")
    parent_mailbox = client.get_mailbox_by_name(args.parent)

    if not parent_mailbox:
        print(f"Error: Parent folder '{args.parent}' not found")
        print("\nUse jmap_list_folders.py to see available folders")
        sys.exit(1)

    parent_id = parent_mailbox['id']
    print(f"Found parent folder: {args.parent} (ID: {parent_id})")

    # Create the new folder
    print(f"\nCreating subfolder '{args.name}' in '{args.parent}'...")
    try:
        new_folder = create_folder(client, parent_id, args.name)
        print(f"\n{'='*80}")
        print("SUCCESS: Folder created")
        print(f"{'='*80}")
        print(f"Name: {new_folder['name']}")
        print(f"ID: {new_folder['id']}")
        print(f"Parent: {args.parent} ({parent_id})")
        print(f"{'='*80}")
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

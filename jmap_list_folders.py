#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jmapc>=0.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
JMAP Folder Hierarchy Listing Script

Lists the mailbox/folder hierarchy with optional depth control.
Can start from a specific folder or show all folders.
"""

import argparse
from typing import List, Dict, Any, Optional
from jmap_common import JMAPClient, load_jmap_credentials


def build_folder_tree(mailboxes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Build a tree structure from flat mailbox list."""
    children_map = {}

    # Group mailboxes by parent
    for mailbox in mailboxes:
        parent_id = mailbox.get('parentId')
        key = parent_id if parent_id else 'root'

        if key not in children_map:
            children_map[key] = []
        children_map[key].append(mailbox)

    return children_map


def display_folder(
    mailbox: Dict[str, Any],
    children_map: Dict[str, List[Dict[str, Any]]],
    depth: int = 0,
    max_depth: Optional[int] = None,
    current_depth: int = 0
) -> None:
    """Display a single folder and its children recursively."""

    # Check if we've reached max depth
    if max_depth is not None and current_depth >= max_depth:
        return

    name = mailbox.get('name', '(Unnamed)')
    role = mailbox.get('role', '')
    total_emails = mailbox.get('totalEmails', 0)
    unread_emails = mailbox.get('unreadEmails', 0)
    total_threads = mailbox.get('totalThreads', 0)
    unread_threads = mailbox.get('unreadThreads', 0)
    mailbox_id = mailbox.get('id', '')

    # Format role if present
    role_str = f" [{role}]" if role else ""

    # Indentation
    indent = "  " * depth

    print(f"{indent}{name}{role_str}")
    print(f"{indent}  ID: {mailbox_id}")
    print(f"{indent}  Emails: {unread_emails} unread / {total_emails} total")
    if total_threads > 0:
        print(f"{indent}  Threads: {unread_threads} unread / {total_threads} total")
    print()

    # Display children
    children = children_map.get(mailbox_id, [])
    # Sort children by sortOrder
    children_sorted = sorted(children, key=lambda x: x.get('sortOrder', 999))

    for child in children_sorted:
        display_folder(child, children_map, depth + 1, max_depth, current_depth + 1)


def display_folders(
    mailboxes: List[Dict[str, Any]],
    start_folder: Optional[str] = None,
    max_depth: Optional[int] = None
) -> None:
    """Display folder hierarchy."""

    if not mailboxes:
        print("No folders found.")
        return

    # Build tree structure
    children_map = build_folder_tree(mailboxes)

    # Find starting folder
    start_mailbox = None
    if start_folder:
        # Try to find by name (case-insensitive)
        start_folder_lower = start_folder.lower()
        for mailbox in mailboxes:
            if mailbox.get('name', '').lower() == start_folder_lower:
                start_mailbox = mailbox
                break

        if not start_mailbox:
            print(f"Error: Folder '{start_folder}' not found")
            return

        print(f"{'='*80}")
        print(f"Folder Hierarchy starting from: {start_mailbox.get('name')}")
        if max_depth is not None:
            print(f"Maximum depth: {max_depth}")
        print(f"{'='*80}\n")

        display_folder(start_mailbox, children_map, 0, max_depth, 0)
    else:
        # Show all root folders
        print(f"{'='*80}")
        print("Folder Hierarchy")
        print(f"Found {len(mailboxes)} folder(s)")
        if max_depth is not None:
            print(f"Maximum depth: {max_depth}")
        print(f"{'='*80}\n")

        # Get root mailboxes (those without parents)
        root_mailboxes = children_map.get('root', [])
        # Sort by sortOrder
        root_sorted = sorted(root_mailboxes, key=lambda x: x.get('sortOrder', 999))

        for mailbox in root_sorted:
            display_folder(mailbox, children_map, 0, max_depth, 0)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='List JMAP folder/mailbox hierarchy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # List all folders
  %(prog)s --max-depth 1                # List only top-level folders
  %(prog)s --start "Archive"            # List Archive folder and its subfolders
  %(prog)s --start "100_projects" --max-depth 2  # List projects with max 2 levels
        """
    )
    parser.add_argument(
        '--start',
        type=str,
        help='Starting folder name (default: show all folders from root)'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        help='Maximum depth to display (default: unlimited)'
    )
    args = parser.parse_args()

    # Load credentials
    host, api_token = load_jmap_credentials()

    # Create client and connect
    client = JMAPClient(host, api_token)
    client.connect()

    # Get all mailboxes
    mailboxes = client.get_mailboxes()

    # Display folder hierarchy
    display_folders(mailboxes, args.start, args.max_depth)


if __name__ == "__main__":
    main()

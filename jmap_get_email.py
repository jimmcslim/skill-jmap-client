#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jmapc>=0.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
JMAP Email Detail Retrieval Script

Retrieves full details of a specific email by its JMAP ID.
Shows all metadata, headers, full body content, and attachment list.
"""

import argparse
import json
from typing import Dict, Any
from jmap_common import (
    JMAPClient,
    load_jmap_credentials,
    format_email_address,
    format_datetime
)


def format_size(bytes_size: int) -> str:
    """Format byte size to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def display_email_detail(email: Dict[str, Any]) -> None:
    """Display full email details in a readable format."""

    print(f"{'='*80}")
    print(f"EMAIL DETAILS")
    print(f"{'='*80}\n")

    # Basic metadata
    print(f"ID: {email.get('id', 'N/A')}")
    print(f"Subject: {email.get('subject', '(No subject)')}")
    print()

    # Addresses
    from_addrs = email.get('from', [])
    if from_addrs:
        print("From:")
        for addr in from_addrs:
            print(f"  {format_email_address(addr)}")
        print()

    to_addrs = email.get('to', [])
    if to_addrs:
        print("To:")
        for addr in to_addrs:
            print(f"  {format_email_address(addr)}")
        print()

    cc_addrs = email.get('cc', [])
    if cc_addrs:
        print("Cc:")
        for addr in cc_addrs:
            print(f"  {format_email_address(addr)}")
        print()

    bcc_addrs = email.get('bcc', [])
    if bcc_addrs:
        print("Bcc:")
        for addr in bcc_addrs:
            print(f"  {format_email_address(addr)}")
        print()

    # Dates
    received_at = email.get('receivedAt')
    if received_at:
        print(f"Received: {format_datetime(received_at)}")

    sent_at = email.get('sentAt')
    if sent_at:
        print(f"Sent: {format_datetime(sent_at)}")
    print()

    # Thread and mailbox info
    thread_id = email.get('threadId')
    if thread_id:
        print(f"Thread ID: {thread_id}")

    mailbox_ids = email.get('mailboxIds', {})
    if mailbox_ids:
        print(f"Mailboxes: {', '.join(mailbox_ids.keys())}")
    print()

    # Flags and keywords
    keywords = email.get('keywords', {})
    if keywords:
        print("Keywords:")
        for keyword in keywords.keys():
            print(f"  {keyword}")
        print()

    # Status indicators
    is_seen = '$seen' in keywords
    is_flagged = '$flagged' in keywords
    is_draft = '$draft' in keywords
    is_answered = '$answered' in keywords

    status_parts = []
    if not is_seen:
        status_parts.append('UNREAD')
    if is_flagged:
        status_parts.append('FLAGGED')
    if is_draft:
        status_parts.append('DRAFT')
    if is_answered:
        status_parts.append('ANSWERED')

    if status_parts:
        print(f"Status: {' | '.join(status_parts)}")
    else:
        print("Status: READ")
    print()

    # Size
    size = email.get('size')
    if size:
        print(f"Size: {format_size(size)}")
        print()

    # Attachments
    has_attachment = email.get('hasAttachment', False)
    attachments = email.get('attachments', [])

    if has_attachment or attachments:
        print(f"{'='*80}")
        print("ATTACHMENTS")
        print(f"{'='*80}\n")

        if attachments:
            for idx, att in enumerate(attachments, 1):
                name = att.get('name', 'Unnamed')
                att_type = att.get('type', 'unknown')
                att_size = att.get('size', 0)
                disposition = att.get('disposition', 'attachment')

                print(f"[{idx}] {name}")
                print(f"    Type: {att_type}")
                print(f"    Size: {format_size(att_size)}")
                print(f"    Disposition: {disposition}")

                cid = att.get('cid')
                if cid:
                    print(f"    Content-ID: {cid}")
                print()
        else:
            print("(Attachment flag set but no attachments listed)")
            print()

    # Headers
    headers = email.get('headers', [])
    if headers:
        print(f"{'='*80}")
        print("HEADERS")
        print(f"{'='*80}\n")
        for header in headers:
            name = header.get('name', 'Unknown')
            value = header.get('value', '')
            print(f"{name}: {value}")
        print()

    # Preview
    preview = email.get('preview')
    if preview:
        print(f"{'='*80}")
        print("PREVIEW")
        print(f"{'='*80}\n")
        print(preview)
        print()

    # Body content
    body_values = email.get('bodyValues', {})
    if body_values:
        print(f"{'='*80}")
        print("BODY CONTENT")
        print(f"{'='*80}\n")

        for part_id, body_value in body_values.items():
            value = body_value.get('value', '')
            is_truncated = body_value.get('isTruncated', False)

            print(f"Part ID: {part_id}")
            if is_truncated:
                print("(Truncated)")
            print(f"{'-'*80}")
            print(value)
            print()

    # HTML body structure if available
    html_body = email.get('htmlBody', [])
    if html_body:
        print(f"{'='*80}")
        print("HTML BODY STRUCTURE")
        print(f"{'='*80}\n")
        # Convert EmailBodyPart objects to dict representation
        try:
            if isinstance(html_body, list):
                html_parts = []
                for part in html_body:
                    if hasattr(part, '__dict__'):
                        html_parts.append(str(part))
                    else:
                        html_parts.append(part)
                for part in html_parts:
                    print(part)
            else:
                print(html_body)
        except Exception as e:
            print(f"(Unable to display HTML body structure: {e})")
        print()

    # Text body structure if available
    text_body = email.get('textBody', [])
    if text_body:
        print(f"{'='*80}")
        print("TEXT BODY STRUCTURE")
        print(f"{'='*80}\n")
        # Convert EmailBodyPart objects to dict representation
        try:
            if isinstance(text_body, list):
                text_parts = []
                for part in text_body:
                    if hasattr(part, '__dict__'):
                        text_parts.append(str(part))
                    else:
                        text_parts.append(part)
                for part in text_parts:
                    print(part)
            else:
                print(text_body)
        except Exception as e:
            print(f"(Unable to display text body structure: {e})")
        print()


def get_email_by_id(client: JMAPClient, email_id: str) -> Dict[str, Any]:
    """Retrieve a specific email by ID with all details."""
    if not client.client:
        raise ValueError("Client not connected. Call connect() first.")

    try:
        from jmapc.methods import EmailGet

        # Request the email with all available properties
        result = client.client.request(
            EmailGet(
                ids=[email_id],
                properties=None,  # None means get all properties
                fetch_all_body_values=True,
                fetch_text_body_values=True,
                fetch_html_body_values=True,
            )
        )

        # Extract email from response
        if hasattr(result, 'response'):
            email_get_response = result.response
        else:
            email_get_response = result

        email_list = email_get_response.data if hasattr(email_get_response, 'data') else email_get_response.list

        if not email_list:
            return None

        email = email_list[0]

        # Convert to dict with all available fields
        email_dict = {
            'id': email.id,
            'blobId': getattr(email, 'blob_id', None),
            'threadId': getattr(email, 'thread_id', None),
            'mailboxIds': getattr(email, 'mailbox_ids', {}),
            'keywords': getattr(email, 'keywords', {}),
            'size': getattr(email, 'size', None),
            'receivedAt': email.received_at.isoformat() if hasattr(email, 'received_at') and email.received_at else None,
            'sentAt': email.sent_at.isoformat() if hasattr(email, 'sent_at') and email.sent_at else None,
            'subject': email.subject or '',
            'from': [{'name': addr.name or '', 'email': addr.email or ''} for addr in (getattr(email, 'mail_from', None) or [])],
            'to': [{'name': addr.name or '', 'email': addr.email or ''} for addr in (getattr(email, 'to', None) or [])],
            'cc': [{'name': addr.name or '', 'email': addr.email or ''} for addr in (getattr(email, 'cc', None) or [])],
            'bcc': [{'name': addr.name or '', 'email': addr.email or ''} for addr in (getattr(email, 'bcc', None) or [])],
            'replyTo': [{'name': addr.name or '', 'email': addr.email or ''} for addr in (getattr(email, 'reply_to', None) or [])],
            'hasAttachment': getattr(email, 'has_attachment', False),
            'preview': getattr(email, 'preview', ''),
            'headers': [],
            'attachments': [],
        }

        # Handle headers
        if hasattr(email, 'headers') and email.headers:
            email_dict['headers'] = [
                {'name': h.name, 'value': h.value}
                for h in email.headers
            ]

        # Handle attachments
        if hasattr(email, 'attachments') and email.attachments:
            for att in email.attachments:
                att_dict = {
                    'partId': getattr(att, 'part_id', None),
                    'blobId': getattr(att, 'blob_id', None),
                    'size': getattr(att, 'size', 0),
                    'name': getattr(att, 'name', 'Unnamed'),
                    'type': getattr(att, 'type', 'application/octet-stream'),
                    'charset': getattr(att, 'charset', None),
                    'disposition': getattr(att, 'disposition', 'attachment'),
                    'cid': getattr(att, 'cid', None),
                    'location': getattr(att, 'location', None),
                }
                email_dict['attachments'].append(att_dict)

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
        email_dict['bodyValues'] = body_values_dict

        # Body structure - convert EmailBodyPart objects to serializable format
        if hasattr(email, 'text_body') and email.text_body:
            text_body_list = []
            for part in email.text_body:
                if hasattr(part, '__dict__'):
                    # Convert EmailBodyPart to dict
                    part_dict = {
                        'partId': getattr(part, 'part_id', None),
                        'blobId': getattr(part, 'blob_id', None),
                        'size': getattr(part, 'size', None),
                        'type': getattr(part, 'type', None),
                    }
                    text_body_list.append(part_dict)
                else:
                    text_body_list.append(str(part))
            email_dict['textBody'] = text_body_list

        if hasattr(email, 'html_body') and email.html_body:
            html_body_list = []
            for part in email.html_body:
                if hasattr(part, '__dict__'):
                    # Convert EmailBodyPart to dict
                    part_dict = {
                        'partId': getattr(part, 'part_id', None),
                        'blobId': getattr(part, 'blob_id', None),
                        'size': getattr(part, 'size', None),
                        'type': getattr(part, 'type', None),
                    }
                    html_body_list.append(part_dict)
                else:
                    html_body_list.append(str(part))
            email_dict['htmlBody'] = html_body_list

        return email_dict

    except Exception as e:
        print(f"Error retrieving email: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Retrieve full details of a specific email by ID',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s M123abc456      # Get email with ID M123abc456
  %(prog)s --json M123abc  # Output raw JSON instead of formatted display
        """
    )
    parser.add_argument(
        'email_id',
        type=str,
        help='JMAP Email ID to retrieve'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output raw JSON instead of formatted display'
    )
    args = parser.parse_args()

    # Load credentials
    host, api_token = load_jmap_credentials()

    # Create client and connect
    client = JMAPClient(host, api_token)
    client.connect()

    # Get email details
    email = get_email_by_id(client, args.email_id)

    if not email:
        print(f"Error: Email with ID '{args.email_id}' not found")
        return

    # Display results
    if args.json:
        print(json.dumps(email, indent=2))
    else:
        display_email_detail(email)


if __name__ == "__main__":
    main()

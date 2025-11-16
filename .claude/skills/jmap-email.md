# JMAP Email Management

Retrieve and manage emails from an email account using the JMAP (JSON Meta Application Protocol) standard.

## Capabilities

- Connect to JMAP-compatible email servers (Fastmail, Cyrus, etc.)
- List folder/mailbox hierarchy with depth control
- Fetch emails from specific folders
- Display email metadata (subject, from, date, preview, body)
- Support for authentication via API tokens

## Available Scripts

### 1. List Folders (`jmap_list_folders.py`)
Display the mailbox/folder hierarchy.

**Usage:**
```bash
uv run jmap_list_folders.py                              # All folders
uv run jmap_list_folders.py --max-depth 1                # Top-level only
uv run jmap_list_folders.py --start "Archive"            # From Archive folder
uv run jmap_list_folders.py --start "100_projects" --max-depth 2
```

### 2. List Emails (`jmap_list_emails.py`)
List emails from a specific folder.

**Usage:**
```bash
uv run jmap_list_emails.py                          # Inbox emails
uv run jmap_list_emails.py --folder "Sent Items"    # Sent emails
uv run jmap_list_emails.py --folder "100_projects" --limit 20
```

## When to Use

When the user asks to:
- "Show my email folders" or "List my mailboxes" → Use `jmap_list_folders.py`
- "What are my PARA folders?" → Use `jmap_list_folders.py --start "100_projects"`
- "Show emails from [folder]" → Use `jmap_list_emails.py --folder "[folder]"`
- "Fetch my emails" or "Get my recent emails" → Use `jmap_list_emails.py` (defaults to Inbox)

## Configuration

Before using this skill, ensure the user has a `.env` file with the following credentials:

```env
JMAP_HOST=api.fastmail.com
JMAP_API_TOKEN=your-api-token-here
```

**Note:** The hostname should not include `https://` - just the domain name.

For Fastmail users:
1. Go to Settings → Password & Security → App Passwords
2. Create a new app password for JMAP access
3. Use that as JMAP_API_TOKEN

## Example Interaction

User: "Fetch my recent emails"
Assistant: *Runs the JMAP fetch script and displays the results*

## Implementation Notes

- Uses JMAP Core and Mail specifications (RFC 8620, RFC 8621)
- Handles session discovery and capability checking
- Retrieves the last 10 emails by default
- Displays email metadata in a clean, readable format

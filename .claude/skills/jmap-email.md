# JMAP Email Management

Retrieve and manage emails from an email account using the JMAP (JSON Meta Application Protocol) standard.

## Capabilities

- Connect to JMAP-compatible email servers (Fastmail, Cyrus, etc.)
- List folder/mailbox hierarchy with depth control
- Fetch emails from specific folders
- Display email metadata (subject, from, date, preview, body)
- Create new subfolders in PARA parent folders
- Support for authentication via API tokens (read-only and read-write)

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

### 3. Get Email Details (`jmap_get_email.py`)
Retrieve full details of a specific email by its JMAP ID.

**Usage:**
```bash
uv run jmap_get_email.py M123abc456           # Get full email details
uv run jmap_get_email.py --json M123abc456    # Output as JSON
```

**Shows:**
- All metadata (ID, thread ID, mailbox IDs, keywords, size)
- Complete addresses (From, To, Cc, Bcc, Reply-To)
- Full body content (text and HTML)
- Complete header list
- Attachment list with names, sizes, types (does NOT download attachments)

### 4. Create Folder (`jmap_create_folder.py`)
Create a new subfolder in one of the PARA parent folders.

**Usage:**
```bash
uv run jmap_create_folder.py --parent 100_projects --name "2025-Q1_website-redesign"
uv run jmap_create_folder.py --parent 200_areas --name "Team Management"
uv run jmap_create_folder.py --parent 300_resources --name "Design Templates"
```

**Restrictions:**
- Only creates subfolders in: `100_projects`, `200_areas`, or `300_resources`
- Requires read-write API token (`JMAP_API_TOKEN_RW` in .env)

### 5. Archive Folder (`jmap_archive_folder.py`)
Move a completed project, area, or resource to the archives folder.

**Usage:**
```bash
uv run jmap_archive_folder.py "2024-Q4_website-redesign"     # Archive a project
uv run jmap_archive_folder.py "Old Team Management"          # Archive an area
uv run jmap_archive_folder.py --dry-run "Project Name"       # Preview without moving
uv run jmap_archive_folder.py --yes "Project Name"           # Skip confirmation
uv run jmap_archive_folder.py -y "Project Name"              # Short form
```

**Features:**
- Searches for folder in `100_projects`, `200_areas`, and `300_resources` (one level deep)
- Moves folder and all its contents to `400_archives`
- Requires confirmation before moving (use `--yes` or `-y` to skip)
- Supports `--dry-run` to preview without making changes
- Requires read-write API token (`JMAP_API_TOKEN_RW` in .env)

## When to Use

When the user asks to:
- "Show my email folders" or "List my mailboxes" → Use `jmap_list_folders.py`
- "What are my PARA folders?" → Use `jmap_list_folders.py --start "100_projects"`
- "Show emails from [folder]" → Use `jmap_list_emails.py --folder "[folder]"`
- "Fetch my emails" or "Get my recent emails" → Use `jmap_list_emails.py` (defaults to Inbox)
- "Get full details of email [ID]" or "Show me the complete email [ID]" → Use `jmap_get_email.py [ID]`
- "Create a folder [name] in [parent]" or "Add a new project folder" → Use `jmap_create_folder.py`
- "Archive [folder]" or "Move [folder] to archives" → Use `jmap_archive_folder.py`

## Configuration

Before using this skill, ensure the user has a `.env` file with the following credentials:

```env
JMAP_HOST=api.fastmail.com
JMAP_API_TOKEN_RO=your-read-only-token
JMAP_API_TOKEN_RW=your-read-write-token
```

**Note:** The hostname should not include `https://` - just the domain name.

**Tokens:**
- `JMAP_API_TOKEN_RO`: Read-only token for listing folders and emails
- `JMAP_API_TOKEN_RW`: Read-write token for creating folders and archiving

For Fastmail users:
1. Go to Settings → Password & Security → App Passwords
2. Create two app passwords:
   - One with read-only access (for general email viewing)
   - One with read-write access (for folder creation and modifications)
3. Use them as JMAP_API_TOKEN_RO and JMAP_API_TOKEN_RW respectively

## Example Interaction

User: "Fetch my recent emails"
Assistant: *Runs the JMAP fetch script and displays the results*

## Implementation Notes

- Uses JMAP Core and Mail specifications (RFC 8620, RFC 8621)
- Handles session discovery and capability checking
- Retrieves the last 10 emails by default
- Displays email metadata in a clean, readable format

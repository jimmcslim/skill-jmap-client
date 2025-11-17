# JMAP Email Management Skill

A Claude Code skill for managing emails using the JMAP (JSON Meta Application Protocol) standard.

## Features

- **Folder Hierarchy Browsing**: View your mailbox structure with depth control
- **Email Listing**: Fetch emails from any folder
- **PARA Method Support**: Optimized for PARA (Projects, Areas, Resources, Archives) organization
- **Modern Python**: Uses PEP 723 inline script metadata
- **Secure Credentials**: Environment-based configuration with python-dotenv

## Architecture

The skill is split into focused, single-purpose scripts:

- **`jmap_common.py`**: Shared JMAP client wrapper using the `jmapc` library
- **`jmap_list_folders.py`**: Browse folder hierarchy
- **`jmap_list_emails.py`**: List emails from folders
- **`jmap_get_email.py`**: Retrieve full details of a specific email by ID
- **`jmap_file_email.py`**: File (move or copy) emails to PARA subfolders
- **`jmap_create_folder.py`**: Create new subfolders in PARA parent folders
- **`jmap_archive_folder.py`**: Move folders from projects/areas/resources to archives

The implementation uses the [`jmapc`](https://github.com/smkent/jmapc) Python library, which provides a robust, type-safe interface to JMAP servers.

## Setup

### 1. Copy the example environment file

```bash
cp .env.example .env
```

### 2. Configure your credentials

Edit `.env` and add your JMAP server details:

```env
JMAP_HOST=api.fastmail.com
JMAP_API_TOKEN_RO=your-read-only-token
JMAP_API_TOKEN_RW=your-read-write-token
```

**Note:** The hostname should not include `https://` - just the domain name.

**Tokens:**
- `JMAP_API_TOKEN_RO`: Read-only token for listing folders and emails
- `JMAP_API_TOKEN_RW`: Read-write token for creating folders and archiving

#### Getting API Tokens

**For Fastmail:**
1. Log in to Fastmail
2. Go to Settings → Password & Security → App Passwords
3. Create two app passwords:
   - One with read-only access (for general email viewing)
   - One with read-write access (for folder creation and modifications)
4. Copy the generated tokens to your `.env` file as `JMAP_API_TOKEN_RO` and `JMAP_API_TOKEN_RW`

**For other JMAP providers:**
Consult your provider's documentation for API token generation.

## Usage

### List Folder Hierarchy

```bash
# Show all folders
uv run jmap_list_folders.py

# Show only top-level folders
uv run jmap_list_folders.py --max-depth 1

# Show a specific folder and its children
uv run jmap_list_folders.py --start "Archive"

# Show PARA projects with max 2 levels deep
uv run jmap_list_folders.py --start "100_projects" --max-depth 2
```

### List Emails

```bash
# List emails from Inbox (default)
uv run jmap_list_emails.py

# List emails from a specific folder
uv run jmap_list_emails.py --folder "Sent Items"

# List more emails
uv run jmap_list_emails.py --folder "100_projects" --limit 20

# List emails from PARA areas
uv run jmap_list_emails.py --folder "200_areas"
```

### Get Full Email Details

```bash
# Get complete details of a specific email by ID
uv run jmap_get_email.py M123abc456

# Output raw JSON for processing
uv run jmap_get_email.py --json M123abc456
```

The email detail view shows:
- All metadata (ID, thread ID, size, dates)
- Complete address fields (From, To, Cc, Bcc, Reply-To)
- Status flags (read/unread, flagged, draft, answered)
- Full email body (both text and HTML parts)
- Complete headers
- Attachment list with sizes and types (does not download files)

### File Email

```bash
# Move an email to a project folder
uv run jmap_file_email.py M123abc456 "2025-Q1_website-redesign"

# Move an email to an area folder
uv run jmap_file_email.py M123abc456 "Team Management"

# Copy an email to a resource folder (keeps in original location)
uv run jmap_file_email.py --copy M123abc456 "Design Templates"

# Skip confirmation prompt (auto-confirm)
uv run jmap_file_email.py --yes M123abc456 "Project Name"
uv run jmap_file_email.py -y M123abc456 "Project Name"
```

The file script will:
1. Search for the folder in `100_projects`, `200_areas`, and `300_resources` (one level deep)
2. Show details about the email (subject, sender, current location)
3. Ask for confirmation (use `--yes` or `-y` to skip)
4. Move the email to the target folder (or copy with `--copy`)

**Note:** By default, the email is **moved** (removed from its current location). Use `--copy` to keep the email in its original location as well. This script requires the read-write API token (`JMAP_API_TOKEN_RW`).

### Create Folder

```bash
# Create a new project folder
uv run jmap_create_folder.py --parent 100_projects --name "2025-Q1_website-redesign"

# Create a new area folder
uv run jmap_create_folder.py --parent 200_areas --name "Team Management"

# Create a new resource folder
uv run jmap_create_folder.py --parent 300_resources --name "Design Templates"
```

**Note:** This script only supports creating subfolders in the PARA parent folders: `100_projects`, `200_areas`, or `300_resources`. It requires the read-write API token (`JMAP_API_TOKEN_RW`).

### Archive Folder

```bash
# Archive a completed project
uv run jmap_archive_folder.py "2024-Q4_website-redesign"

# Archive an area or resource
uv run jmap_archive_folder.py "Old Team Management"

# Preview the archive operation without making changes
uv run jmap_archive_folder.py --dry-run "Project Name"

# Skip confirmation prompt (auto-confirm)
uv run jmap_archive_folder.py --yes "Project Name"
uv run jmap_archive_folder.py -y "Project Name"
```

The archive script will:
1. Search for the folder in `100_projects`, `200_areas`, and `300_resources` (one level deep)
2. Show details about the folder (location, email counts)
3. Ask for confirmation (use `--yes` or `-y` to skip, or `--dry-run` to preview)
4. Move the folder and all its contents to `400_archives`

**Note:** This script requires the read-write API token (`JMAP_API_TOKEN_RW`) and the `400_archives` folder must exist.

### Using with Claude Code

Simply ask Claude:
- "Show my email folders" → Lists folder hierarchy
- "What are my PARA folders?" → Shows PARA structure
- "List emails from my projects folder" → Shows emails from 100_projects
- "Fetch my recent emails" → Shows Inbox emails
- "File email M123abc to my website-redesign project" → Moves email to project folder
- "Create a project folder called 2025-Q2_mobile-app" → Creates new folder in 100_projects
- "Archive the folder 2024-Q4_website-redesign" → Moves folder to 400_archives

## Requirements

- Python 3.8+
- `uv` package manager (https://github.com/astral-sh/uv)

Dependencies are automatically managed via PEP 723 inline script metadata:
- **jmapc** - Python JMAP client library with type-safe API
- **python-dotenv** - Environment variable management

## JMAP Protocol

This skill implements the JMAP Core and Mail specifications:
- RFC 8620: JSON Meta Application Protocol (JMAP) Core
- RFC 8621: JMAP for Mail

JMAP is a modern, efficient protocol for email that uses JSON over HTTP, making it easier to work with than traditional IMAP.

## PARA Method Support

The skill is optimized for the PARA method of organization:

- **100_projects** - Active projects with deadlines
- **200_areas** - Ongoing areas of responsibility
- **300_resources** - Reference materials and resources
- **400_archives** - Inactive items for future reference

Use folder hierarchy browsing to navigate your PARA structure and list emails from specific categories.

## Example Output

### Folder Listing

```
================================================================================
Folder Hierarchy starting from: 100_projects
Maximum depth: 2
================================================================================

100_projects
  ID: P3V
  Emails: 0 unread / 0 total

  2025-11_my-50th-birthday
    ID: P69Sj
    Emails: 0 unread / 16 total
    Threads: 0 unread / 13 total

  2025-H2_renovation-31-bond-st
    ID: P3k
    Emails: 0 unread / 51 total
    Threads: 0 unread / 38 total
```

### Email Listing

```
================================================================================
Folder: Inbox
Found 3 email(s)
================================================================================

[1] Project Update: Q4 Planning
    From: Team Lead <lead@company.com>
    Date: 2025-11-16 14:30:00 UTC
    Status: UNREAD
    Preview: Here's the update on our Q4 planning session...
    Body: Here's the update on our Q4 planning session. We've identified...
--------------------------------------------------------------------------------
```

## Troubleshooting

**Authentication Error:**
- Verify your credentials in `.env` are correct
- For Fastmail, ensure you're using an app password, not your account password
- Check that JMAP_HOST is just the hostname (e.g., `api.fastmail.com`), not a full URL
- Ensure JMAP_HOST does not include `https://` or `http://`

**Connection Error:**
- Ensure you have internet connectivity
- Verify the JMAP server URL is accessible
- Check if your provider supports JMAP

**Folder Not Found:**
- Use `jmap_list_folders.py` to see all available folders
- Folder names are case-sensitive

**No Emails Found:**
- Verify the folder contains emails
- Try increasing the `--limit` parameter
- Check that you're looking in the right folder

## License

MIT

# CLAUDE.md - AI Assistant Guide for JMAP Email Management Skill

This document provides comprehensive guidance for AI assistants working with this codebase. Last updated: 2025-11-17

## Repository Overview

**Purpose**: A Claude Code skill for managing emails using the JMAP (JSON Meta Application Protocol) standard, optimized for the PARA (Projects, Areas, Resources, Archives) organizational method.

**Technology Stack**:
- Python 3.12+
- PEP 723 inline script metadata for dependency management
- `uv` package manager for execution
- `jmapc` library (type-safe Python JMAP client)
- `python-dotenv` for environment configuration

**Key Features**:
- Folder hierarchy browsing with depth control
- Email listing and retrieval
- PARA method support (100_projects, 200_areas, 300_resources, 400_archives)
- Folder creation and archiving operations
- Secure credential management

## Codebase Structure

### File Organization

```
skill-jmap-client/
├── jmap_common.py           # Shared JMAP client wrapper and utilities
├── jmap_list_folders.py     # Browse folder hierarchy
├── jmap_list_emails.py      # List emails from folders
├── jmap_get_email.py        # Retrieve full email details by ID
├── jmap_create_folder.py    # Create new subfolders in PARA structure
├── jmap_archive_folder.py   # Move folders to 400_archives
├── .env.example             # Environment configuration template
├── .gitignore               # Git ignore patterns
└── README.md                # User-facing documentation
```

### Script Architecture

All scripts follow a consistent pattern:

1. **PEP 723 Headers**: Every executable script starts with inline dependency metadata
2. **Single Responsibility**: Each script performs one focused task
3. **Shared Core**: Common functionality centralized in `jmap_common.py`
4. **CLI Interface**: All scripts use `argparse` for consistent CLI experience
5. **Environment Config**: Credentials loaded via `.env` file using `python-dotenv`

## Core Components

### jmap_common.py

**Purpose**: Centralized JMAP client wrapper and shared utilities.

**Key Classes/Functions**:

- `JMAPClient`: Main client wrapper class
  - `__init__(host, api_token)`: Initialize with connection details
  - `connect()`: Establish connection to JMAP server
  - `get_mailboxes()`: Retrieve all mailboxes (returns list of dicts)
  - `get_mailbox_by_name(name)`: Find mailbox by name (case-insensitive)
  - `get_mailbox_by_role(role)`: Find mailbox by role (e.g., 'inbox')
  - `get_emails(mailbox_id, limit)`: Retrieve emails with filtering

- `load_jmap_credentials()`: Load read-only credentials from `.env`
- `format_email_address(addr)`: Format email address objects as strings
- `format_datetime(dt_str)`: Convert ISO datetime to readable format

**Important Notes**:
- All mailbox data is converted from `jmapc` objects to dicts for compatibility
- Host URLs are automatically stripped of `https://` prefix
- Client connection should be called before any operations
- Returns structured dictionaries with consistent key names

### Executable Scripts Pattern

All executable scripts follow this structure:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jmapc>=0.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
Script description
"""

import argparse
from jmap_common import JMAPClient, load_jmap_credentials

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()

    # Load credentials
    host, api_token = load_jmap_credentials()

    # Connect client
    client = JMAPClient(host, api_token)
    client.connect()

    # Perform operations
    ...

if __name__ == "__main__":
    main()
```

## Key Conventions

### Code Style

1. **Type Hints**: Use type hints for function parameters and return values
   - Example: `def get_emails(mailbox_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:`

2. **Docstrings**: All functions and classes have descriptive docstrings
   - Single-line for simple functions
   - Multi-line for complex operations

3. **Error Handling**:
   - Use try/except blocks for external operations
   - Print user-friendly error messages
   - Exit with `sys.exit(1)` on fatal errors
   - Provide actionable troubleshooting guidance

4. **Formatting**:
   - Use f-strings for string formatting
   - 80-character line separator: `'='*80`
   - Consistent indentation (4 spaces)

### Naming Conventions

- **Scripts**: `jmap_<action>_<target>.py` (e.g., `jmap_list_folders.py`)
- **Functions**: Snake_case (e.g., `get_mailbox_by_name`)
- **Classes**: PascalCase (e.g., `JMAPClient`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `JMAP_HOST`)
- **Private methods**: Leading underscore (e.g., `_internal_helper`)

### Data Structures

**Mailbox Dictionary**:
```python
{
    'id': str,              # Unique mailbox ID
    'name': str,            # Display name
    'role': Optional[str],  # JMAP role (inbox, sent, trash, etc.)
    'sortOrder': int,       # Sort order number
    'parentId': Optional[str],  # Parent mailbox ID
    'totalEmails': int,     # Total email count
    'unreadEmails': int,    # Unread email count
    'totalThreads': int,    # Total thread count
    'unreadThreads': int    # Unread thread count
}
```

**Email Dictionary**:
```python
{
    'id': str,
    'subject': str,
    'from': List[{'name': str, 'email': str}],
    'to': List[{'name': str, 'email': str}],
    'receivedAt': str,  # ISO datetime
    'preview': str,
    'hasAttachment': bool,
    'keywords': Dict[str, bool],
    'bodyValues': Dict[str, {'value': str, 'isEncodingProblem': bool, 'isTruncated': bool}]
}
```

### PARA Folder Structure

The codebase is optimized for PARA method folders:

- `100_projects`: Active projects with deadlines
- `200_areas`: Ongoing areas of responsibility
- `300_resources`: Reference materials and resources
- `400_archives`: Inactive items for future reference

**Important**:
- Folder creation (`jmap_create_folder.py`) only supports creating subfolders in the first three
- Archiving (`jmap_archive_folder.py`) moves folders to `400_archives`
- Search operations in PARA scripts only go one level deep

## Environment Configuration

### Credential Management

**Required Environment Variables**:
```env
JMAP_HOST=api.fastmail.com              # Hostname only, no https://
JMAP_API_TOKEN_RO=<read-only-token>     # For listing/reading operations
JMAP_API_TOKEN_RW=<read-write-token>    # For create/modify operations
```

**Token Usage**:
- `JMAP_API_TOKEN_RO`: Used by list/get scripts (read-only operations)
- `JMAP_API_TOKEN_RW`: Used by create/archive scripts (write operations)

**Security Best Practices**:
- `.env` file is gitignored
- Never commit actual credentials
- Use separate tokens for read/write to minimize permissions
- For Fastmail: Create app passwords, not account password

### Configuration Loading

All scripts use this pattern:
```python
from dotenv import load_dotenv

def load_jmap_credentials() -> tuple[str, str]:
    load_dotenv()  # Loads .env file
    host = os.getenv('JMAP_HOST')
    api_token = os.getenv('JMAP_API_TOKEN_RO')
    # Validation and cleanup
    return host, api_token
```

## Development Workflows

### Adding a New Script

1. **Create file**: Follow naming convention `jmap_<action>_<target>.py`
2. **Add PEP 723 header**: Include script dependencies
3. **Import common**: Use `from jmap_common import JMAPClient, load_jmap_credentials`
4. **Follow script pattern**: Use established argparse + main() structure
5. **Handle errors**: Provide user-friendly messages and troubleshooting
6. **Update README**: Add usage examples and documentation
7. **Test with uv**: Run with `uv run <script>.py`

### Extending JMAPClient

When adding new functionality to `jmap_common.py`:

1. **Add method to JMAPClient class**
2. **Use jmapc library methods** (import from `jmapc.methods`)
3. **Convert jmapc objects to dicts** for return values
4. **Handle errors gracefully** with try/except
5. **Add type hints** for parameters and return values
6. **Write descriptive docstring**

Example:
```python
def get_thread(self, thread_id: str) -> List[Dict[str, Any]]:
    """Retrieve all emails in a thread."""
    if not self.client:
        raise ValueError("Client not connected. Call connect() first.")

    try:
        # Implementation using jmapc
        result = self.client.request(...)
        # Convert to dict format
        return [...]
    except Exception as e:
        print(f"Error retrieving thread: {e}")
        sys.exit(1)
```

### Testing Approach

**Manual Testing Workflow**:
1. Ensure `.env` is configured with test credentials
2. Use `uv run <script>.py` to execute
3. Test with various arguments and edge cases
4. Verify output format matches documentation
5. Check error handling with invalid inputs

**Test Scenarios**:
- Empty folders
- Non-existent folders
- Missing credentials
- Network errors
- Invalid API tokens
- PARA structure variations

### Git Workflow

**Branch Naming**: `claude/claude-md-<session-id>`

**Commit Message Pattern**:
```
<type>: <description>

Examples:
feat: added archive and create functionality
fix: handle missing folder edge case
docs: update README with new examples
refactor: extract common validation logic
```

**Push Commands**:
```bash
git push -u origin <branch-name>
# Retry with exponential backoff on network errors
```

## JMAP Protocol Specifics

### Protocol References

- RFC 8620: JMAP Core specification
- RFC 8621: JMAP for Mail
- Uses JSON over HTTP instead of IMAP

### Key JMAP Concepts

**Mailboxes**: Equivalent to folders, have hierarchical structure via `parentId`

**Emails**: Immutable objects with metadata and body parts

**Threads**: Group related emails together

**Roles**: Special mailbox types (inbox, sent, trash, drafts, etc.)

### jmapc Library Usage

The codebase uses the `jmapc` library which provides:
- Type-safe Python interface
- Request/response objects
- Automatic session handling
- Built-in error handling

**Common jmapc imports**:
```python
from jmapc import Client, Ref, Comparator
from jmapc.methods import (
    MailboxGet, MailboxGetResponse, MailboxSet,
    EmailQuery, EmailGet,
    EmailQueryFilterCondition
)
```

## AI Assistant Guidelines

### When Making Changes

1. **Read first**: Always read files before editing
2. **Understand context**: Review related files and common utilities
3. **Follow patterns**: Match existing code style and structure
4. **Test mentally**: Consider edge cases before implementation
5. **Update docs**: Modify README.md if user-facing changes
6. **Preserve safety**: Don't commit `.env` or credentials

### Common Tasks

**Adding email filtering**:
- Modify `jmap_common.py` `get_emails()` method
- Use `EmailQueryFilterCondition` from jmapc
- Add appropriate CLI arguments to calling scripts

**Adding new folder operations**:
- Check if read-only or read-write token needed
- Use `MailboxSet` for modifications
- Follow PARA structure constraints if applicable
- Add confirmation prompts for destructive operations

**Improving error handling**:
- Catch specific exceptions when possible
- Provide actionable error messages
- Reference documentation (README.md sections)
- Exit with appropriate status codes

### Code Quality Checklist

Before committing changes:

- [ ] Type hints present on all function signatures
- [ ] Docstrings written for all functions/classes
- [ ] Error messages are user-friendly and actionable
- [ ] Follows existing code style and naming conventions
- [ ] No hardcoded credentials or sensitive data
- [ ] PEP 723 headers updated if dependencies change
- [ ] README.md updated if user-facing changes
- [ ] Tested with `uv run` command

### Debugging Tips

**Connection Issues**:
- Verify `.env` has correct credentials
- Check that `JMAP_HOST` has no `https://` prefix
- Test network connectivity to JMAP server
- Try read-only token first (simpler permissions)

**Folder Not Found**:
- Run `jmap_list_folders.py` to see actual structure
- Check for case sensitivity in folder names
- Verify PARA parent folders exist

**jmapc Errors**:
- Check jmapc library documentation: https://github.com/smkent/jmapc
- Verify correct method imports from `jmapc.methods`
- Ensure proper request/response object handling
- Convert jmapc objects to dicts when returning data

## Common Pitfalls

1. **Forgetting to strip https:// from JMAP_HOST**: The `jmapc` library expects just the hostname
2. **Not converting jmapc objects to dicts**: Return values should be standard Python dicts
3. **Hardcoding folder IDs**: Always look up by name, IDs vary per account
4. **Missing read-write token**: Create/modify operations require `JMAP_API_TOKEN_RW`
5. **Deep PARA searches**: Archive/create scripts intentionally only go one level deep
6. **Assuming folder structure**: PARA folders may not exist, always verify

## Performance Considerations

- **Mailbox listing**: Cached after first `get_mailboxes()` call in session
- **Email queries**: Use `limit` parameter to control result size
- **Deep hierarchies**: Use `max_depth` parameter to limit traversal
- **Body values**: Limited to 5000 bytes by default in email queries

## Future Enhancement Ideas

Potential areas for expansion:

- Email sending capability (requires EmailSubmission methods)
- Thread-based operations
- Search functionality with complex filters
- Email flagging and keyword management
- Attachment download support
- Batch operations
- Calendar integration (JMAP Calendar spec)
- Automated PARA folder maintenance

## Additional Resources

- **JMAP Official Site**: https://jmap.io/
- **jmapc Library**: https://github.com/smkent/jmapc
- **PEP 723 (Inline Dependencies)**: https://peps.python.org/pep-0723/
- **uv Package Manager**: https://github.com/astral-sh/uv
- **PARA Method**: https://fortelabs.com/blog/para/

## Questions and Troubleshooting

When encountering issues:

1. Check the README.md Troubleshooting section
2. Review `.env.example` for configuration format
3. Run `jmap_list_folders.py` to verify connectivity
4. Check git commit history for recent changes
5. Review jmapc library documentation for API details

---

**Document Maintenance**: Keep this file updated when making significant architectural changes, adding new conventions, or discovering important patterns.

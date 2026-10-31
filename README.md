# Google Drive CLI Manager

A minimalist, high-performance CLI for managing Google Drive files, folders, and backups. Supports all file formats (binaries, databases, media, documents, archives, and spreadsheets) with built-in OAuth 2.0 token management and structured CSV appending.

## Features

- **Universal File Support:** Upload and download any file format (`.tar.gz`, `.sqlite`, `.png`, `.pdf`, `.json`, etc.) with automatic MIME detection and binary stream fallback.
- **Folder Hierarchy:** Create nested directories (`mkdir`) and inspect folder contents (`ls`).
- **File Lifecycle:** Download files by name or Google Drive ID, and delete files with Trash protection or permanent deletion flags.
- **In-Drive CSV Appender:** Append rows directly to remote CSV files without downloading and re-uploading the entire file.
- **OAuth 2.0 Auto-Refresh:** Automatically refreshes expired OAuth credentials using local refresh tokens.

---

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or standard `pip`

---

## Setup & Authentication

1. Enable the **Google Drive API** in your Google Cloud Console.
2. Create an **OAuth 2.0 Client ID** (Application type: *Desktop App*).
3. Generate your credentials and save the token as `google_token.json` in the project root, or specify its path via the `GOOGLE_TOKEN_PATH` environment variable:

```bash
export GOOGLE_TOKEN_PATH="/path/to/google_token.json"
```

---

## Usage

Run directly with `uv` (dependencies are resolved automatically):

### 1. Browse and Manage Folders

```bash
# List files in root Drive
uv run gdrive_cli.py ls

# List files inside a specific folder
uv run gdrive_cli.py ls --folder "Backup"

# Create a new folder
uv run gdrive_cli.py mkdir "Database"

# Create a nested subfolder
uv run gdrive_cli.py mkdir "Daily" --parent "Database"
```

### 2. Upload Any File

```bash
# Upload a database backup
uv run gdrive_cli.py upload ./backup.sqlite --folder "Database"

# Upload an archive
uv run gdrive_cli.py upload ./archive.tar.gz --folder "Backup"

# Upload with a custom remote filename
uv run gdrive_cli.py upload ./local_file.log --name "server-2026-10-31.log" --folder "Logs"
```

### 3. Download Files

```bash
# Download by filename
uv run gdrive_cli.py download "backup.sqlite" --output "./restored.sqlite"

# Download by Google Drive File ID
uv run gdrive_cli.py download "1UQysuF5r3OdfJWX03O7TT8o7KECHYb5L" --output "./data.zip"
```

### 4. Delete Files & Folders

```bash
# Move file to Trash (can be restored from Google Drive UI)
uv run gdrive_cli.py rm "old_archive.tar.gz"

# Permanently delete file
uv run gdrive_cli.py rm "old_archive.tar.gz" --permanent
```

### 5. Append Rows to Remote CSV

```bash
uv run gdrive_cli.py csv-append "accounts.csv" \
  --row '["1", "user@example.com", "hint_code", "2026-10-31", "notes"]' \
  --folder "Backup"
```

---

## License

MIT

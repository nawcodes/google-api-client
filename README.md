# Google Drive Universal CLI Manager

A minimalist, high-performance CLI utility for managing Google Drive files, folders, and backups. Supports all file formats (binaries, databases, media, documents, archives, and spreadsheets) with built-in OAuth 2.0 token management, hierarchical credential resolution, and in-place CSV row appending.

## Features

- **Universal File Support:** Upload and download any file format (`.tar.gz`, `.sqlite`, `.png`, `.pdf`, `.json`, etc.) with automatic MIME detection and binary stream fallback.
- **Direct OAuth CLI Auth:** Built-in `auth` command to authenticate with Google Cloud OAuth 2.0 (local browser server or headless terminal URL copy flow).
- **Zero Hardcoded Paths:** Resolves credentials hierarchically via CLI flag, environment variables (`.env`), local directory, or standard user config (`~/.config/gdrive/`).
- **Folder Hierarchy:** Create nested directories (`mkdir`) and inspect folder contents (`ls`).
- **File Lifecycle:** Download files by name or Google Drive ID, and delete files with Trash protection or permanent deletion flags.
- **In-Drive CSV Appender:** Append rows directly to remote CSV files without downloading and re-uploading the entire file.

---

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or standard `pip`

---

## Setup & Authentication

### 1. Obtain Google Cloud OAuth Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Drive API** under **APIs & Services > Library**.
3. Under **APIs & Services > Credentials**, create an **OAuth 2.0 Client ID**:
   - Application type: **Desktop App**.
4. Download the generated client secret JSON file (e.g. `client_secret.json`).

### 2. Authorize
Run the interactive `auth` command:

```bash
# Standard browser login (opens default web browser)
uv run gdrive_cli.py auth --client-secret client_secret.json

# Headless / remote server login (prints auth URL to copy-paste into terminal)
uv run gdrive_cli.py auth --client-secret client_secret.json --headless
```

By default, the token is saved securely to `~/.config/gdrive/token.json`.

---

## Environment Configuration (Optional)

You can copy `.env.example` to `.env` to customize paths:

```bash
cp .env.example .env
```

Available environment variables:
- `GDRIVE_TOKEN_PATH`: Custom path to `token.json`.
- `GDRIVE_CLIENT_SECRET_PATH`: Path to OAuth client secret.

---

## Usage

Run directly with `uv` (dependencies are resolved automatically):

### 1. Browse and Manage Folders

```bash
# List files in root Drive
uv run gdrive_cli.py ls

# List files inside a specific folder (by folder name or folder ID)
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
uv run gdrive_cli.py upload ./local_file.log --name "server-2026-11-01.log" --folder "Logs"
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
uv run gdrive_cli.py rm "sensitive_file.txt" --permanent
```

### 5. Append Rows to Remote CSV

```bash
uv run gdrive_cli.py csv-append "accounts.csv" \
  --row '["1", "user@example.com", "hint_code", "2026-11-01", "notes"]' \
  --folder "Backup"
```

---

## License

MIT

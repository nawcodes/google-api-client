# Google API Client (Drive Manager)

CLI minimalis untuk manajemen backup Google Drive (Folder & CSV).

## Fitur
- Pembuatan struktur folder otomatis di Google Drive
- Upload & update file CSV secara aman
- Append data baris baru ke CSV yang sudah ada
- Otentikasi OAuth 2.0 dengan auto-refresh token

## Cara Pakai (dengan uv)
```bash
# List file/folder
uv run gdrive_cli.py ls --folder Account

# Buat folder baru
uv run gdrive_cli.py mkdir NamaFolder --parent ParentID_atau_Nama

# Upload CSV
uv run gdrive_cli.py upload email_accounts.csv --folder Account

# Append baris ke CSV
uv run gdrive_cli.py csv-append email_accounts.csv --row '["id", "email@gmail.com", "hint", "", "", "date", "notes"]' --folder Account
```

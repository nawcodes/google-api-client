#!/usr/bin/env python3
# /// script
# dependencies = [
#   "google-api-python-client",
#   "google-auth",
#   "google-auth-oauthlib",
#   "google-auth-httplib2"
# ]
# ///

"""
gdrive_cli.py - Google Drive CLI using user OAuth credentials.
"""

import sys
import io
import csv
import json
import argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload, MediaFileUpload

TOKEN_PATH = Path('/opt/data/google_token.json')
CLIENT_SECRET_PATH = Path('/opt/data/google_client_secret.json')

def get_service():
    if not TOKEN_PATH.exists():
        print(f"Error: Token not found at {TOKEN_PATH}", file=sys.stderr)
        sys.exit(1)
    
    with open(TOKEN_PATH, 'r', encoding='utf-8') as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(token_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def find_item(service, name, mime_type=None, parent_id=None):
    q = f"name = '{name}' and trashed = false"
    if mime_type:
        q += f" and mimeType = '{mime_type}'"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = service.files().list(q=q, fields="files(id, name, mimeType, parents)").execute()
    items = res.get('files', [])
    return items[0] if items else None

def create_folder(service, name, parent_id=None):
    existing = find_item(service, name, mime_type='application/vnd.google-apps.folder', parent_id=parent_id)
    if existing:
        return existing
    body = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        body['parents'] = [parent_id]
    return service.files().create(body=body, fields='id, name, webViewLink').execute()

def append_csv_row(service, filename, row, headers=None, parent_id=None):
    existing_file = find_item(service, filename, parent_id=parent_id)
    
    rows = []
    if existing_file:
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, service.files().get_media(fileId=existing_file['id']))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        content = fh.getvalue().decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
    else:
        if headers:
            rows.append(headers)

    rows.append(row)

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerows(rows)
    csv_bytes = out.getvalue().encode('utf-8')

    media = MediaInMemoryUpload(csv_bytes, mimetype='text/csv', resumable=True)
    if existing_file:
        return service.files().update(fileId=existing_file['id'], media_body=media, fields='id, name, webViewLink').execute()
    else:
        body = {'name': filename}
        if parent_id:
            body['parents'] = [parent_id]
        return service.files().create(body=body, media_body=media, fields='id, name, webViewLink').execute()

def main():
    parser = argparse.ArgumentParser(description="Drive Manager")
    sub = parser.add_subparsers(dest="cmd")

    p_f = sub.add_parser("mkdir")
    p_f.add_argument("name")
    p_f.add_argument("--parent", help="Parent folder name or ID")

    p_c = sub.add_parser("csv-append")
    p_c.add_argument("file")
    p_c.add_argument("--row", required=True, help="JSON list of values, e.g. '[\"a\",\"b\"]'")
    p_c.add_argument("--headers", help="JSON list of headers if creating fresh file")
    p_c.add_argument("--folder", help="Folder name or ID where file lives")

    p_u = sub.add_parser("upload")
    p_u.add_argument("file_path")
    p_u.add_argument("--name", help="Remote filename")
    p_u.add_argument("--folder", help="Folder name or ID where file lives")

    p_l = sub.add_parser("ls")
    p_l.add_argument("--folder", help="Folder name or ID")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    service = get_service()

    parent_id = None
    if getattr(args, "parent", None) or getattr(args, "folder", None):
        target = getattr(args, "parent", None) or getattr(args, "folder", None)
        if len(target) > 20 and " " not in target:
            parent_id = target
        else:
            folder_item = find_item(service, target, mime_type='application/vnd.google-apps.folder')
            if folder_item:
                parent_id = folder_item['id']
            else:
                print(f"Error: Folder '{target}' not found.", file=sys.stderr)
                sys.exit(1)

    if args.cmd == "mkdir":
        res = create_folder(service, args.name, parent_id)
        print(json.dumps(res, indent=2))

    elif args.cmd == "csv-append":
        row = json.loads(args.row)
        headers = json.loads(args.headers) if args.headers else None
        res = append_csv_row(service, args.file, row, headers=headers, parent_id=parent_id)
        print(json.dumps(res, indent=2))

    elif args.cmd == "upload":
        p = Path(args.file_path)
        name = args.name or p.name
        existing = find_item(service, name, parent_id=parent_id)
        media = MediaFileUpload(str(p), mimetype='text/csv', resumable=True)
        if existing:
            res = service.files().update(fileId=existing['id'], media_body=media, fields='id, name, webViewLink').execute()
        else:
            body = {'name': name}
            if parent_id:
                body['parents'] = [parent_id]
            res = service.files().create(body=body, media_body=media, fields='id, name, webViewLink').execute()
        print(json.dumps(res, indent=2))

    elif args.cmd == "ls":
        q = "trashed = false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        res = service.files().list(q=q, fields="files(id, name, mimeType, webViewLink, size)").execute()
        print(json.dumps(res.get('files', []), indent=2))

if __name__ == "__main__":
    main()

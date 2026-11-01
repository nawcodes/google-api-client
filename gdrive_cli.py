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
gdrive_cli.py - Full-featured Google Drive Manager CLI.
Handles ANY file type (upload, download, delete, list, mkdir, csv-append).
"""

import sys
import os
import io
import csv
import json
import argparse
import mimetypes
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload, MediaFileUpload

def get_token_paths():
    paths = []
    env_p = os.environ.get("GOOGLE_TOKEN_PATH")
    if env_p:
        paths.append(Path(env_p))
    paths.extend([
        Path("/opt/data/google_token.json"),
        Path.home() / ".config/gdrive/google_token.json",
        Path.home() / ".hermes/google_token.json",
        Path("google_token.json")
    ])
    return paths

def get_service():
    token_file = None
    for p in get_token_paths():
        if p.is_file():
            token_file = p
            break
            
    if not token_file:
        print("Error: Google token not found. Set GOOGLE_TOKEN_PATH or run setup.", file=sys.stderr)
        sys.exit(1)
    
    with open(token_file, 'r', encoding='utf-8') as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(token_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def find_item(service, name_or_id, mime_type=None, parent_id=None):
    # If it looks like a Drive ID (alphanumeric, len >= 25, no space)
    if len(name_or_id) >= 25 and " " not in name_or_id and "." not in name_or_id:
        try:
            return service.files().get(fileId=name_or_id, fields="id, name, mimeType, parents").execute()
        except Exception:
            pass
            
    q = f"name = '{name_or_id}' and trashed = false"
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

def upload_any_file(service, file_path, remote_name=None, parent_id=None):
    p = Path(file_path)
    if not p.exists():
        print(f"Error: Local file '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    name = remote_name or p.name
    # Google Drive accepts literally ANY format. We detect mime for preview, or fallback to octet-stream
    mime = mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
    media = MediaFileUpload(str(p), mimetype=mime, resumable=True)
    
    existing = find_item(service, name, parent_id=parent_id)
    if existing:
        return service.files().update(fileId=existing['id'], media_body=media, fields='id, name, webViewLink, size').execute()
    else:
        body = {'name': name}
        if parent_id:
            body['parents'] = [parent_id]
        return service.files().create(body=body, media_body=media, fields='id, name, webViewLink, size').execute()

def download_file(service, name_or_id, destination=None, parent_id=None):
    item = find_item(service, name_or_id, parent_id=parent_id)
    if not item:
        print(f"Error: File '{name_or_id}' not found.", file=sys.stderr)
        sys.exit(1)
        
    dest_path = Path(destination) if destination else Path(item['name'])
    request = service.files().get_media(fileId=item['id'])
    with open(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
    return {"status": "downloaded", "id": item['id'], "name": item['name'], "path": str(dest_path)}

def delete_item(service, name_or_id, permanent=False, parent_id=None):
    item = find_item(service, name_or_id, parent_id=parent_id)
    if not item:
        print(f"Error: Item '{name_or_id}' not found.", file=sys.stderr)
        sys.exit(1)
        
    if permanent:
        service.files().delete(fileId=item['id']).execute()
        return {"status": "deleted_permanently", "id": item['id'], "name": item['name']}
    else:
        service.files().update(fileId=item['id'], body={'trashed': True}).execute()
        return {"status": "moved_to_trash", "id": item['id'], "name": item['name']}

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
    parser = argparse.ArgumentParser(description="Google Drive Universal Manager CLI")
    sub = parser.add_subparsers(dest="cmd")

    # upload (ANY FILE)
    p_u = sub.add_parser("upload", help="Upload ANY file to Google Drive")
    p_u.add_argument("file_path", help="Local file path")
    p_u.add_argument("--name", help="Remote filename")
    p_u.add_argument("--folder", help="Target folder name or ID")

    # download
    p_d = sub.add_parser("download", help="Download file from Google Drive")
    p_d.add_argument("name_or_id", help="File name or ID")
    p_d.add_argument("--output", help="Local destination path")
    p_d.add_argument("--folder", help="Parent folder name or ID")

    # delete (rm)
    p_r = sub.add_parser("rm", help="Delete file or folder")
    p_r.add_argument("name_or_id", help="File or folder name or ID")
    p_r.add_argument("--permanent", action="store_true", help="Permanently delete instead of moving to trash")
    p_r.add_argument("--folder", help="Parent folder name or ID")

    # mkdir
    p_f = sub.add_parser("mkdir", help="Create folder")
    p_f.add_argument("name", help="Folder name")
    p_f.add_argument("--parent", help="Parent folder name or ID")

    # ls
    p_l = sub.add_parser("ls", help="List files and folders")
    p_l.add_argument("--folder", help="Folder name or ID")

    # csv-append (helper utility)
    p_c = sub.add_parser("csv-append", help="Append row to CSV file")
    p_c.add_argument("file", help="CSV filename")
    p_c.add_argument("--row", required=True, help="JSON list of values, e.g. '[\"a\",\"b\"]'")
    p_c.add_argument("--headers", help="JSON list of headers if creating fresh file")
    p_c.add_argument("--folder", help="Folder name or ID")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    service = get_service()

    parent_id = None
    target_folder = getattr(args, "parent", None) or getattr(args, "folder", None)
    if target_folder:
        if len(target_folder) >= 25 and " " not in target_folder and "." not in target_folder:
            parent_id = target_folder
        else:
            folder_item = find_item(service, target_folder, mime_type='application/vnd.google-apps.folder')
            if folder_item:
                parent_id = folder_item['id']
            else:
                print(f"Error: Folder '{target_folder}' not found.", file=sys.stderr)
                sys.exit(1)

    if args.cmd == "upload":
        res = upload_any_file(service, args.file_path, args.name, parent_id)
        print(json.dumps(res, indent=2))

    elif args.cmd == "download":
        res = download_file(service, args.name_or_id, args.output, parent_id)
        print(json.dumps(res, indent=2))

    elif args.cmd == "rm":
        res = delete_item(service, args.name_or_id, args.permanent, parent_id)
        print(json.dumps(res, indent=2))

    elif args.cmd == "mkdir":
        res = create_folder(service, args.name, parent_id)
        print(json.dumps(res, indent=2))

    elif args.cmd == "ls":
        q = "trashed = false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        res = service.files().list(q=q, fields="files(id, name, mimeType, webViewLink, size)").execute()
        print(json.dumps(res.get('files', []), indent=2))

    elif args.cmd == "csv-append":
        row = json.loads(args.row)
        headers = json.loads(args.headers) if args.headers else None
        res = append_csv_row(service, args.file, row, headers=headers, parent_id=parent_id)
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()

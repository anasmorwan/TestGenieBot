import os
import time
import threading
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account

DB_PATH = "quiz_users.db"

# ⚙️ CONFIG
SERVICE_ACCOUNT_FILE = "credentials.json"
FOLDER_ID = "1iNbwM1kx9sBZKw4ve3PEiZ2W2VZ1JChq"
ADMIN_CHAT_ID = int(os.getenv("ADMIN_ID"))

SCOPES = ['https://www.googleapis.com/auth/drive']


# =========================
# 🔹 Google Drive Client
# =========================
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)


# =========================
# 🔹 Upload Backup
# =========================
def upload_to_drive():
    try:
        service = get_drive_service()

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"quiz_users_{timestamp}.db"

        file_metadata = {
            'name': filename,
            'parents': [FOLDER_ID]
        }

        media = MediaFileUpload(DB_PATH, mimetype='application/octet-stream')

        service.files().create(
            body=file_metadata,
            media_body=media
        ).execute()

        print(f"✅ Uploaded to Drive: {filename}")

    except Exception as e:
        print("❌ Drive upload failed:", e)


# =========================
# 🔹 Download Latest Backup
# =========================
def download_latest_backup():
    try:
        service = get_drive_service()

        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            orderBy="createdTime desc",
            pageSize=1,
            fields="files(id, name)"
        ).execute()

        files = results.get('files', [])
        if not files:
            print("⚠️ No backup found on Drive")
            return

        file_id = files[0]['id']
        file_name = files[0]['name']

        request = service.files().get_media(fileId=file_id)

        with open(DB_PATH, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

        print(f"✅ Downloaded backup: {file_name}")

    except Exception as e:
        print("❌ Download failed:", e)


# =========================
# 🔹 Telegram Backup
# =========================
def backup_to_telegram(bot):
    try:
        with open(DB_PATH, "rb") as f:
            bot.send_document(
                ADMIN_CHAT_ID,
                f,
                caption="📦 DB Backup"
            )
        print("✅ Sent backup to Telegram")

    except Exception as e:
        print("❌ Telegram backup failed:", e)


# =========================
# 🔹 Combined Backup
# =========================
def backup_all(bot):
    upload_to_drive()
    backup_to_telegram(bot)


# =========================
# 🔹 Auto Backup Thread
# =========================
def start_auto_backup(bot, interval=300):
    def loop():
        while True:
            print("🔄 Running auto backup...")
            backup_all(bot)
            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()


# =========================
# 🔹 Restore on Startup
# =========================
def restore_if_needed():
    if not os.path.exists(DB_PATH):
        print("⚠️ No local DB found, restoring...")
        download_latest_backup()
    else:
        print("✅ Local DB exists, skipping restore")

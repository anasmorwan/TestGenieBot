import os
import time
import threading
from datetime import datetime
import json
import base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from storage.sqlite_db import get_connection

DB_PATH = "quiz_users.db"

# ⚙️ CONFIG
SERVICE_ACCOUNT_FILE = get_gdrive_service()
FOLDER_ID = "1iNbwM1kx9sBZKw4ve3PEiZ2W2VZ1JChq"
ADMIN_CHAT_ID = int(os.getenv("ADMIN_ID"))

SCOPES = ['https://www.googleapis.com/auth/drive']



def get_gdrive_service():
    # 1. جلب النص المشفر من متغيرات بيئة ريندر
    encoded_creds = os.environ.get('GDRIVE_CREDENTIALS_BASE64')
    
    if not encoded_creds:
        raise ValueError("خطأ: لم يتم العثور على متغير البيئة GDRIVE_CREDENTIALS_BASE64")

    # 2. فك تشفير Base64 وتحويله إلى نص JSON
    decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
    
    # 3. تحويل نص الـ JSON إلى قاموس (Dictionary) بايثون
    credentials_dict = json.loads(decoded_creds)

    return credentials_dict


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
# 🔹 cleanup_old_backups
# =========================
def cleanup_old_backups(max_files=10):
    try:
        service = get_drive_service()

        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            orderBy="createdTime desc",
            fields="files(id, name)"
        ).execute()

        files = results.get('files', [])

        if len(files) <= max_files:
            return

        old_files = files[max_files:]

        for f in old_files:
            service.files().delete(fileId=f['id']).execute()
            print("🗑️ Deleted:", f['name'])

    except Exception as e:
        print("Cleanup failed:", e)


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
# 🔹 smart_restore
# =========================
def smart_restore():
    try:
        service = get_drive_service()

        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            orderBy="createdTime desc",
            fields="files(id, name)"
        ).execute()

        files = results.get('files', [])

        for f in files[:5]:  # جرب آخر 5 نسخ
            try:
                request = service.files().get_media(fileId=f['id'])

                with open(DB_PATH, 'wb') as file:
                    downloader = MediaIoBaseDownload(file, request)

                    done = False
                    while not done:
                        status, done = downloader.next_chunk()

                print(f"✅ Restored from: {f['name']}")
                return True

            except Exception as e:
                print(f"❌ Failed restore from {f['name']}:", e)

        print("❌ All restore attempts failed")
        return False

    except Exception as e:
        print("Restore error:", e)
        return False


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
# 🔹 safe_backup
# =========================
def safe_backup(bot, retries=3):
    for i in range(retries):
        try:
            backup_manual(bot)
            return True
        except Exception as e:
            print(f"Backup attempt {i+1} failed:", e)
            time.sleep(2)

    print("❌ Backup failed after retries")
    return False


# =========================
# 🔹 Combined Backup
# =========================
def backup_all():
    upload_to_drive()
    

# =========================
# 🔹 Combined Backup
# =========================
def backup_manual(bot):
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
def is_db_valid():
    try:
        conn = get_connection
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master LIMIT 1;")
        conn.close()
        return True
    except:
        return False


# =========================
# 🔹 Restore on Startup
# =========================
def restore_if_needed():
    if not os.path.exists(DB_PATH):
        print("⚠️ No local DB found, restoring...")
        download_latest_backup()
    else:
        print("✅ Local DB exists, skipping restore")

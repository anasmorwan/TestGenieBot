import os
import time
import sqlite3
import threading
from datetime import datetime
import json
import base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from storage.sqlite_db import get_connection




# 1. استخراج البيانات من متغير البيئة وتحويلها لقاموس (Dictionary)
def load_credentials():
    encoded_creds = os.environ.get('GDRIVE_CREDENTIALS_BASE64')
    if not encoded_creds:
        print("❌ Error: GDRIVE_CREDENTIALS_BASE64 not found in environment variables")
        return None
    
    # فك التشفير
    decoded_json = base64.b64decode(encoded_creds).decode('utf-8')
    # تحويل النص إلى قاموس بايثون
    return json.loads(decoded_json)



DB_PATH = "quiz_users.db"

# ⚙️ CONFIG
# 2. إعداد المتغيرات الأساسية
CREDENTIALS_DICT = load_credentials()


FOLDER_ID = "1iNbwM1kx9sBZKw4ve3PEiZ2W2VZ1JChq"
ADMIN_CHAT_ID = int(os.getenv("ADMIN_ID"))

SCOPES = ['https://www.googleapis.com/auth/drive']

# =========================
# 🔹 Google Drive Client
# =========================
# 3. دالة بناء الخدمة (التعديل المهم هنا)
def get_drive_service():
    if not CREDENTIALS_DICT:
        raise Exception("Credentials data is missing!")

    # ✅ التغيير هنا: استخدمنا from_service_account_info
    # لأننا نمرر "قاموس البيانات" مباشرة وليس "مسار ملف"
    creds = service_account.Credentials.from_service_account_info(
        CREDENTIALS_DICT, 
        scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)


# =========================
# 🔹 Upload Backup
# =========================
def upload_to_drive():
    try:
        # تأكد من وجود ملف لرفعه
        if not os.path.exists(DB_PATH):
            print("❌ لا يوجد ملف قاعدة بيانات لرفعه")
            return

        service = get_drive_service()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"quiz_users_{timestamp}.db"

        file_metadata = {'name': filename, 'parents': [FOLDER_ID]}
        
        # نستخدم mimetype المناسب لـ SQLite
        media = MediaFileUpload(DB_PATH, mimetype='application/x-sqlite3', resumable=True)

        service.files().create(body=file_metadata, media_body=media).execute()
        print(f"✅ تم الرفع بنجاح: {filename}")

    except Exception as e:
        print("❌ فشل الرفع إلى Drive:", e)



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
    cleanup_old_backups()
    

# =========================
# 🔹 Combined Backup
# =========================
def backup_manual(bot):
    upload_to_drive()
    backup_to_telegram(bot)
    

# =========================
# 🔹 Auto Backup Thread
# =========================
def start_auto_backup(interval=300):
    def loop():
        while True:
            print("🔄 Running auto backup...")
            backup_all()
            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()



# =========================
# 🔹 is_db_valid
# =========================
def is_db_valid():
    conn = None
    try:
        # تأكد من استدعاء الدالة بـ () إذا كانت get_connection دالة
        conn = get_connection() 
        cursor = conn.cursor()
        
        # نختبر القراءة من جدول داخلي للتأكد أن الملف ليس تالفاً
        cursor.execute("SELECT name FROM sqlite_master LIMIT 1;")
        
        # اختياري: يمكنك التأكد من وجود أحد جداولك الخاصة 
        # cursor.execute("SELECT 1 FROM users LIMIT 1;")
        
        return True
    except sqlite3.Error:
        # فشل في الاتصال أو الملف تالف
        return False
    finally:
        if conn:
            conn.close()


# =========================
# 🔹 Restore on Startup
# =========================
def restore_if_needed():
    # نتحقق: هل الملف غير موجود؟ أو هل حجمه 0 بايت (فارغ)؟ أو هل هو غير صالح؟
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) < 100 or not is_db_valid():
        print("⚠️ قاعدة البيانات مفقودة، فارغة أو تالفة. جاري الاستعادة من Drive...")
        
        # محاولة التحميل
        download_latest_backup()
        
        # إذا فشل التحميل العادي، نجرب الـ smart_restore
        if not is_db_valid():
             smart_restore()
    else:
        print(f"✅ قاعدة البيانات موجودة وصالحة (الحجم: {os.path.getsize(DB_PATH)} بايت)")


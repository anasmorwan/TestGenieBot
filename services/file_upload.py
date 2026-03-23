import os
from bot.bot_instance import mybot

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def is_file_size_allowed(mybot, file_id):
    file_info = mybot.get_file(file_id)
    return file_info.file_size <= MAX_FILE_SIZE

def get_file_extension(file_path):
    """استخراج امتداد الملف من المسار"""
    return os.path.splitext(file_path)[1] if file_path else ""

def handle_file_upload(msg):
    """
    دالة متكاملة لتحميل الملفات والصور
    تعيد: (مسار الملف المحفوظ، اسم الملف)
    """
    uid = msg.from_user.id
    chat_id = msg.chat.id
    
    file_id = None
    file_name = None
    file_type = None
    
    # ✅ تحديد نوع الملف
    if msg.document:
        # ملف مستند
        file_id = msg.document.file_id
        file_name = msg.document.file_name
        file_type = "document"
        
    elif msg.photo:
        # صورة (نأخذ أكبر صورة)
        photo = msg.photo[-1]  # آخر عنصر هو أكبر صورة
        file_id = photo.file_id
        # إنشاء اسم افتراضي للصورة
        file_name = f"photo_{uid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        file_type = "photo"
        
    # elif msg.video:
     #   file_id = msg.video.file_id
    #    file_name = msg.video.file_name or f"video_{uid}.mp4"
     #   file_type = "video"
        
 #   elif msg.audio:
    #    file_id = msg.audio.file_id
 #       file_name = msg.audio.file_name or f"audio_{uid}.mp3"
#        file_type = "audio"
        
    else:
        mybot.send_message(chat_id, "❌ نوع الملف غير مدعوم")
        return None, None
    
    # ✅ التحقق من الحجم
    if not is_file_size_allowed(mybot, file_id):
        mybot.send_message(chat_id, f"⚠️ الملف كبير جداً (الحد الأقصى 5MB)")
        return None, None
    
    # ✅ تحميل الملف
    try:
        file_info = mybot.get_file(file_id)
        file_data = mybot.download_file(file_info.file_path)
        
    except Exception as e:
        print(f"Download error: {e}")
        mybot.send_message(chat_id, "❌ لم أستطع قراءة الملف")
        return None, None
    
    # ✅ حفظ الملف
    path = save_file(uid, file_name, file_data, file_type)
    
    mybot.send_message(chat_id, f"✅ تم رفع {file_type}: {file_name}")
    
    return path, file_name

def save_file(uid, file_name, file_data, file_type="document"):
    """حفظ الملف مع تنظيم حسب النوع"""
    # إنشاء مجلد حسب نوع الملف
    folder = os.path.join("downloads", file_type)
    os.makedirs(folder, exist_ok=True)
    
    # تنظيف اسم الملف من الأحرف غير المسموحة
    safe_name = "".join(c for c in file_name if c.isalnum() or c in "._-")
    path = os.path.join(folder, f"{uid}_{safe_name}")
    
    with open(path, "wb") as f:
        f.write(file_data)
    
    return path

import os
from bot.bot_instance import mybot
from datetime import datetime
from services.usage import is_paid_user_active

def get_max_file_size(user_id):
    if not is_paid_user_active(user_id): 
        max_file_size = 5 * 1024 * 1024  # 5 MB
    else:
        max_file_size = 12 * 1024 * 1024
    return max_file_size

def is_file_size_allowed(mybot, user_id, file_id):
    file_info = mybot.get_file(file_id)
    max_size = get_max_file_size(user_id)
    
    return file_info.file_size <= max_size
    
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
        
    else:
        mybot.send_message(chat_id, "❌ نوع الملف غير مدعوم")
        return None, None
    
    # ✅ التحقق من الحجم
    if not is_file_size_allowed(mybot, uid, file_id):
        if is_paid_user_active(uid):
            return "large_file", 12
        return "large_file", 5
        
        
    
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

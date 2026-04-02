# storage/quiz_repository.py

import json
import time
import uuid
from datetime import datetime, timedelta
from storage.sqlite_db import get_connection
from services.usage import is_paid_user_active
import threading
import time

#----------------------------
#  🔹 توليد و حفظ ال QC
#----------------------------
def generate_quiz_code():

    return "QC_" + uuid.uuid4().hex[:6]


def store_quiz(user_id, quizzes):

    conn = get_connection()
    c = conn.cursor()

    code = generate_quiz_code()
    is_paid = 1 if is_paid_user_active(user_id) else 0


    c.execute("""
    INSERT INTO user_quizzes
    (user_id, quiz_data, quiz_code, created_at, is_paid)
    VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        json.dumps(quizzes),
        code,
        datetime.now().isoformat(),
        is_paid
    ))
    
    print("🗑 old quizzes deleated", flush=True)

    conn.commit()
    conn.close()

    return code

def store_content(user_id, content_data, content_type):
    conn = get_connection()
    c = conn.cursor()

    code = generate_quiz_code()
    is_paid = 1 if is_paid_user_active(user_id) else 0

    c.execute("""
    INSERT INTO user_quizzes 
    (user_id, quiz_data, quiz_code, quiz_type, created_at, is_paid) 
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id, 
        json.dumps(content_data), 
        code, 
        content_type, # هنا نحدد هل هو poll أم quiz
        datetime.now().isoformat(), 
        is_paid
    ))
    
    conn.commit()
    conn.close()
    return code
    
#----------------------------
#  🔹 cleanup old quizzes
#----------------------------
def cleanup_old_quizzes():
    conn = get_connection()
    cursor = conn.cursor()
    expiry_time = datetime.utcnow() - timedelta(hours=48)

    cursor.execute("""
    DELETE FROM user_quizzes
    WHERE is_paid = 0
    AND datetime(created_at) < datetime(?)
    """, (expiry_time.isoformat(),))

    conn.commit()

def maybe_cleanup():
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.utcnow()

    cursor.execute("""
    DELETE FROM user_quizzes
    WHERE is_paid = 0
    AND datetime(created_at) < datetime('now', '-48 hours')
    """)
    conn.commit()
#----------------------------
#  🔹 Quiz share log
#----------------------------
def log_quiz_share(quiz_code, shared_by_user_id, shared_by_name):
    conn = get_connection()
    c = conn.cursor()

    shared_at = datetime.now().isoformat()  

    c.execute("""  
        INSERT INTO quiz_shares (quiz_code, shared_by_user_id, shared_by_name, shared_at)  
        VALUES (?, ?, ?, ?)  
    """, (quiz_code, shared_by_user_id, shared_by_name, shared_at))  

    conn.commit()  
    conn.close()





#----------------------------
#  🔹 تحديث و إسترجاع ال QC
#----------------------------
def update_user_current_quiz(user_id, quiz_code):
    """
    تحديث الكويز الذي يتفاعل معه المستخدم حالياً (الذاكرة المؤقتة).
    """
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE users SET current_quiz_selection = ? WHERE user_id = ?",
            (quiz_code, user_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error updating current quiz: {e}")
        return False

def get_user_current_quiz(user_id):
    """
    استرجاع الكود الذي اختاره المستخدم آخر مرة.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT current_quiz_selection FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "sample_quiz"



#----------------------------
#  🔹 إرسال الاختبارات إلى الشات
#----------------------------
def send_quiz_to_chat(bot, chat_id, quiz_code, is_pro=False):
    """
    تسترجع الاختبار من القاعدة وترسله كـ Polls متتالية إلى الدردشة المستهدفة.
    """
    conn = get_connection()
    c = conn.cursor()
    
    # 1. جلب بيانات الاختبار باستخدام الكود الفريد
    c.execute("SELECT quiz_data FROM user_quizzes WHERE quiz_code = ?", (quiz_code,))
    row = c.fetchone()
    conn.close()

    if not row:
        print(f"❌ الاختبار {quiz_code} غير موجود في القاعدة.")
        return False

    try:
        # 2. تحويل النص المخزن (JSON) إلى قائمة بايثون
        quizzes = json.loads(row[0]) 

        for item in quizzes:
            question = item.get('question', 'سؤال بدون عنوان')
            options = item.get('options', [])
            correct_id = item.get('correct_option_index', 0)
            explanation = item.get('explanation', '')

            # 3. إرسال السؤال بنمط الاختبار (Quiz Mode)
            bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=options,
                type='quiz',
                correct_option_id=correct_id,
                is_anonymous=True, # يسمح لصاحب القناة برؤية من أجاب (اختياري)
                explanation=explanation if is_pro else "تم التوليد بواسطة @TestGenieBot",
                explanation_parse_mode="Markdown"
            )
            
            # 4. تأخير بسيط لتجنب الـ Flood (حظر تيليجرام للإرسال السريع)
            time.sleep(0.5) 

        return True

    except Exception as e:
        print(f"❌ خطأ أثناء إرسال الكويز {quiz_code}: {e}")
        return False




def is_quiz_expired(quiz_code):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT created_at, is_paid
    FROM user_quizzes
    WHERE quiz_code = ? AND is_active = 1
    """, (quiz_code,))
    
    row = cursor.fetchone()
    
    if not row:
        return True  # غير موجود = منتهي
    
    created_at, is_paid = row
    
    # المدفوعين لا ينتهي
    if is_paid:
        return False
    
    created_time = datetime.fromisoformat(created_at)
    
    # مدة الصلاحية (مثلاً 48 ساعة)
    if datetime.utcnow() - created_time > timedelta(hours=48):
        return True
    
    return False


"""
def run_cleanup():
    while True:
        cleanup_old_quizzes()
        time.sleep(3600)  # كل ساعة

threading.Thread(target=run_cleanup, daemon=True).start()

"""

import random
from storage.sqlite_db import get_connection,
from datetime import timedelta, datetime, date
from storage.session_store import user_streak




def get_or_create_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users_trap WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()
        return get_or_create_user(user_id)

    return user

def is_new_day(last_date):
    if not last_date:
        return True
    return last_date != str(date.today())


def should_show_daily(user):
    last_quiz_date = user_streak.get(user)  # حسب ترتيب الجدول
    return is_new_day(last_quiz_date)




def is_yesterday(date_str):
    if not date_str:
        return False
    last = datetime.strptime(date_str, "%Y-%m-%d").date()
    return last == date.today() - timedelta(days=1)


def update_progress(user_id, correct=None, total=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT streak, last_quiz_date, xp FROM users_trap WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    
    if result is None:
        return None  # المستخدم غير موجود
    
    streak, last_date, xp = result
    today = str(date.today())
    
    # تحديث الـ streak فقط إذا أردت (يعني عند أداء اختبار)
    if correct is not None:
        # streak logic
        if last_date == today:
            pass
        elif is_yesterday(last_date):
            streak += 1
        else:
            streak = 1
        
        # xp logic
        gained_xp = correct * 10
        xp += gained_xp
        
        cursor.execute("""
            UPDATE users_trap
            SET streak=?, last_quiz_date=?, xp=?
            WHERE user_id=?
        """, (streak, today, xp, user_id))
        
        conn.commit()
        return streak, gained_xp
    else:
        # فقط جلب البيانات بدون تحديث
        return streak, xp


def save_quiz(user_id, correct, total, quiz_type="daily"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_history (user_id, correct_answers, total_questions, quiz_type)
        VALUES (?, ?, ?, ?)
    """, (user_id, correct, total, quiz_type))

    conn.commit()




# ---------------------------
#   🔹  helping functions.  
# ---------------------------

def get_feedback_line(score, total):
    """رسالة ذكية بناءً على أداء المستخدم في الاختبار الحالي"""

    if total == 0:
        return ""

    ratio = score / total

    if ratio == 1:
        return "🏆 أداء مثالي! واضح أنك مسيطر على هذا الجزء بالكامل"
    
    elif ratio >= 0.8:
        return "💪 أداء قوي جداً! أنت قريب من الإتقان الكامل"
    
    elif ratio >= 0.6:
        return "👍 جيد! فهمك واضح، فقط بعض التفاصيل تحتاج تركيز"
    
    elif ratio >= 0.4:
        return "🧠 بداية جيدة… أنت على الطريق الصحيح، استمر"
    
    else:
        return "📚 لا بأس… هذا يعني أنك تتعلم الآن، ركّز وستتحسن بسرعة"


def get_weakness_line(user_id, wrong_count):
    """رسالة تركز على نقاط الضعف الحالية + دعم من قاعدة البيانات"""

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*), 
               COUNT(CASE WHEN fail_count >= 2 THEN 1 END)
        FROM user_mistakes
        WHERE user_id = ?
    """, (user_id,))

    row = c.fetchone()
    conn.close()

    total_mistakes = row[0] or 0
    repeated = row[1] or 0

    # 🔥 لا توجد أخطاء حالية
    if wrong_count == 0:
        return "🔥 ممتاز! لا توجد أخطاء في هذا التحدي"

    # 🟢 أخطاء قليلة
    if wrong_count <= 2:
        return "🎯 أخطاء بسيطة… يمكنك تجاوزها بسهولة في المحاولة القادمة"

    # 🟡 متوسط
    if wrong_count <= 4:
        return "📌 بعض النقاط تحتاج مراجعة، ركّز عليها وستتحسن سريعاً"

    # 🔴 أداء ضعيف + تاريخ أخطاء
    if repeated >= 3:
        return "⚠️ لاحظنا تكرار نفس الأخطاء… راجعها الآن وستحدث فرق كبير"

    return "🔁 هذا التحدي كشف نقاط تحتاج عمل… وهذا أفضل وقت للتحسن"



def get_detailed_weakness(user_id, limit=1):
    """عرض ذكي لأهم نقاط الضعف بدون إزعاج"""

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT question_text, fail_count
        FROM user_mistakes 
        WHERE user_id = ?
        ORDER BY fail_count DESC, last_failed DESC
        LIMIT ?
    """, (user_id, limit))

    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    lines = []
    for i, (q_text, fail_count) in enumerate(rows, 1):
        short_q = q_text[:50] + "..." if len(q_text) > 50 else q_text
        lines.append(f"• نقطة تحتاج تركيز ({fail_count}×)")

    return "\n".join(lines)

def build_result_message(user_id, score, total, streak, xp):
    feedback = get_feedback_line(score, total)
    weakness = get_weakness_line(user_id, total - score)
    details = get_detailed_weakness(user_id)

    text = f"""
🎯 النتيجة: {score}/{total}

{feedback}

🔥 سلسلة: {streak} يوم  
⚡ +{xp} XP

{weakness}
"""

    if details:
        text += f"\n💡 ركّز على:\n{details}"

    text += "\n\n👇 لا تفقد تقدمك:"

    return text.strip()






def get_dynamic_level(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT difficulty FROM users WHERE user_id=?", (user_id,))
    user_level = cursor.fetchone()
    if not user_level:
        user_level = "mid"

    
    levels = ["easy", "medium", "hard"]

    if user_level == "early":
        return random.choices(levels, weights=[0.7, 0.2, 0.1])[0]

    elif user_level == "mid":
        return random.choices(levels, weights=[0.2, 0.6, 0.2])[0]

    else:
        return random.choices(levels, weights=[0.1, 0.3, 0.6])[0]

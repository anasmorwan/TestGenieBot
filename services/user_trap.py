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

def get_feedback_line(user_id):
    """ترجع رسالة تقييم أداء المستخدم بناءً على الأخطاء"""
    conn = get_connection()
    c = conn.cursor()
    
    # الحصول على إحصائيات الأخطاء
    c.execute("""
        SELECT 
            COUNT(*) as total_mistakes,
            SUM(fail_count) as total_fails,
            AVG(fail_count) as avg_fails,
            COUNT(CASE WHEN fail_count >= 2 THEN 1 END) as repeated_mistakes
        FROM user_mistakes 
        WHERE user_id = ?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()
    
    total_mistakes = row[0] or 0
    total_fails = row[1] or 0
    avg_fails = row[2] or 0
    repeated_mistakes = row[3] or 0
    
    # لا توجد أخطاء → أداء ممتاز
    if total_mistakes == 0:
        return "🏆 ممتاز! أداءك قوي جداً، استمر بهذا المستوى!"
    
    # نسبة التكرار (كم مرة تكرر نفس الخطأ)
    repetition_rate = repeated_mistakes / total_mistakes if total_mistakes > 0 else 0
    
    # تحليل الأداء
    if total_mistakes <= 3 and avg_fails <= 1.2:
        return "💪 أداء قوي! واضح أنك فاهم المادة، فقط بعض التفاصيل الصغيرة تحتاج تركيز"
    
    elif total_mistakes <= 7 and repetition_rate < 0.3:
        return "👍 جيد جداً! لديك فهم جيد، لكن仍有 مجال للتحسن في بعض النقاط"
    
    elif repetition_rate > 0.5:
        return "🧠 لا بأس… هذا يعني أنك تتعلم الآن. الأخطاء المتكررة هي فرصة لتثبيت المعلومة!"
    
    elif total_mistakes > 10:
        return "📚 لا تيأس! كل خطأ يقرّبك من الإتقان. ركّز على فهم الأساسيات أولاً"
    
    else:
        return "🎯 أنت على الطريق الصحيح! مع التدريب المستمر، ستتحسن النتائج بشكل ملحوظ"



def get_weakness_line(user_id):
    """ترجع رسالة عن نقاط الضعف بناءً على الأخطاء"""
    conn = get_connection()
    c = conn.cursor()
    
    # إحصائيات عامة
    c.execute("""
        SELECT 
            COUNT(*) as total_mistakes,
            COUNT(CASE WHEN fail_count >= 2 THEN 1 END) as repeated_mistakes,
            MAX(fail_count) as max_fail
        FROM user_mistakes 
        WHERE user_id = ?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()
    
    total_mistakes = row[0] or 0
    repeated_mistakes = row[1] or 0
    max_fail = row[2] or 0
    
    # لا توجد أخطاء
    if total_mistakes == 0:
        return "🔥 رائع! لا توجد نقاط ضعف واضحة، أنت مبدع!"
    
    # حالات مختلفة
    if repeated_mistakes >= 5:
        return f"⚠️ لاحظنا أنك تكرر الخطأ في {repeated_mistakes} أسئلة. هذه فرصة ذهبية للتعلم!"
    
    elif max_fail >= 3:
        return f"🔁 تركيز مطلوب! لديك {max_fail} أسئلة تكرر خطؤها أكثر من مرة، راجعها جيداً"
    
    elif total_mistakes <= 3:
        return f"🎯 نقاط قليلة فقط! ركّز على {total_mistakes} نقطة وسوف تتقن المادة"
    
    elif total_mistakes <= 7:
        return f"📌 لديك {total_mistakes} نقطة تحتاج مراجعة، أنت قريب جداً من الإتقان!"
    
    elif total_mistakes <= 12:
        return f"🔁 ركّز على هذا: لديك {total_mistakes} نقاط تحتاج مراجعة. خصص وقتاً لها"
    
    else:
        return f"📚 لا تقلق! {total_mistakes} نقطة ضعف تعني أن أمامك مجال كبير للنمو والتطور"



def get_detailed_weakness(user_id, limit=3):
    """ترجع أكثر 3 أسئلة يحتاج المستخدم التركيز عليها"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT question_text, fail_count, last_failed
        FROM user_mistakes 
        WHERE user_id = ?
        ORDER BY fail_count DESC, last_failed DESC
        LIMIT ?
    """, (user_id, limit))
    
    weak_questions = c.fetchall()
    conn.close()
    
    if not weak_questions:
        return None
    
    lines = []
    for i, (q_text, fail_count, last_failed) in enumerate(weak_questions, 1):
        short_q = q_text[:60] + "..." if len(q_text) > 60 else q_text
        lines.append(f"{i}. {short_q} (أخطأت فيها {fail_count} مرة)")
    
    return "\n".join(lines)




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

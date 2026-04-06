import random
from storage.sqlite_db import get_connection
from datetime import timedelta, datetime, date
from storage.session_store import user_streak
from services.usage import is_paid_user_active
from storage.session_store import last_active

from datetime import datetime


def send_daily_challenge(bot, user_id, new_count, challenge_count):
    content = get_user_content(user_id)
    
    if challenge_count and new_count > 0:
        is_pro = is_paid_user_active(user_id)
        
        num_quizzes = challenge_count + new_count
        extended_quizzes = generate_challenge_quiz(content, num_quizzes, is_pro)
        
        return extended_quizzes  # ✅ ترجع القائمة، وليس العدد
    
    return []  # ✅ إرجاع قائمة فارغة إذا لم تكن الشروط مستوفاة



def update_last_active(user_id):
    last_active[user_id] = datetime.now()


def get_user_content(user_id):
    """
    استرجاع محتوى المستخدم من قاعدة البيانات
    للمستخدم المدفوع: دمج 3 نصوص بنسب محددة
    للمستخدم العادي: إرجاع آخر نص فقط
    """
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # التحقق من حالة المستخدم أولاً
        if not is_paid_user_active(user_id):
            # مستخدم عادي: جلب آخر نص فقط باستخدام LIMIT 1
            c.execute("""
                SELECT last_text, specialty 
                FROM user_knowledge 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (user_id,))
            
            record = c.fetchone()
            if not record:
                return None
            
            last_text = record[0]
            specialty = record[1]
            
            # اقتصاص إلى 2000 حرف إذا كان أطول
            if len(last_text) > 2000:
                last_text = last_text[:2000]
            
            return f"【آخر نص محفوظ - {specialty}】\n{last_text}"
        
        else:
            # مستخدم مدفوع: جلب جميع النصوص للدمج
            c.execute("""
                SELECT last_text, specialty, updated_at 
                FROM user_knowledge 
                WHERE user_id = ? 
                ORDER BY updated_at DESC
            """, (user_id,))
            
            records = c.fetchall()
            
            if not records:
                return None
            
            if len(records) == 1:
                # إذا كان عنده نص واحد فقط
                return f"【النص الوحيد】\n{records[0][0]}"
            
            elif len(records) == 2:
                # إذا كان عنده نصين فقط
                latest_text = records[0][0]
                oldest_text = records[1][0]
                
                # توزيع 60% - 40%
                latest_len = int(2000 * 0.6)
                oldest_len = 2000 - latest_len
                
                truncated_latest = latest_text[:latest_len]
                truncated_oldest = oldest_text[:oldest_len]
                
                return f"""【النص الأحدث (60%)】
{truncated_latest}

【النص الأقدم (40%)】
{truncated_oldest}"""
            
            else:
                # 3 نصوص أو أكثر
                latest_text = records[0][0]      # أحدث نص
                oldest_text = records[-1][0]     # أقدم نص
                
                # النصوص المتوسطة (ما عدا الأحدث والأقدم)
                middle_records = records[1:-1]
                
                # اختيار نص عشوائي من النصوص المتوسطة
                random_record = random.choice(middle_records)
                random_text = random_record[0]
                
                # حساب الطول لكل جزء (حد أقصى 2000 حرف)
                max_total = 2000
                latest_percent = 0.6
                oldest_percent = 0.2
                random_percent = 0.2
                
                latest_len = int(max_total * latest_percent)
                oldest_len = int(max_total * oldest_percent)
                random_len = max_total - latest_len - oldest_len
                
                # اقتصاص النصوص
                truncated_latest = latest_text[:latest_len]
                truncated_oldest = oldest_text[:oldest_len]
                truncated_random = random_text[:random_len]
                
                specialty_latest = records[0][1]
                specialty_oldest = records[-1][1]
                specialty_random = random_record[1]
                
                return f"""【النص الأحدث - {specialty_latest} (60%)】
{truncated_latest}

【النص الأقدم - {specialty_oldest} (20%)】
{truncated_oldest}

【نص عشوائي - {specialty_random} (20%)】
{truncated_random}"""
    
    except Exception as e:
        print(f"❌ Error in get_user_content: {e}")
        return None
    finally:
        conn.close()

    

def save_user_knowledge(user_id, last_text, specialty):
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # تنظيف المدخلات (حل مشكلة الـ tuple التي واجهتها سابقاً)
        if isinstance(last_text, (tuple, list)): last_text = last_text[0]
        if isinstance(specialty, (tuple, list)): specialty = specialty[0]

        if is_paid_user_active(user_id):
            # 1. إدراج النص الجديد (مسموح بالتكرار هنا لأننا حذفنا الـ Unique Index)
            c.execute("""
                INSERT INTO user_knowledge (user_id, last_text, specialty, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, last_text, specialty))
            
            # 2. فحص العدد للحذف الزائد (كودك الحالي سليم)
            c.execute("SELECT COUNT(*) FROM user_knowledge WHERE user_id = ?", (user_id,))
            count = c.fetchone()[0]
            
            if count > 10:
                c.execute("""
                    DELETE FROM user_knowledge WHERE id IN (
                        SELECT id FROM user_knowledge 
                        WHERE user_id = ? 
                        ORDER BY updated_at ASC 
                        LIMIT ?
                    )
                """, (user_id, count - 10))
        
        else:
            # للمستخدم العادي: نريد دائماً صفاً واحداً فقط
            c.execute("SELECT id FROM user_knowledge WHERE user_id = ?", (user_id,))
            existing = c.fetchone()
            
            if existing:
                c.execute("""
                    UPDATE user_knowledge 
                    SET last_text = ?, specialty = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (last_text, specialty, user_id))
            else:
                c.execute("""
                    INSERT INTO user_knowledge (user_id, last_text, specialty, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, last_text, specialty))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
        

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

from datetime import datetime, timedelta

def is_inactive(user_id, hours=24):
    last = last_active.get(user_id)
    if not last:
        return True
    return datetime.now() - last > timedelta(hours=hours)

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

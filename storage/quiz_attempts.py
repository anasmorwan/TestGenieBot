from datetime import datetime
from storage.sqlite_db import get_connection




#--------------------------
#     تسجيل بداية الاختبار
#-----------------------------
def log_quiz_start(user_id, quiz_code):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT OR IGNORE INTO quiz_attempts 
        (quiz_code, user_id, score, total, timestamp)
        VALUES (?, ?, NULL, NULL, ?)
    """, (
        quiz_code,
        user_id,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

#--------------------------
#    جلب صانع الاختبار    
#-----------------------------
def get_quiz_creator(quiz_code):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT user_id 
        FROM user_quizzes
        WHERE quiz_code=?
    """, (quiz_code,))

    row = c.fetchone()
    conn.close()

    return row[0] if row else None


#--------------------------
#      تحليل الاداء للسمتخدمين    
#-----------------------------
def get_quiz_stats(quiz_code):
    conn = get_connection()
    c = conn.cursor()

    # عدد المحاولات
    c.execute("""
        SELECT COUNT(*) FROM quiz_attempts WHERE quiz_code=?
    """, (quiz_code,))
    attempts = c.fetchone()[0]

    # عدد المستخدمين الفريدين
    c.execute("""
        SELECT COUNT(DISTINCT user_id) FROM quiz_attempts WHERE quiz_code=?
    """, (quiz_code,))
    users = c.fetchone()[0]

    # عدد المكتملين (score != NULL)
    c.execute("""
        SELECT COUNT(*) FROM quiz_attempts 
        WHERE quiz_code=? AND score IS NOT NULL
    """, (quiz_code,))
    completed = c.fetchone()[0]

    conn.close()

    return {
        "attempts": attempts,
        "users": users,
        "completed": completed
    }


#--------------------------
#    تسجيل كل محاولة 
#-----------------------------
def log_quiz_attempt(user_id, quiz_code, score, total):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO quiz_attempts (quiz_code, user_id, score, total, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        quiz_code,
        user_id,
        score,
        total,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


#--------------------------
#      أفضل المستخدمين (Leaderboard)    
#-----------------------------
def get_top_users(quiz_code, limit=5):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT user_id, score 
        FROM quiz_attempts
        WHERE quiz_code=?
        ORDER BY score DESC
        LIMIT ?
    """, (quiz_code, limit))

    rows = c.fetchall()
    conn.close()

    return rows

#--------------------------
#    جلب اسماء المستخدمين    
#---------------------------
def get_quiz_user_ids(quiz_code):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT DISTINCT user_id 
        FROM quiz_attempts
        WHERE quiz_code=?
    """, (quiz_code,))

    rows = c.fetchall()
    conn.close()

    return [r[0] for r in rows]
    
#--------------------------
#      . أسماء المستخدمين (اختياري)    
#---------------------------
def format_usernames(bot, user_ids):
    names = []
    for uid in user_ids:
        try:
            user = bot.get_chat(uid)
            names.append(user.first_name)
        except:
            continue
    return names


#--------------------------
#      رسالة Upsell الذكية
#--------------------------
def build_quiz_viral_message(stats, names):
    sample_names = "\n".join([f"- {n}" for n in names[:3]])

    return f"""
🔥 اختبارك بدأ ينتشر!

👥 {stats['users']} شخصاً جربوه  
📊 {stats['completed']} أكملوه

👀 بعض الأسماء:
{sample_names}

━━━━━━━━━━━━━━━
🔓 افتح الإحصائيات الكاملة وتحليل الأداء مع TestGenie Pro
"""

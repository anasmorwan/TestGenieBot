from datetime import datetime
from storage.sqlite_db import get_connection


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


def log_question_attempt(user_id, quiz_code, question_index, selected, correct):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO question_attempts 
        (quiz_code, user_id, question_index, selected_option, correct_option, is_correct, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        quiz_code,
        user_id,
        question_index,
        selected,
        correct,
        int(selected == correct),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_hardest_question(quiz_code):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT 
            question_index,
            SUM(is_correct) as correct,
            COUNT(*) as total
        FROM question_attempts
        WHERE quiz_code=?
        GROUP BY question_index
        ORDER BY (CAST(correct AS FLOAT) / total) ASC
        LIMIT 1
    """, (quiz_code,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    q_index, correct, total = row
    accuracy = correct / total if total else 0

    return {
        "question_index": q_index,
        "accuracy": round(accuracy * 100, 1),
        "wrong_rate": round((1 - accuracy) * 100, 1)
    }


def get_success_rate(quiz_code):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT AVG(CAST(score AS FLOAT) / total)
        FROM quiz_attempts
        WHERE quiz_code=? AND score IS NOT NULL
    """, (quiz_code,))

    result = c.fetchone()[0]
    conn.close()

    if not result:
        return 0

    return round(result * 100, 1)



def build_advanced_stats_message(stats, hardest, success):
    return f"""
🔥 اختبارك بدأ يتحول إلى تجربة حقيقية!

👥 {stats['users']} مستخدمين جربوه  
📊 {stats['completed']} أكملوه  

━━━━━━━━━━━━━━━
📉 تحليل ذكي:

😮 السؤال الأصعب: رقم {hardest['question_index'] + 1}  
❌ نسبة الخطأ: {hardest['wrong_rate']}%

📈 متوسط النجاح: {success}%

━━━━━━━━━━━━━━━
🔓 افتح تحليل كامل + معرفة من أخطأ في ماذا مع TestGenie Pro
"""

import random
from storage.sqlite_db import get_connection
from datetime import timedelta, datetime, date





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
    last_quiz_date = user[4]  # حسب ترتيب الجدول
    return is_new_day(last_quiz_date)




def is_yesterday(date_str):
    if not date_str:
        return False
    last = datetime.strptime(date_str, "%Y-%m-%d").date()
    return last == date.today() - timedelta(days=1)


def update_progress(user_id, correct, total):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT streak, last_quiz_date, xp FROM users_trap WHERE user_id=?", (user_id,))
    streak, last_date, xp = cursor.fetchone()

    today = str(date.today())

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

if should_show_daily(user):
    send("🔥 تحدي اليوم جاهز!")

streak, xp = update_progress(...)
send(f"🔥 streak: {streak} | +{xp} XP")




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

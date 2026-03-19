from storage.sqlite_db import get_connection



"""
def consume_quiz(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE users 
        SET free_quizzes = free_quizzes - 1 
        WHERE user_id=? AND free_quizzes > 0
    """, (user_id,))

    conn.commit()
    conn.close()
"""

def consume_quiz(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET used_today = used_today + 1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()
    conn.close()


"""
def can_generate(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT free_quizzes FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    conn.close()

    if not row:
        return False

    return row[0] > 0
"""
def can_generate(user_id):
    sub = get_subscription(user_id)

    reset_daily_if_needed(user_id)

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT used_today FROM users WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()

    if not row:
        return False, "no_user"

    used_today = row[0]
    limit = sub.get("daily_quiz_limit", 3)

    if used_today < limit:
        return True, {
            "remaining": limit - used_today,
            "limit": limit
        }

    return False, {
        "remaining": 0,
        "limit": limit
    }



from datetime import datetime

def reset_daily_if_needed(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT last_reset FROM users WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()

    today = datetime.utcnow().date()

    if row and row[0]:
        last = datetime.fromisoformat(row[0]).date()
        if last == today:
            conn.close()
            return

    # 👇 reset
    c.execute("""
        UPDATE users
        SET used_today = 0,
            last_reset = ?
        WHERE user_id=?
    """, (datetime.utcnow().isoformat(), user_id))

    conn.commit()
    conn.close()




def get_remaining(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT daily_limit, used_today FROM users WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()

    if not row:
        return 0

    return max(0, row[0] - row[1])

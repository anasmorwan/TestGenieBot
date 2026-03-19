from storage.sqlite_db import get_connection

def get_subscription(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT plan, expires_at, daily_quiz_limit 
    FROM subscriptions 
    WHERE user_id=?
""", (user_id,))
    
    row = c.fetchone()
    conn.close()

    if not row:
        return {"plan": "free", "expires_at": None, "daily_quiz_limit": 3}

    return {
    "plan": row[0],
    "expires_at": row[1],
    "daily_quiz_limit": row[2]
    }

# def consume_quiz(user_id):
#    conn = get_connection()
#    c = conn.cursor()

#    c.execute("""
#        UPDATE users 
#        SET free_quizzes = free_quizzes - 1 
#        WHERE user_id=? AND free_quizzes > 0
#    """, (user_id,))

#    conn.commit()
#    conn.close()


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



# def can_generate(user_id):
 #   conn = get_connection()
#    c = conn.cursor()
#
#    c.execute("SELECT free_quizzes FROM users WHERE user_id=?", (user_id,))
#    row = c.fetchone()

#    conn.close()

#    if not row:
#        return False

#    return row[0] > 0

def can_generate(user_id):
    sub = get_subscription(user_id)

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT used_today FROM users WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()

    # ✅ إذا مستخدم جديد → أنشئه
    if not row:
        used_today = add_new_user(user_id)
    else:
        used_today = row[0]

    conn.close()

    # 👇 بعد التأكد من وجود المستخدم
    reset_daily_if_needed(user_id)

    # 👇 تحديد الحد
    limit = get_daily_limit(user_id)

    if used_today < limit:
        return True, {
            "remaining": limit - used_today,
            "limit": limit
        }

    return False, {
        "remaining": 0,
        "limit": limit,
        "reason": "limit_reached"
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



def add_new_user(uid):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    INSERT INTO users (user_id, used_today, last_reset)
    VALUES (?, 0, ?)
    """, (user_id, datetime.utcnow().isoformat()))
    conn.commit()
    used_today = 0

    return used_today


def get_daily_limit(user_id):
    sub = get_subscription(user_id)

    plan = sub["plan"]

    if plan == "pro+":
        return 50
    elif plan == "pro":
        return 25
    else:
        return 3

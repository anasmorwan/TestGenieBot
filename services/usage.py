from storage.sqlite_db import get_connection
from datetime import datetime, timedelta




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



def add_new_user(user_id):
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






def get_usage(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT used_today FROM users WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()

    return row[0] if row else 0

def build_status_message(data):
    plan = data["plan"]
    used = data["used"]
    limit = data["limit"]
    remaining = limit - used

    if plan == "free":
        return f"""
📊 <b>حالة حسابك</b>

🆓 الخطة: Free  
⚡ المتبقي اليوم: <b>{remaining}/{limit}</b>

🎁 الدعوات: {data['referrals']}

━━━━━━━━━━━━━━━
🚀 تريد استخدام أكثر بدون قيود؟

✨ Pro: 25 اختبار يومياً  
🔥 Pro+: 50 اختبار يومياً  

أو ادعُ أصدقاءك واحصل على محاولات إضافية مجاناً 👇
"""

    else:
        return f"""
📊 <b>حالة اشتراكك</b>

💎 الخطة: {plan.upper()}  
⚡ المتبقي اليوم: <b>{remaining}/{limit}</b>  
⏳ ينتهي في: {data['expires_at'] or "غير محدد"}

━━━━━━━━━━━━━━━
🔥 استمر! أنت تستخدم البوت بكفاءة
"""



def get_subscription_full(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT plan, expires_at, daily_quiz_limit, daily_ocr_limit
    FROM subscriptions
    WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()

    if not row:
        return {
            "plan": "free",
            "expires_at": None,
            "daily_quiz_limit": 3,
            "daily_ocr_limit": 1
        }

    return {
        "plan": row[0],
        "expires_at": row[1],
        "daily_quiz_limit": row[2],
        "daily_ocr_limit": row[3]
    }


#--------------------------
#       ترقية المستخدمين      
#----------------------------


def get_plan_limits(plan):
    if plan == "pro":
        return {
            "quiz_limit": 25,
            "ocr_limit": 3,
            "days": 30
        }
    elif plan == "pro_plus":
        return {
            "quiz_limit": 50,
            "ocr_limit": 5,
            "days": 30
        }
    else:
        return {
            "quiz_limit": 3,
            "ocr_limit": 1,
            "days": 0
    }




def activate_subscription(user_id, plan):
    conn = get_connection()
    c = conn.cursor()

    limits = get_plan_limits(plan)

    expires_at = None
    if limits["days"] > 0:
        expires_at = (datetime.utcnow() + timedelta(days=limits["days"])).isoformat()

    # هل المستخدم لديه اشتراك سابق؟
    c.execute("SELECT id FROM subscriptions WHERE user_id=?", (user_id,))
    exists = c.fetchone()

    if exists:
        # تحديث
        c.execute("""
            UPDATE subscriptions
            SET plan=?,
                expires_at=?,
                daily_quiz_limit=?,
                daily_ocr_limit=?,
                updated_at=?
            WHERE user_id=?
        """, (
            plan,
            expires_at,
            limits["quiz_limit"],
            limits["ocr_limit"],
            datetime.utcnow().isoformat(),
            user_id
        ))
    else:
        # إدخال جديد
        c.execute("""
            INSERT INTO subscriptions 
            (user_id, plan, expires_at, daily_quiz_limit, daily_ocr_limit)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            plan,
            expires_at,
            limits["quiz_limit"],
            limits["ocr_limit"]
        ))

    conn.commit()
    conn.close()



def downgrade_to_free(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE subscriptions
        SET plan='free',
            expires_at=NULL,
            daily_quiz_limit=3,
            daily_ocr_limit=1
        WHERE user_id=?
    """, (user_id,))

    conn.commit()
    conn.close()


def check_subscription_valid(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT plan, expires_at FROM subscriptions WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()

    if not row:
        conn.close()
        return "free"

    plan, expires_at = row

    if expires_at:
        if datetime.utcnow() > datetime.fromisoformat(expires_at):
            conn.close()
            downgrade_to_free(user_id)
            return "free"

    conn.close()
    return plan


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




def can_generate(user_id):
    sub = get_subscription(user_id)

    conn = get_connection()
    c = conn.cursor()


    # 👇 بعد التأكد من وجود المستخدم
    reset_daily_if_needed(user_id)

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

    plan = sub.get("plan", "free")

    if plan == "pro":
        return 25
    elif plan == "pro_plus":
        return 50
    else:
        return 3

"""
def get_daily_limit(user_id):
    sub = get_subscription(user_id)

    plan = sub["plan"]

    if plan == "pro+":
        return 50
    elif plan == "pro":
        return 25
    else:
        return 3

"""




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
        time_left = get_time_until_reset(data["user_id"])

        return f"""
📊 <b>حالة حسابك</b>

🆓 الخطة: Free  
⚡ المتبقي اليوم: <b>{remaining}/{limit}</b>  
⏳ إعادة التعيين بعد: <b>{time_left}</b>

🎁 الدعوات: {data['referrals']}

━━━━━━━━━━━━━━━
🚫 وصلت للحد بسرعة؟

🚀 لا تنتظر… واصل الآن بدون توقف:

✨ <b>Pro:</b> 25 اختبار يومياً  
🔥 <b>Pro+:</b> 50 اختبار يومياً  

أو ادعُ أصدقاءك واحصل على محاولات إضافية 👇
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



from datetime import datetime
from storage.sqlite_db import get_connection
from services.usage import reset_daily_if_needed


def is_paid_user_active(user_id):
    """
    ترجع True إذا:
    - المستخدم لديه اشتراك مدفوع (pro / pro+)
    - الاشتراك ساري (لم ينتهِ)
    - لم يتجاوز الحد اليومي
    """

    conn = get_connection()
    c = conn.cursor()

    # 1️⃣ جلب الاشتراك
    c.execute("""
        SELECT plan, expires_at, daily_quiz_limit 
        FROM subscriptions 
        WHERE user_id=?
    """, (user_id,))
    
    sub = c.fetchone()

    if not sub:
        conn.close()
        return False

    plan, expires_at, daily_limit = sub

    # 2️⃣ التأكد أنه خطة مدفوعة
    if plan not in ("pro", "pro_plus"):
        conn.close()
        return False

    # 3️⃣ التأكد أن الاشتراك لم ينتهِ
    if expires_at:
        if datetime.fromisoformat(expires_at) < datetime.utcnow():
            conn.close()
            return False

    # 4️⃣ reset يومي إن لزم
    reset_daily_if_needed(user_id)

    # 5️⃣ جلب الاستخدام الحالي
    c.execute("""
        SELECT used_today FROM users WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()

    if not row:
        return False

    used_today = row[0]

    # 6️⃣ التحقق من الحد
    if used_today < daily_limit:
        return True

    return False




from datetime import datetime, timedelta

def get_time_until_reset(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT last_reset FROM users WHERE user_id=?
    """, (user_id,))
    
    row = c.fetchone()
    conn.close()

    now = datetime.utcnow()

    if not row or not row[0]:
        # أول استخدام → reset بعد 24 ساعة
        next_reset = now + timedelta(days=1)
    else:
        last_reset = datetime.fromisoformat(row[0])
        next_reset = last_reset + timedelta(days=1)

    remaining = next_reset - now

    # تحويل إلى ساعات ودقائق
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60

    return f"{hours} ساعة و {minutes} دقيقة"



def reset_or_set_daily_usage(user_id, new_limit=3):
    conn = get_connection()
    c = conn.cursor()

    # تأكد أن المستخدم موجود
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        add_new_user(user_id)

    c.execute("""
        UPDATE users
        SET used_today = 0,
            daily_limit = ?
        WHERE user_id=?
    """, (new_limit, user_id))

    conn.commit()
    conn.close()



def activate_subscription_manual(user_id, plan, days=None):
    conn = get_connection()
    c = conn.cursor()

    limits = get_plan_limits(plan)

    # 👇 لو الأدمن حدد مدة
    duration = days if days else limits["days"]

    expires_at = None
    if duration > 0:
        expires_at = (datetime.utcnow() + timedelta(days=duration)).isoformat()

    c.execute("SELECT id FROM subscriptions WHERE user_id=?", (user_id,))
    exists = c.fetchone()

    if exists:
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


def get_user_full_info(user_id):
    conn = get_connection()
    c = conn.cursor()

    # users
    c.execute("""
    SELECT used_today, daily_limit, created_at
    FROM users WHERE user_id=?
    """, (user_id,))
    user = c.fetchone()

    # subscription
    c.execute("""
    SELECT plan, expires_at, daily_quiz_limit, daily_ocr_limit
    FROM subscriptions WHERE user_id=?
    """, (user_id,))
    sub = c.fetchone()

    # referrals
    c.execute("""
    SELECT COUNT(*) FROM referrals WHERE referrer_id=?
    """, (user_id,))
    referrals = c.fetchone()[0]

    conn.close()

    return {
        "user": user,
        "sub": sub,
        "referrals": referrals
    }

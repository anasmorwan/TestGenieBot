from storage.sqlite_db import get_connection


def get_referral_link(user_id):
    return f"https://t.me/YourBot?start=ref_{user_id}"


def save_referral(referrer_id, referred_id):
    conn = get_connection()
    c = conn.cursor()

    # تأكد أنه ليس مكرر
    c.execute("""
        SELECT 1 FROM referrals 
        WHERE referrer_id=? AND referred_id=?
    """, (referrer_id, referred_id))

    if c.fetchone():
        return

    c.execute("""
        INSERT INTO referrals (referrer_id, referred_id)
        VALUES (?, ?)
    """, (referrer_id, referred_id))

    conn.commit()
    conn.close()




    
def reward_referral_if_needed(user_id):
    conn = get_connection()
    c = conn.cursor()

    # هل لديه دعوة؟
    c.execute("""
        SELECT invited_by FROM users WHERE user_id=?
    """, (user_id,))
    row = c.fetchone()

    if not row or not row[0]:
        conn.close()
        return

    referrer_id = row[0]

    # هل تم إعطاء المكافأة مسبقاً؟
    c.execute("""
        SELECT 1 FROM referrals 
        WHERE referred_id=? AND rewarded=1
    """, (user_id,))

    if c.fetchone():
        conn.close()
        return

    # ✅ أعطِ المكافأة
    c.execute("""
        UPDATE users 
        SET free_quizzes = free_quizzes + 3
        WHERE user_id=?
    """, (referrer_id,))

    # سجل العملية
    c.execute("""
        INSERT INTO referrals (referrer_id, referred_id, rewarded)
        VALUES (?, ?, 1)
    """, (referrer_id, user_id))

    conn.commit()
    conn.close()


def show_referral_message()

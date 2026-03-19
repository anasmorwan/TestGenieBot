from sqlite.py import get_connection


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

    # أعطِ المكافأة
    c.execute("""
        UPDATE users 
        SET free_quizzes = free_quizzes + 3
        WHERE user_id=?
    """, (referrer_id,))

    conn.commit()
    conn.close()

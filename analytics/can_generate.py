from storage.sqlite_db import get_connection

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

def check_status(user_id):
    conn = get_connection()
    c = conn.cursor()


def can_generate(uid):
    if user.free_quizzes <= 0:
        return False
    return True

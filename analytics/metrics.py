from storage.sqlite_db import get_connection
from datetime import datetime, timedelta


def get_total_users():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]

    conn.close()
    return total


def get_active_today():
    conn = get_connection()
    c = conn.cursor()

    today = datetime.utcnow().date().isoformat()

    c.execute("""
    SELECT COUNT(*) FROM users
    WHERE DATE(last_reset) = ?
    """, (today,))

    count = c.fetchone()[0]

    conn.close()
    return count


def get_users_hit_limit():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT COUNT(*) FROM users
    WHERE used_today >= daily_limit
    """)

    count = c.fetchone()[0]

    conn.close()
    return count


def get_paid_users():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT COUNT(*) FROM subscriptions
    WHERE plan IN ('pro', 'pro_plus')
    """)

    count = c.fetchone()[0]

    conn.close()
    return count

def get_total_referrals():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM referrals")
    count = c.fetchone()[0]

    conn.close()
    return count



def get_metrics():
    return {
        "users": get_total_users(),
        "active_today": get_active_today(),
        "hit_limit": get_users_hit_limit(),
        "paid": get_paid_users(),
        "referrals": get_total_referrals()
    }

from storage.sqlite_db import get_connection




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


def can_generate(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT free_quizzes FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    conn.close()

    if not row:
        return False

    return row[0] > 0

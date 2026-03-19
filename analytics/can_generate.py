from storage.sqlite_db import get_connection


    

    conn.commit()
    conn.close()

def check_status(user_id):
    conn = get_connection()
    c = conn.cursor()
    # الكود... لم اكتبه
    conn.commit()
    conn.close()


def can_generate(uid):
    if user.free_quizzes <= 0:
        return False
    return True

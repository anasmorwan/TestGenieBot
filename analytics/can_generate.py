from storage.sqlite_db import get_connection

def check_status(user_id):
    conn = get_connection()
    curr = con.currcor


def can_generate(uid):
    if user.free_quizzes <= 0:
        return False
    return True

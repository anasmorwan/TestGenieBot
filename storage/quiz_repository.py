import uuid
from sqlite import sqlite

def generate_unique_quiz_code():
    while True:
        code = f"QC_{uuid.uuid4().hex[:6]}"
        conn = sqlite3.connect("quiz_users.db")
        c = conn.cursor()
        c.execute("SELECT 1 FROM user_quizzes WHERE quiz_code = ?", (code,))
        if not c.fetchone():
            conn.close()
            return code
        conn.close()

def log_quiz_share(quiz_code, shared_by_user_id, shared_by_name):
    conn = sqlite3.connect("quiz_users.db")
    c = conn.cursor()

    shared_at = datetime.now().isoformat()  

    c.execute("""  
        INSERT INTO quiz_shares (quiz_code, shared_by_user_id, shared_by_name, shared_at)  
        VALUES (?, ?, ?, ?)  
    """, (quiz_code, shared_by_user_id, shared_by_name, shared_at))  

    conn.commit()  
    conn.close()




def store_quiz(user_id, quizzes):

    conn = sqlite3.connect("quiz_users.db")
    c = conn.cursor()

    quiz_code = generate_unique_quiz_code()

    c.execute(
        "INSERT INTO user_quizzes (user_id, quiz_data, quiz_code) VALUES (?, ?, ?)",
        (user_id, json.dumps(quizzes), quiz_code)
    )

    conn.commit()
    conn.close()

    return quiz_code

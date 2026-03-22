from datetime import datetime
from storage.sqlite_db import get_connection

def log_question_attempt(user_id, quiz_code, question_index, selected, correct):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO question_attempts 
        (quiz_code, user_id, question_index, selected_option, correct_option, is_correct, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        quiz_code,
        user_id,
        question_index,
        selected,
        correct,
        int(selected == correct),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

from storage.sqlite_db import get_connection
import json
from datetime import datetime

def insert_sample_quiz_if_not_exists(db_path='quiz_users.db'):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
        
    """
    Inserts a sample quiz into the database if it doesn't already exist.

    Args:
        cursor: The database cursor object.
        conn: The database connection object.
    """
    cursor.execute("SELECT quiz_code FROM sample_quizzes WHERE quiz_code = ?", ("sample",))
    if cursor.fetchone() is None:
        # The list of questions should be a single list of dictionaries, not a list within a list.
        sample_quiz_data = [
            {
                "question": "ما هو أطول برج في العالم؟",
                "options": ["برج خليفة", "برج إيفل", "برج بيزا", "برج شنغهاي"],
                "correct_index": 0,
                "explanation": "برج خليفة في دبي هو أطول برج في العالم منذ اكتماله عام 2010."
            },
            {
                "question": "ما هو مجموع 7 + 5؟",
                "options": ["10", "12", "13", "14"],
                "correct_index": 1,
                "explanation": "7 + 5 = 12."
            },
            {
                "question": "ما هي عاصمة فرنسا؟",
                "options": ["باريس", "روما", "برلين", "مدريد"],
                "correct_index": 0,
                "explanation": "باريس هي عاصمة فرنسا وأشهر مدنها."
            },
            {
                "question": "ما هو أكبر محيط في العالم؟",
                "options": ["المحيط الأطلسي", "المحيط الهندي", "المحيط الهادئ", "المحيط المتجمد الشمالي"],
                "correct_index": 2,
                "explanation": "المحيط الهادئ هو أكبر محيط على الأرض."
            },
            {
                "question": "كم عدد أيام الأسبوع؟",
                "options": ["5", "6", "7", "8"],
                "correct_index": 2,
                "explanation": "الأسبوع يحتوي على 7 أيام."
            },
            {
                "question": "ما هو الكوكب الأحمر؟",
                "options": ["المشتري", "المريخ", "الزهرة", "عطارد"],
                "correct_index": 1,
                "explanation": "المريخ يسمى الكوكب الأحمر بسبب لونه."
            },
            {
                "question": "ما هو الغاز الذي نتنفسه؟",
                "options": ["الأكسجين", "ثاني أكسيد الكربون", "الهيدروجين", "النيتروجين"],
                "correct_index": 0,
                "explanation": "الأكسجين هو الغاز الأساسي الذي نتنفسه."
            },
            {
                "question": "كم عدد الحواس عند الإنسان؟",
                "options": ["4", "5", "6", "7"],
                "correct_index": 1,
                "explanation": "الإنسان لديه خمس حواس رئيسية."
            }
        ]
        
        # Convert the Python list of dictionaries to a JSON string.
        # `ensure_ascii=False` is important for correctly handling Arabic characters.
        sample_quiz_json = json.dumps(sample_quiz_data, ensure_ascii=False)
        
        cursor.execute(
            "INSERT INTO sample_quizzes (quiz_code, quiz_data, created_at) VALUES (?, ?, ?)",
            ("sample", sample_quiz_json, datetime.utcnow().isoformat())
        )
        conn.commit()
    conn.close()

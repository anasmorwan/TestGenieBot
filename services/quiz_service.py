# quiz_service.py
def generate_quizzes_from_text(content, user_id, num_questions=5):
    # مؤقت: هنا سيأتي استدعاء AI
    quizzes = [{"question": f"سؤال {i+1}", "options": ["A","B","C","D"], "correct_index": 0} for i in range(num_questions)]
    return quizzes
# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt
from utils.json_utils import extract_json_from_string

num_quizzes = 5
# quiz_service.py

def generate_quizzes_from_text(content, user_id, user_instruction=None, num_quizzes=5):
    """
    توليد اختبارات من نص باستخدام الذكاء الاصطناعي مع إصلاح JSON تلقائي.
    """

    prompt = build_quiz_prompt(content, num_quizzes, user_instruction=user_instruction)

    # استدعاء نموذج الذكاء الاصطناعي
    response = generate_smart_response(prompt)
    print("RAW RESPONSE:\n", response[:1000])

    # استخراج JSON مع إصلاح الأخطاء
    quizzes = extract_json_from_string(response)

    if not isinstance(quizzes, list):
        print("⚠️ Parsed quizzes is not a list. Returning empty list.")
        return []

    # تقليص عدد الاختبارات المطلوبة
    quizzes = quizzes[:num_quizzes]

    print("PARSED QUIZZES:", len(quizzes))
    return quizzes

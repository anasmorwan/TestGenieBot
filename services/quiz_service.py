# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt
from utils.json_utils import extract_json_from_string, extract_json_objects_safely

# quiz_service.py



# ======================================
num_quizzes = 5
def generate_quizzes_from_text(content, user_id, user_instruction=None, num_quizzes=5):
    prompt = build_quiz_prompt(content, num_quizzes, user_instruction=user_instruction)

    response = generate_smart_response(prompt)
    print("RAW RESPONSE:\n", response[:1000])

    # استخدام الدالة الجديدة للمعالجة الآمنة
    quizzes = extract_json_objects_safely(response)

    print("PARSED QUIZZES:", type(quizzes), len(quizzes) if isinstance(quizzes, list) else "invalid")

    if not isinstance(quizzes, list):
        return []

    # تحديد العدد المطلوب فقط
    quizzes = quizzes[:num_quizzes]

    return quizzes

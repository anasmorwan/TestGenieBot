# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt, pro_quiz_generator
from utils.json_utils import extract_json_objects_safely
from services.usage import is_paid_user_active

def generate_quizzes_from_text(content, user_id, user_instruction=None, num_quizzes=5):
    if is_paid_user_active(user_id):
        # دالة Pro ترجع قاموساً فيه metadata و questions
        pro_response = pro_quiz_generator(content, num_questions=num_quizzes)
        
        # يمكنك لاحقاً استخدام pro_response["metadata"] لحفظها في قاعدة البيانات للتتبع (Tracking)
        # db.save_metadata(user_id, pro_response["metadata"])
        
        quizzes = pro_response.get("questions", [])
        return quizzes[:num_quizzes]

    else:
        prompt = build_quiz_prompt(content, num_quizzes, user_instruction=user_instruction)
        response = generate_smart_response(prompt)
        
        quizzes = extract_json_objects_safely(response)
        
        if not isinstance(quizzes, list):
            return []
            
        return quizzes[:num_quizzes]






"""
# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt
from utils.json_utils import extract_json_from_string, extract_json_objects_safely
from ai.prompts import pro_quiz_generator
from services.usage import is_paid_user_active

# quiz_service.py


# ======================================
num_quizzes = 5
def generate_quizzes_from_text(content, user_id, user_instruction=None, num_quizzes=5):
    if is_paid_user_active(user_id):
        response = pro_quiz_generator(content, num_questions=5)
        return response

    else:
        
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
"""

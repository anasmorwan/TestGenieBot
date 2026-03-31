# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt, pro_quiz_generator, safe_generate
from utils.json_utils import extract_json_objects_safely, parse_llm_json
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
        raw_response = safe_generate(prompt) # استخدم هذه الدالة دائماً!

        
        quizzes = parse_llm_json(raw_response)

        
        if not isinstance(quizzes, list):
            return []
            
        return quizzes[:num_quizzes]




# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt, pro_quiz_generator, safe_generate
from utils.json_utils import extract_json_objects_safely, parse_llm_json
from services.usage import is_paid_user_active
from ai.beta_prompts import generate_smart_batch_prompt
from storage.messages import get_message

text = get_message("FINAL_FILE_MSG")
question_count = 10

def generate_quizzes_from_text(content, user_id, bot, user_instruction=None, num_quizzes=10, msg_id=None):
    if is_paid_user_active(user_id):
        # دالة Pro ترجع قاموساً فيه metadata و questions
        prompt = generate_smart_batch_prompt(content, num_questions=question_count)
        if msg_id:
            bot.edit_message_text(chat_id=user_id, message_id=msg_id, text=text)
            
        raw_response = safe_generate(prompt) # استخدم هذه الدالة دائماً!
        
        
        quizzes = parse_llm_json(raw_response)

        
        if not isinstance(quizzes, list):
            return []
            
        return quizzes
        
        
        # pro_response = pro_quiz_generator(content, num_questions=num_quizzes)
        
        # يمكنك لاحقاً استخدام pro_response["metadata"] لحفظها في قاعدة البيانات للتتبع (Tracking)
        # db.save_metadata(user_id, pro_response["metadata"])
        
        #quizzes = pro_response.get("questions", [])
       # return quizzes[:num_quizzes]

    else:
        if msg_id:
            bot.edit_message_text(chat_id=user_id, message_id=msg_id, text=text)
            
        prompt = build_quiz_prompt(content, num_quizzes, user_instruction=user_instruction)
        
        raw_response = safe_generate(prompt) # استخدم هذه الدالة دائماً!
        

        
        quizzes = parse_llm_json(raw_response)

        
        if not isinstance(quizzes, list):
            return []
            
        return quizzes[:num_quizzes]




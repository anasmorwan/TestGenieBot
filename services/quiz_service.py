# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt, pro_quiz_generator, safe_generate
from utils.json_utils import extract_json_objects_safely, parse_llm_json
from services.usage import is_paid_user_active
from ai.beta_prompts import generate_smart_batch_prompt
from storage.messages import get_message
from storage.session_store import user_messages_remaining
from storage.sqlite_db import update_user_major
from services.user_trap import save_user_knowledge
import random
import threading
import time

done_event = threading.Event()
# weights = [0.6, 0.25, 0.15]  # الأول له النسبة الأكبر

# selected_text = random.choices(messages, weights=weights, k=1)[0]
question_count = 10

messages = [
    get_message("FINAL_FILE_MSG"),
    get_message("FINAL_FILE_MSG2"),
    get_message("FINAL_FILE_MSG3")
]






def get_unique_random_message(user_id):
    global user_messages_remaining
    
    # إذا لم يكن المستخدم في القاموس أو القائمة فارغة، أعد تعيين القائمة
    if user_id not in user_messages_remaining or not user_messages_remaining[user_id]:
        user_messages_remaining[user_id] = messages.copy()  # نسخة من القائمة الأصلية
    
    # اختر عشوائيًا من القائمة المتبقية
    selected = random.choice(user_messages_remaining[user_id])
    
    # أزل الرسالة المختارة حتى لا تتكرر
    user_messages_remaining[user_id].remove(selected)
    
    return selected

def delayed_message(bot, user_id, delay, selected_text):
    time.sleep(delay)
    if not done_event.is_set():
        try:
            bot.edit_message_text(
                user_id,
                selected_text,
                parse_mode="HTML"
            )
        except:
            pass




def generate_quizzes_from_text(content, user_id, bot, user_instruction=None, num_quizzes=10, msg_id=None):
    if is_paid_user_active(user_id):
        if user_id == 5048253124:
            selected_text = get_unique_random_message(user_id)
        
            # دالة Pro ترجع قاموساً فيه metadata و questions
            prompt = generate_smart_batch_prompt(user_id, content, num_questions=question_count)
            if msg_id:
                        
                bot.edit_message_text(
                chat_id=user_id,
                message_id=msg_id,
                text=selected_text,
                parse_mode="HTML"
                )

        
            threading.Thread(
                target=delayed_message,
                args=(bot, user_id, 3, selected_text)
            ).start()


            raw_response = safe_generate(prompt) # استخدم هذه الدالة دائماً!
        
        
            quizzes = parse_llm_json(raw_response)
        
        
            if not isinstance(quizzes, list):
                return []
            
            return quizzes

        else:
            pro_response = pro_quiz_generator(content, num_questions=num_quizzes)
        
           #  يمكنك لاحقاً استخدام pro_response["metadata"] لحفظها في قاعدة البيانات للتتبع (Tracking)
           # db.save_metadata(user_id, pro_response["metadata"])
        
            quizzes = pro_response.get("questions", [])
            return quizzes[:num_quizzes]
            domain = pro_response["metadata"]["domain"]
            update_user_major(user_id, detected_domain)
            save_user_knowledge(user_id, content, domain)

    else:
        try:
            if msg_id:
                selected_text = get_unique_random_message(user_id)
                bot.edit_message_text(
                chat_id=user_id,
                message_id=msg_id,
                text=selected_text,
                parse_mode="HTML"
                )
                print(f"✉️ first message sent 📤", flush=True)
            prompt = build_quiz_prompt(content, num_quizzes, user_instruction=user_instruction)
                threading.Thread(
                target=delayed_message,
                args=(bot, user_id, 3, selected_text)
            ).start()
            print(f"✉️ second message sent 📤", flush=True)
        
            raw_response = safe_generate(prompt) # استخدم هذه الدالة دائماً!
            print(f"✉️ raw response message obtained", flush=True)        

        
            response_data = parse_llm_json(raw_response)
            print(f"🗣️ response_data generated", flush=True)
            detected_domain = response_data.get("domain", "General")
            print(f"🎒 detected_domain {detected_domain}", flush=True)
            update_user_major(user_id, detected_domain)
            print(f"user major updated", flush=True)
            quizzes = response_data.get("questions", [])
            print(f"✉️ quizzes extracted successfully", flush=True)
        
            save_user_knowledge(user_id, content, detected_domain)
            print(f"📖 raw user knowledge saved", flush=True)
        except Exception as e:
            print(f"ERROR: {str(e)}")
        

        
        if not isinstance(quizzes, list):
            return []
            
        return quizzes[:num_quizzes]

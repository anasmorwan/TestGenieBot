# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt, pro_quiz_generator, safe_generate, build_adaptive_quiz_prompt
from utils.json_utils import extract_json_objects_safely, parse_llm_json, parse_llm_response
from services.usage import is_paid_user_active, get_current_pro_quota
from ai.beta_prompts import generate_smart_batch_prompt
from storage.messages import get_message
from storage.session_store import user_messages_remaining
from storage.sqlite_db import update_user_major, get_user_question_count, user_has_quizzes

import random
import threading
import time
from models.quiz import QuizQuestion


done_event = threading.Event()
# weights = [0.6, 0.25, 0.15]  # الأول له النسبة الأكبر

# selected_text = random.choices(messages, weights=weights, k=1)[0]


messages = [
    get_message("FINAL_FILE_MSG"),
    get_message("FINAL_FILE_MSG2"),
    get_message("FINAL_FILE_MSG3")
]





def normalize_quizzes(raw_data):
    questions_list = []
    
    # 1. استخراج القائمة سواء كان الرد Object كامل أو Array مباشر
    if isinstance(raw_data, dict):
        questions_list = raw_data.get("questions", [])
    elif isinstance(raw_data, list):
        questions_list = raw_data

    # 2. تحويل كل عنصر إلى كائن باستخدام الكلاس الخاص بك
    normalized = []
    for q in questions_list:
        if isinstance(q, dict) or isinstance(q, list):
            obj = QuizQuestion.from_raw(q)  # 👈 السحر يحدث هنا
            if obj: 
                normalized.append(obj)
        elif isinstance(q, QuizQuestion):
            normalized.append(q)
            
    return normalized
 
 
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
    from services.user_trap import save_user_knowledge
    number = get_user_question_count(user_id)
    question_count = number if number is not None else 5
    
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

        
            add_task(0, {
                "type": "delayed_message",
                "user_id": user_id,
                "text": selected_text,
                "delay": 3,
                "run_at": time.time() + 3
            })


            raw_response = safe_generate(user_id, prompt) # استخدم هذه الدالة دائماً!
            
        
        
            # response = parse_llm_json(raw_response)
            response = parse_llm_response(raw_response, target_schema="simple_quiz")
            if not response:
                return None
            
            quizzes = response["questions"]
            detected_domain = response["domain"]
            title = response["quiz_title"]
            update_user_major(user_id, detected_domain)
        
        
            # if not isinstance(quizzes, list):
               # return []
            
            return normalize_quizzes(quizzes)
        else:
            add_task(0, {
                "type": "delayed_message",
                "user_id": user_id,
                "text": selected_text,
                "delay": 3,
                "run_at": time.time() + 3
            })
            pro_response = pro_quiz_generator(user_id, content, num_questions=question_count)
            
            print(pro_response[:1000], flush=True)  # أول 1000 حرف
            
            
           #  يمكنك لاحقاً استخدام pro_response["metadata"] لحفظها في قاعدة البيانات للتتبع (Tracking)
           # db.save_metadata(user_id, pro_response["metadata"])
        
            quizzes = pro_response.get("questions", [])
            
            
            domain = pro_response["metadata"]["domain"]
            title = pro_response["metadata"]["quiz_title"]
            update_user_major(user_id, domain)
            save_user_knowledge(user_id, content, domain)

            return normalize_quizzes(quizzes)[:question_count]
            
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
                
            
            if user_has_quizzes(user_id):
                if get_current_pro_quota(user_id):
                    # prompt = generate_smart_batch_prompt(user_id, content, num_questions=question_count)
                    # raw_response = safe_generate(user_id, prompt)
                    pass
                pass
                
            prompt = build_quiz_prompt(user_id, content, question_count, user_instruction=user_instruction)
            add_task(0, {
                "type": "delayed_message",
                "user_id": user_id,
                "text": selected_text,
                "delay": 3,
                "run_at": time.time() + 3
            })
            print(f"✉️ second message sent 📤", flush=True)
        
            raw_response = safe_generate(user_id, prompt) # استخدم هذه الدالة دائماً!
            print(raw_response[:1000], flush=True)  # أول 1000 حرف
            
            print(f"✉️ raw response message obtained", flush=True)        

        
            response_data = parse_llm_json(raw_response)
            print(f"🗣️ response_data generated", flush=True)
            detected_domain = response_data.get("domain", "General")
            title = response_data["quiz_title"]
            print(f"🎒 detected_domain {detected_domain}", flush=True)
            update_user_major(user_id, detected_domain)
            print(f"user major updated", flush=True)
            core_concept = response_data["core_academic_concept"]
            

            
            quizzes = response_data.get("questions", [])
            print(f"✉️ quizzes extracted successfully", flush=True)
        
            save_user_knowledge(user_id, content, detected_domain)
            print(f"📖 raw user knowledge saved", flush=True)
            return normalize_quizzes(quizzes)[:question_count], title
        except Exception as e:
            print(f"ERROR: {str(e)}")

        return normalize_quizzes(quizzes)[:question_count], title
        



def generate_challenge_quiz(content, user_id, num_questions, is_pro):
    try:
        
        prompt = build_adaptive_quiz_prompt(content, num_questions, is_pro)
        raw_response = safe_generate(user_id, prompt)
        
        # 🧪 اطبع الرد الخام فوراً قبل أي معالجة
        print(f"DEBUG: Raw AI Response: {raw_response[:200]}...", flush=True)

        if not raw_response or len(raw_response.strip()) < 10:
            print("❌ AI returned empty or very short string", flush=True)
            return []

        # محاولة التحويل لـ JSON
        try:
            data = parse_llm_json(raw_response)
        except Exception as json_err:
            print(f"❌ JSON Parse Error: {json_err}", flush=True)
            return []

        # 🧪 اطبع نوع البيانات المستخرجة
        print(f"DEBUG: Parsed Data Type: {type(data)}", flush=True)

        # استخدام الـ Normalize "الذكي" الذي لا يقتل البيانات
        quizzes = normalize_quizzes(data)
        
        print(f"✅ Extracted {len(quizzes)} quiz objects", flush=True)
        return quizzes
        
    except Exception as e:
        print(f"❌ Critical Error in generator: {str(e)}", flush=True)
        return []
        


from ai.llm_client import generate_smart_response
from ai.prompts import build_poll_prompt
from utils.json_utils import extract_json_objects_safely, parse_llm_json
from services.usage import is_paid_user_active
from storage.quiz_repository import store_content

def generate_and_store_question(user_id, prompt):
    print(f"DEBUG: [User: {user_id}] Sending prompt to LLM...", flush=True)
    raw_poll = generate_smart_response(prompt)
    
    if not raw_poll:
        print(f"DEBUG: [User: {user_id}] LLM returned empty response!", flush=True)
        return None, None

    print(f"DEBUG: [User: {user_id}] Parsing LLM JSON response...", flush=True)
    poll = parse_llm_json(raw_poll)
    
    if not poll:
        print(f"DEBUG: [User: {user_id}] Failed to parse JSON from LLM.", flush=True)
        return None, None

    print(f"DEBUG: [User: {user_id}] Storing poll content in DB...", flush=True)
    # ملاحظة: تأكد أن المتغير اسمه poll وليس result كما كان في الكود السابق
    poll_code = store_content(user_id, poll, content_type="poll")
    
    print(f"DEBUG: [User: {user_id}] Poll stored successfully with code: {poll_code}", flush=True)
    return poll_code, poll

def generate_poll(user_id, content, channel_name=None):
    try:
        print(f"DEBUG: [User: {user_id}] Building poll prompt. Channel: {channel_name}", flush=True)
        prompt = build_poll_prompt(content, channel_name=channel_name)
        
        poll_code, poll = generate_and_store_question(user_id, prompt)
        
        if poll is None:
            print(f"DEBUG: [User: {user_id}] generate_and_store_question returned None", flush=True)
            raise ValueError("فشل الذكاء الاصطناعي في تكوين استطلاع صالح.")

        return poll_code, poll

    except Exception as e:
        print(f"DEBUG: [User: {user_id}] Exception in generate_poll: {str(e)}", flush=True)
        raise ValueError(f"خطأ توليد الاستطلاع: {str(e)}")


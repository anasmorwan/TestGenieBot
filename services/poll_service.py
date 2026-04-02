# poll_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_poll_prompt
from utils.json_utils import extract_json_objects_safely, parse_llm_json
from services.usage import is_paid_user_active
from storage.quiz_repository import store_content


def generate_and_store_question(user_id, prompt):
    raw_poll = generate_smart_response(prompt)
    poll = parse_llm_json(raw_poll)
        
    poll_code = store_content(user_id, result, content_type="poll")
    
    return poll_code, poll


def generate_poll(user_id, content, channel_name=None):
    try:
        prompt = build_poll_prompt(content, channel_name=None)
        poll_code, poll = generate_and_store_question(user_id, prompt)
        
        if not isinstance(poll, list):
            return []

    except Exception as e:
        raise ValueError(f"خطا توليد الاستطلاع: {str(e)}")
            
    return poll_code, poll


    


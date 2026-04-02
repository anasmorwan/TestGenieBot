# poll_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_poll_prompt
from utils.json_utils import extract_json_objects_safely, parse_llm_json
from services.usage import is_paid_user_active



def generate_poll_question(prompt):
    result = generate_smart_response(prompt)
    poll_code = generate_quiz_code(result)
    return poll_code, result


def generate_poll(content):
    try:
        prompt = build_poll_prompt(content)
        poll_code, raw_poll = generate_poll_question(prompt)
        poll = parse_llm_json(raw_poll)
        
        if not isinstance(poll, list):
            return []
            
        return poll_code, poll


    


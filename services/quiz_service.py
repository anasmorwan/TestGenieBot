# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt
from utils.json_utils import extract_json_from_string

num_quizzes = 10
def generate_quizzes_from_text(content, user_id, user_instruction=None, num_quizzes=5):

    prompt = build_quiz_prompt(content, num_quizzes, user_instruction=None)

    response = generate_smart_response(prompt)

    quizzes = extract_json_from_string(response)

    return quizzes

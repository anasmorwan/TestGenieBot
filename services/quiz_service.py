# quiz_service.py
from ai.llm_client import generate_smart_response
from ai.prompts import build_quiz_prompt
from utils.json_utils import extract_json_from_string

num_quizzes = 5
def generate_quizzes_from_text(content, user_id, user_instruction=None, num_quizzes=5):

    prompt = build_quiz_prompt(content, num_quizzes, user_instruction=None)

    response = generate_smart_response(prompt)
    print("RAW RESPONSE:\n", response[:1000])

    quizzes = extract_json_from_string(response)

    print("PARSED QUIZZES:", type(quizzes), len(quizzes) if isinstance(quizzes, list) else "invalid")
    
    if not isinstance(quizzes, list):
        return []

    quizzes = quizzes[:num_quizzes]

    return quizzes

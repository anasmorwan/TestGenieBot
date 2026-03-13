# quiz_service.py
from ai.llm_client import generate_ai
from ai.prompts import build_quiz_prompt


def generate_quizzes_from_text(content, user_id, num_quizzes=5):

    prompt = build_quiz_prompt(content, num_quizzes)

    response = generate_ai(prompt)

    quizzes = parse_quiz_json(response)

    return quizzes

# llm_client.py
from openai import OpenAI

client = OpenAI()

def generate_ai(prompt):

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text

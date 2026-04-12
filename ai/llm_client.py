# llm_client.py
import os
from openai import OpenAI
from google import genai
import requests
import cohere
from groq import Groq
import json
import traceback
import logging


GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# from ai.prompts import QUIZ_PROMPT, ENGLISH_QUIZ_PROMPT, ENGLISH_QUIZ_RULES, QUIZ_RULES







# 1️⃣ Gemini
gemini_model = None
if GEMINI_API_KEY:
    try:
        gemini_model = genai.Client(api_key=GEMINI_API_KEY)
        logging.info("✅ 1. Gemini configured successfully")
    except Exception as e:
        logging.warning(f"❌ Gemini failed: {e}")

# 2️⃣ Groq
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logging.info("✅ 2. Groq configured successfully")
        models = groq_client.models.list()
        for m in models.data:
            print(m.id, flush=True)
    except Exception as e:
        logging.warning(f"❌ Groq failed: {e}")

# 3️⃣ OpenRouter
if OPENROUTER_API_KEY:
    logging.info("✅ 3. OpenRouter configured successfully")
    
# 4. إعداد Cohere
cohere_client = None
if COHERE_API_KEY:
    try:
        cohere_client = cohere.Client(COHERE_API_KEY)
        logging.info("✅ 4. Cohere configured successfully")
    except Exception as e:
        logging.warning(f"⚠️ Could not configure Cohere: {e}")





    
def generate_smart_response(prompt: str) -> str:
    """
    Tries to generate a response by attempting a chain of services silently.
    It logs errors for the developer but does not send progress messages to the user.
    """
    timeout_seconds = 45

    
    # 1️⃣ Google Gemini
    if gemini_model:
        try:
            logging.info("Attempting request with: 1. Google Gemini...")

            response = gemini_model.models.generate_content(
            model="gemini-2.0-flash-lite-001", 
            contents=prompt,
            config={
                'temperature': 0.7,
                'top_p': 0.95,
            }
            )

            if response and response.text:
                logging.info("✅ Success with Gemini.")
                print("✅ Success with Gemini", flush=True)
                return response.text.strip()

            logging.warning("❌ Gemini returned empty response. Trying fallback...")

        except Exception as e:
            logging.warning(f"❌ Gemini failed: {e}")


    
    # 2️⃣ Groq (LLaMA 3.3)
    if groq_client:
        try:
            logging.info("Attempting request with: 2. Groq (LLaMA 3.3)...")

            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-instruct",
                temperature=0.7,
                top_p=0.9,
                
            )

            result = chat_completion.choices[0].message.content

            if result:
                logging.info("✅ Success with Groq.")
                print("✅ Success with Groq", flush=True)
                return result.strip()

            logging.warning("❌ Groq returned empty response. Trying fallback...")

        except Exception as e:
            logging.warning(f"❌ Groq failed: {e}")
            

    # 3️⃣ Cohere
    if cohere_client:
        try:
            logging.info("Attempting request with: 4. Cohere...")

            response = cohere_client.chat(
                model="command-a-03-2025",
                message=prompt,
                temperature=0.8
            )

            if response and response.text:
                logging.info("✅ Success with Cohere.")
                print("✅ Success with Cohere", flush=True)
                return response.text.strip()

            logging.warning("❌ Cohere returned empty response. Trying fallback...")

        except Exception as e:
            logging.warning(f"❌ Cohere failed: {e}")


    # 4️⃣ OpenRouter
    if OPENROUTER_API_KEY:
        try:
            logging.info("Attempting request with: 3. OpenRouter...")
    
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/Oiuhelper_bot",
                "X-Title": "AI Quiz Bot"
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "google/gemma-2-9b-it",
                    "messages": [
                    {"role": "user", "content": prompt}
                    ]
                },
                timeout=timeout_seconds
            )

            response.raise_for_status()

            data = response.json()

            result_text = data["choices"][0]["message"]["content"]

            if result_text:
                logging.info("✅ Success with OpenRouter.")
                print("✅ Success with OpenRouter", flush=True)
                return result_text.strip()

            logging.warning("❌ OpenRouter returned empty response.")

        except Exception as e:
            logging.warning(f"❌ OpenRouter failed: {e}")


    # 🚫 All models failed
    raise Exception("All AI providers failed")
    return ""





def generate_free_response(prompt: str) -> str:
    """
    Tries to generate a response by attempting a chain of services silently.
    It logs errors for the developer but does not send progress messages to the user.
    """
    timeout_seconds = 45
    
    # 1️⃣ Groq (LLaMA 3.3)
    if groq_client:
        try:
            logging.info("Attempting request with: 2. Groq (LLaMA 3.3)...")

            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-instruct",
                temperature=0.7,
                top_p=0.9,
            )

            result = chat_completion.choices[0].message.content

            if result:
                logging.info("✅ Success with Groq.")
                print("✅ Success with Groq", flush=True)
                return result.strip()

            logging.warning("❌ Groq returned empty response. Trying fallback...")

        except Exception as e:
            logging.warning(f"❌ Groq failed: {e}")

    
    # 2️⃣ Google Gemini
    if gemini_model:
        try:
            logging.info("Attempting request with: 1. Google Gemini...")

            response = gemini_model.models.generate_content(
            model="gemini-2.0-flash-lite-001", 
            contents=prompt,
            config={
                'temperature': 0.7,
                'top_p': 0.95,
            }
            )

            if response and response.text:
                logging.info("✅ Success with Gemini.")
                print("✅ Success with Gemini", flush=True)
                return response.text.strip()

            logging.warning("❌ Gemini returned empty response. Trying fallback...")

        except Exception as e:
            logging.warning(f"❌ Gemini failed: {e}")

    
            

    # 3️⃣ Cohere
    if cohere_client:
        try:
            logging.info("Attempting request with: 4. Cohere...")

            response = cohere_client.chat(
                model="command-a-03-2025",
                message=prompt,
                temperature=0.8
            )

            if response and response.text:
                logging.info("✅ Success with Cohere.")
                print("✅ Success with Cohere", flush=True)
                return response.text.strip()

            logging.warning("❌ Cohere returned empty response. Trying fallback...")

        except Exception as e:
            logging.warning(f"❌ Cohere failed: {e}")


    # 4️⃣ OpenRouter
    if OPENROUTER_API_KEY:
        try:
            logging.info("Attempting request with: 3. OpenRouter...")
    
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/Oiuhelper_bot",
                "X-Title": "AI Quiz Bot"
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "google/gemma-2-9b-it",
                    "messages": [
                    {"role": "user", "content": prompt}
                    ]
                },
                timeout=timeout_seconds
            )

            response.raise_for_status()

            data = response.json()

            result_text = data["choices"][0]["message"]["content"]

            if result_text:
                logging.info("✅ Success with OpenRouter.")
                print("✅ Success with OpenRouter", flush=True)
                return result_text.strip()

            logging.warning("❌ OpenRouter returned empty response.")

        except Exception as e:
            logging.warning(f"❌ OpenRouter failed: {e}")


    # 🚫 All models failed
    raise Exception("All AI providers failed")
    return ""
            

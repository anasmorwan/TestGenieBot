#----------------------------------------
#               توليد الإختبارات للمستخدمين Pro                    
#-----------------------------------------


prompt1 = (
    "You are an expert educator.\n\n"
    "Analyze the following content and extract:\n\n"
    "1. Main topics\n"
    "2. Key concepts\n"
    "3. Important facts\n"
    "4. Difficulty level (easy, medium, hard)\n"
    "5. Type of content (theory, definitions, processes, case-based)\n"
    f"6 {LANGUAGE_RULE}\n\n"
    "Return JSON only:\n"
    "{\n"
    '  "topics": [],\n'
    '  "key_concepts": [],\n'
    '  "facts": [],\n'
    '  "difficulty": "",\n'
    '  "content_type": ""\n'
    "}\n"
)

prompt2 = (
    "You are a professional exam creator.\n\n"
    "Based on the analysis below, generate high-quality MCQs.\n\n"
    "Rules:\n"
    "- Questions must test understanding, not memorization\n"
    "- Use realistic distractors (wrong answers)\n"
    "- Avoid obvious answers\n"
    "- Mix difficulty levels\n"
    "- Include at least:\n"
    "  - 30% conceptual questions\n"
    "  - 30% application questions\n"
    "  - 20% tricky questions\n"
    "  - 20% direct questions\n\n"
    "Each question must include:\n"
    "- question\n"
    "- 4 options\n"
    "- correct_index\n"
    "- explanation (very important)\n"
    "- difficulty\n"
    "- topic\n\n"
    f"{LANGUAGE_RULE}\n\n"
    "Output format (STRICT JSON ONLY):\n"
    "Return ONLY valid JSON. No explanations outside JSON.\n\n"
    "FORMAT:\n\n"
    "[\n"
    "  {\n"
    "    \"question\": \"...\",\n"
    "    \"options\": [\"...\", \"...\", \"...\", \"...\"],\n"
    "    \"correct_index\": 0,\n"
    "    \"explanation\": \"Short explanation of why this is correct\"\n"
    "  }\n"
    "]\n\n"
    "IMPORTANT:\n"
    "- Ensure JSON is valid\n"
    "- Do not include any text before or after JSON\n"
)


prompt3 = (
    "You are a strict exam reviewer.\n\n"
    "Review the following MCQs:\n\n"
    "Check:\n"
    "- Is the correct answer واضح؟\n"
    "- Are distractors strong?\n"
    "- Is the question testing understanding?\n"
    "- Is there ambiguity?\n\n"
    "Fix and improve weak questions.\n\n"
    f"{LANGUAGE_RULE}\n"
    "Output format (STRICT JSON ONLY):\n"
    "Return ONLY valid JSON. No explanations outside JSON.\n\n"
    "FORMAT:\n\n"
    "[\n"
    "  {\n"
    '    "question": "...",\n'
    '    "options": ["...", "...", "...", "..."],\n'
    '    "correct_index": 0,\n'
    '    "explanation": "Short explanation of why this is correct"\n'
    "  }\n"
    "]\n\n"
    "IMPORTANT:\n"
    "- Ensure JSON is valid\n"
    "- Do not include any text before or after JSON\n"
)



prompt4 = f"""
You are an intelligent tutor.

Based on:
- student answers
- correct answers
- topics

Generate:

1. Strengths
2. Weaknesses
3. Smart advice (1-2 lines)

Be specific and concise.
{LANGUAGE_RULE}
"""


powerfull_prompt2 = f"""
You are an expert assessment designer specialized in creating high-quality educational quizzes.

Your task:
Generate a set of multiple-choice questions based ONLY on the provided content.

CONTENT:
"""
{input_text}
"""

INSTRUCTIONS:

1. Generate exactly {num_questions} questions.

2. Each question must:
- Test understanding, not memorization
- Be clear, specific, and unambiguous
- Avoid trivial or overly obvious questions

3. Options:
- Provide exactly 4 options
- Only ONE correct answer
- The other 3 must be plausible distractors (not random or silly)
- Avoid "All of the above" or "None of the above"

4. Cognitive variety:
Ensure a mix of:
- comprehension questions
- application questions
- inference/analysis questions

5. Difficulty:
- Medium to challenging
- Avoid very easy questions

6. Language:
- Match the language of the content
- Keep wording natural and professional

7. Output format (STRICT JSON ONLY):
Return ONLY valid JSON. No explanations outside JSON.

FORMAT:
[
  {
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "correct_index": 0,
    "explanation": "Short explanation of why this is correct"
  }
]

IMPORTANT:
- Ensure JSON is valid
- Do not include any text before or after JSON
"""



port json
from utilsjson_utils import parse_llm_json

from ai.llm_client import generate_smart_response


# جزء من ملف prompts.py (أو الملف الذي يحوي الدالة)

def pro_quiz_generator(content, num_questions=5):
    """
    محرك توليد الأسئلة الاحترافي بنظام الطبقات (Layers)
    """
    try:
        # الطبقة الأولى: فهم السياق
        analysis_input = f"{prompt1}\n\nCONTENT:\n{content}"
        analysis_result = generate_smart_response(analysis_input)
        
        # استخراج القاموس بأمان (بما أن الدالة ترجع قائمة، نأخذ العنصر الأول)
        extracted_analysis = parse_llm_json(analysis_result)
        analysis_data = extracted_analysis[0] if isinstance(extracted_analysis, list) and len(extracted_analysis) > 0 else extracted_analysis
        
        # الطبقة الثانية: التوليد
        generation_input = f"""
        {prompt2}
        
        ANALYSIS DATA:
        {json.dumps(analysis_data, ensure_ascii=False)}
        
        CONTENT:
        {content}
        
        Generate exactly {num_questions} questions.
        """
        raw_questions = generate_smart_response(generation_input)
        parsed_questions = parse_llm_json(raw_questions)
        
        # الطبقة الثالثة: المراجعة
        # نرسل الأسئلة المبدئية للمراجعة
        review_input = f"{prompt3}\n\nQUESTIONS TO REVIEW:\n{json.dumps(parsed_questions, ensure_ascii=False)}"
        final_questions_raw = generate_smart_response(review_input)
        
        # النتيجة النهائية جاهزة (وهي قائمة List جاهزة)
        final_quizzes = parse_llm_json(final_questions_raw)
        
        # التأكد من أن النتيجة النهائية قائمة صالحة
        if not isinstance(final_quizzes, list):
            final_quizzes = parsed_questions # استخدام نتيجة الطبقة الثانية كاحتياط
            
        return {
            "metadata": analysis_data, 
            "questions": final_quizzes
        }
        
    except Exception as e:
        print(f"Pro Generator Error: {e}")
        # نظام الاحتياط (Fallback)
        prompt = build_quiz_prompt(content, num_questions)
        fallback_raw = generate_smart_response(prompt)
        fallback_quizzes = parse_llm_json(fallback_raw)

        return {
            "metadata": {"fallback": True, "error": str(e)},
            "questions": fallback_quizzes if isinstance(fallback_quizzes, list) else []
        }










# --------------------------
#      توليد الأختبار ل free users   
#--------------------------

QUIZ_RULES = """
Rules:
- Use ONLY information in the content.
- Do NOT invent or assume information.
- Questions must test recall or understanding.
"""

SYSTEM_ROLE = """
You are a precise AI quiz generator.
Your task is to create quiz questions strictly from the provided content.
"""



ANTI_HALLUCINATION = """
If the content is insufficient, generate fewer questions rather than inventing information.
"""

LANGUAGE_RULE = """
Language rule:
Use the same language as the content.
"""


QUIZ_FORMAT = """
Output JSON format:

[
  {
    "question": "...",
    "options": ["A","B","C","D"],
    "correct_index": 0
  }
]

Return ONLY valid JSON.
No markdown.
"""

# prompts.py
ENGLISH_QUIZ_PROMPT = "Generate quiz questions strictly from content, return JSON only."
ARABIC_QUIZ_PROMPT = "قم بإنشاء أسئلة اختبار فقط من المحتوى المعطى، وأعد JSON صالح."


def build_quiz_prompt(content, num_questions, user_instruction=None):

    user_part = f"User instruction:\n{user_instruction}" if user_instruction else ""

    prompt = f"""
{SYSTEM_ROLE}

{QUIZ_RULES}

{LANGUAGE_RULE}

Generate {num_questions} quiz questions.

{user_part}

{QUIZ_FORMAT}

Content:
{content}
"""

    return prompt



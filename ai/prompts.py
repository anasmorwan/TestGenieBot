import re
import json
from typing import Any, Dict, List, Union

from utils.json_utils import parse_llm_json
from ai.llm_client import generate_smart_response


# ============================================================
#  Language detection
# ============================================================

ARABIC_RE = re.compile(r'[\u0600-\u06FF]')
LATIN_RE = re.compile(r'[A-Za-z]')


def detect_text_language(text: Any) -> str:
    """
    نسخة مضادة للأخطاء: تتعامل مع الـ Tuples وأي أنواع بيانات غريبة
    """
    # 1. فك الـ Tuple إذا كان النص القادم من الملف عبارة عن Tuple
    if isinstance(text, tuple):
        text = text[0] # نأخذ النص فقط ونتجاهل الباقي
        
    # 2. تحويل أي كائن إلى نص (String) كإجراء أمان إضافي
    text = str(text) if text else ""

    # الآن يمكننا استخدام .strip() بأمان تام
    if not text or not text.strip():
        return "English"

    arabic_chars = len(ARABIC_RE.findall(text))
    latin_chars = len(LATIN_RE.findall(text))

    if arabic_chars > latin_chars and arabic_chars >= 10:
        return "Arabic"

    return "English"



def contains_arabic(text: str) -> bool:
    return bool(ARABIC_RE.search(text or ""))


def contains_latin(text: str) -> bool:
    return bool(LATIN_RE.search(text or ""))


# ============================================================
#  Prompt builders
# ============================================================

def build_strict_language_prompt(lang: str) -> str:
    """
    Build a strict prompt in a clean single-language style.
    lang must be 'English' or 'Arabic'
    """
    if lang == "Arabic":
        return """
أنت خبير أكاديمي دقيق في توليد أسئلة الاختيار من متعدد.

[قاعدة اللغة الصارمة]
- المحتوى باللغة العربية.
- جميع القيم النصية داخل JSON يجب أن تكون بالعربية فقط.
- ممنوع إدخال أي نص إنجليزي في:
  question, options, explanation, topics, discipline, difficulty, complexity

[القواعد الأساسية]
- استخدم فقط المعلومات الموجودة في المحتوى.
- لا تخترع معلومات.
- إذا كانت المعلومات غير كافية، أنشئ عددًا أقل من الأسئلة بدلًا من التخمين.
- ركز على الفهم والتحليل، وليس الحفظ المباشر فقط.
- لا تستخدم: All of the above / None of the above.

[تنسيق الإخراج]
أعد JSON صالحًا فقط، بدون Markdown، وبدون شرح خارج JSON.
        """.strip()

    return """
You are a precise academic quiz generator.

[Strict language rule]
- The content is in English.
- All string values inside the JSON must be in English only.
- Do not use Arabic anywhere in:
  question, options, explanation, topics, discipline, difficulty, complexity

[Core rules]
- Use only the information in the content.
- Do not invent facts.
- If the content is insufficient, generate fewer questions instead of guessing.
- Focus on understanding and analysis, not just direct recall.
- Do not use: All of the above / None of the above.

[Output format]
Return valid JSON only, no markdown, no extra text.
    """.strip()


def build_pro_quiz_prompt(content: str, num_questions: int, lang: str) -> str:
    """
    Clean prompt for pro mode.
    Keeps the schema minimal to reduce language drift.
    """
    language_instruction = build_strict_language_prompt(lang)

    return f"""
{language_instruction}

[JSON SCHEMA]
Return ONLY a JSON object in this structure:

{{
  "metadata": {{
    "topics": ["..."],
    "difficulty": "Medium",
    "discipline": "..."
  }},
  "questions": [
    {{
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct_index": 0,
      "explanation": "...",
      "complexity": "Analysis"
    }}
  ]
}}

[IMPORTANT RULES]
- Generate exactly {num_questions} questions if possible.
- Each question must have exactly 4 options.
- correct_index must be between 0 and 3.
- Keep questions concise and academically strong.
- Do not include _thinking.
- Do not include markdown.
- Do not wrap the JSON in code fences.

CONTENT:
{content}
    """.strip()


def build_repair_prompt(raw_response: str, lang: str, num_questions: int) -> str:
    """
    Ask the model to repair malformed or wrong-language output.
    """
    if lang == "Arabic":
        return f"""
أعد كتابة JSON التالي فقط.

[قواعد الإصلاح]
- حافظ على نفس البنية.
- اجعل جميع القيم بالعربية فقط.
- لا تضف Markdown.
- لا تضف أي نص خارج JSON.
- أصلح أي خطأ في البنية أو اللغة.
- أخرج فقط JSON صالحًا.

الهدف: {num_questions} أسئلة.

JSON:
{raw_response}
        """.strip()

    return f"""
Rewrite the following output as valid JSON only.

[Repair rules]
- Keep the same structure.
- All string values must be in English only.
- Do not add markdown.
- Do not add any text outside JSON.
- Fix any JSON or language errors.
- Return only valid JSON.

Target: {num_questions} questions.

RAW OUTPUT:
{raw_response}
    """.strip()


# ============================================================
#  Validation helpers
# ============================================================
def safe_generate(prompt: str) -> str:
    """
    دالة وسيطة لضمان استخراج النص فقط في حال كانت 
    generate_smart_response تُرجع Tuple
    """
    response = generate_smart_response(prompt)
    if isinstance(response, tuple):
        return response[0]
    return response


def normalize_llm_output(full_data: Any) -> Dict[str, Any]:
    """
    إصلاح هيكل البيانات أياً كان شكل مخرجات النموذج
    """
    # 1. إذا أرجع النموذج قائمة من الأسئلة مباشرة (تغليفها في قاموس)
    if isinstance(full_data, list):
        return {"metadata": {}, "questions": full_data}
    
    if isinstance(full_data, dict):
        # 2. إذا أرجع سؤالاً واحداً فقط غير مغلف
        if "question" in full_data and "options" in full_data:
            return {"metadata": {}, "questions": [full_data]}
        # 3. الشكل الطبيعي والصحيح
        return full_data
        
    return {"metadata": {}, "questions": []}


def extract_text_blob(data: Any) -> str:
    """
    Serialize the object to inspect language usage.
    """
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return str(data)


def has_language_mismatch(data: Dict[str, Any], target_lang: str) -> bool:
    """
    Return True if output appears to violate the requested language.
    For English: reject any Arabic characters anywhere in the JSON.
    For Arabic: reject if Arabic content is missing from important text fields.
    """
    blob = extract_text_blob(data)

    if target_lang == "English":
        return contains_arabic(blob)

    # Arabic mode:
    # A few English fragments are acceptable technically, but if almost everything is Latin,
    # it suggests the model ignored the target language.
    arabic_chars = len(ARABIC_RE.findall(blob))
    latin_chars = len(LATIN_RE.findall(blob))

    return arabic_chars < latin_chars and arabic_chars < 10


def question_structure_is_valid(data: Dict[str, Any]) -> bool:
    """
    Basic structure validation.
    """
    if not isinstance(data, dict):
        return False

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        return False

    for q in questions:
        if not isinstance(q, dict):
            return False
        if "question" not in q or "options" not in q or "correct_index" not in q:
            return False
        if not isinstance(q.get("options"), list) or len(q["options"]) != 4:
            return False
        if not isinstance(q.get("correct_index"), int):
            return False
        if not (0 <= q["correct_index"] <= 3):
            return False

    return True


def trim_questions(data: Dict[str, Any], num_questions: int) -> Dict[str, Any]:
    """
    Keep only the requested number of questions.
    """
    if not isinstance(data, dict):
        return {"metadata": {}, "questions": []}

    questions = data.get("questions", [])
    if isinstance(questions, list):
        data["questions"] = questions[:num_questions]
    else:
        data["questions"] = []

    return data


# ============================================================
#  Main generator
# ============================================================

def pro_quiz_generator(content: Any, num_questions: int = 5) -> Dict[str, Any]:
    # --- إضافة الحماية هنا أيضاً ---
    if isinstance(content, tuple):
        content = content[0]
    content = str(content) if content else ""
    try:
        target_lang = detect_text_language(content)

        # المحاولة الأولى
        prompt = build_pro_quiz_prompt(content, num_questions, target_lang)
        raw_response = safe_generate(prompt) # استخدام الدالة الآمنة
        
        full_data = normalize_llm_output(parse_llm_json(raw_response))

        # محاولة الإصلاح إذا كان هناك خطأ بالهيكل أو اللغة
        if not question_structure_is_valid(full_data) or has_language_mismatch(full_data, target_lang):
            print("⚠️ Invalid structure or language mismatch. Triggering Repair...")
            repair_prompt = build_repair_prompt(raw_response, target_lang, num_questions)
            repaired_raw = safe_generate(repair_prompt) # استخدام الدالة الآمنة
            repaired_data = normalize_llm_output(parse_llm_json(repaired_raw))

            if question_structure_is_valid(repaired_data) and not has_language_mismatch(repaired_data, target_lang):
                full_data = repaired_data

        # الفحص النهائي
        if not question_structure_is_valid(full_data):
            raise ValueError("Invalid quiz structure from model")

        if has_language_mismatch(full_data, target_lang):
            raise ValueError(f"Language mismatch detected for target language: {target_lang}")

        full_data = trim_questions(full_data, num_questions)

        if not full_data.get("questions"):
            raise ValueError("No questions generated")

        return {
            "metadata": full_data.get("metadata", {}),
            "questions": full_data.get("questions", [])
        }

                                                                                            
    except Exception as e:
        print(f"⚠️ Integrated Pro Generator Error: {e}")

        # Language-safe fallback: still use the same target language
        try:
            target_lang = detect_text_language(content)
            fallback_prompt = build_pro_quiz_prompt(content, num_questions, target_lang)
            fallback_raw = generate_smart_response(fallback_prompt)
            fallback_data = normalize_llm_output(parse_llm_json(fallback_raw))

            if question_structure_is_valid(fallback_data) and not has_language_mismatch(fallback_data, target_lang):
                fallback_data = trim_questions(fallback_data, num_questions)
                return {
                    "metadata": {"fallback": True},
                    "questions": fallback_data.get("questions", [])
                }

        except Exception as fallback_error:
            print(f"⚠️ Fallback failed: {fallback_error}")

        return {
            "metadata": {
                "fallback": True,
                "error": str(e)
            },
            "questions": []
        }


# ============================================================
#  Free quiz prompt
# ============================================================

SYSTEM_ROLE = """
You are a precise AI quiz generator.
Your task is to create quiz questions strictly from the provided content.
""".strip()

QUIZ_RULES = """
Rules:
- Use ONLY information in the content.
- Do NOT invent or assume information.
- Questions must test recall or understanding.
""".strip()

QUIZ_FORMAT = """
Output JSON format:

[
  {
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_index": 0
  }
]

Return ONLY valid JSON.
No markdown.
""".strip()


    
def build_quiz_prompt(content: Any, num_questions: int, user_instruction: str = None) -> str:
    # --- إضافة الحماية ---
    if isinstance(content, tuple):
        content = content[0]
    content = str(content) if content else ""
    
    target_lang = detect_text_language(content)

    user_part = f"User instruction:\n{user_instruction}" if user_instruction else ""

    if target_lang == "Arabic":
        language_rule = """
[قاعدة اللغة]
- المحتوى باللغة العربية.
- يجب أن تكون جميع القيم النصية داخل JSON بالعربية فقط.
- ممنوع استخدام الإنجليزية في النصوص.
        """.strip()
    else:
        language_rule = """
[Language rule]
- The content is in English.
- All string values inside JSON must be in English only.
- Do not use Arabic in the output.
        """.strip()

    prompt = f"""
{SYSTEM_ROLE}

{QUIZ_RULES}

{language_rule}

Generate {num_questions} quiz questions.

{user_part}

{QUIZ_FORMAT}

Content:
{content}

[STRICT LIMITS]:
- Question text: Max 250 characters.
- EACH Option: Strictly max 95 characters.
- If an option is long, condense it without losing academic meaning.
    """.strip()

    return prompt







# ============================================================
#  برومبت الاستطلاعات
# ============================================================
Ar_polls_prompt = """
أنت خبير في صياغة استطلاعات الرأي (Polls) التفاعلية لمنصة تلجرام.
مهمتك هي تحليل نص المستخدم وتحويله إلى استطلاع رأي احترافي بصيغة JSON.

القواعد:
1. استخلص "السؤال الرئيسي" بوضوح واجعله قصيراً وجذاباً.
2. إذا قدم المستخدم خيارات، استخدمها كما هي (لا تزد عليها ولا تغير معناها).
3. إذا لم يقدم المستخدم خيارات، صغ خيارات ذكية (بحد أقصى 4 وحد أدنى 2) بناءً على سياق السؤال.
4. إذا كان الطلب غير واضح أو مجرد نص عشوائي، حاول صياغة سؤال عام حوله.
5. **أسلوب التفاعل**: أعد صياغة السؤال بأسلوب طبيعي ومتجدد يجذب الانتباه ويحفّز التفاعل. احرص على تنويع الصياغة واستخدام نبرة محادثة بشرية، مع إدخال عنصر فضول أو تأثير عاطفي عند المناسب. تجنب التكرار واللغة الجامدة أو الآلية.

المخرجات يجب أن تكون JSON فقط بالمفاتيح التالية:
- "poll": نص السؤال.
- "answers": قائمة (List) بالخيارات.

{context_clause}

نص المستخدم:
{user_input}
"""


en_polls_prompt = """
Act as an expert Telegram Poll Architect. Your task is to analyze the user's input and structure it into a professional poll format.

Guidelines:
1. **Extraction**: Identify the core question. If the user input is vague, rephrase it into a clear, engaging poll question.
2. **Options**: 
   - If the user provided specific options, use them exactly as they are.
   - If no options are provided, generate 2 to 4 contextually relevant and high-quality options.
3. **Smart Context**: Detect if the user wants a "Quiz" (one correct answer) or a "Regular Poll" (opinion-based).
4. **Engagement Style**: Rewrite the question to sound human, engaging, and scroll-stopping. Prefer conversational tone, subtle curiosity, or a hook. Avoid generic or robotic phrasing.

Output MUST be a valid JSON object with these keys:
- "poll": (String) The final question text.
- "answers": (Array of Strings) The options for the poll.

{context_clause}

User Input:
{user_input}
"""



def build_poll_prompt(content, channel_name=None):
    # --- إضافة الحماية ---
    if isinstance(content, tuple):
        content = content[0]
    content = str(content) if content else ""
    
    target_lang = detect_text_language(content)
    
    if channel_name:
        if target_lang == "Arabic":
            context_clause = f"\nملاحظة: هذا الاستطلاع مخصص لمجتمع/قناة باسم '{channel_name}'. يجب تعديل النبرة والمفردات لتناسب هذا الجمهور."
            # استخدام .format() بدلاً من f-string لأننا نريد تمرير المتغيرات لاحقاً
            prompt = Ar_polls_prompt.format(context_clause=context_clause, user_input=content)
        else:
            context_clause = f"\nNote: This poll is intended for a community/channel named '{channel_name}'. Adjust the tone and vocabulary to suit this audience."
            prompt = en_polls_prompt.format(context_clause=context_clause, user_input=content)
    else:
        # بدون channel_name، نمرر context_clause فارغاً
        if target_lang == "Arabic":
            prompt = Ar_polls_prompt.format(context_clause="", user_input=content)
        else:
            prompt = en_polls_prompt.format(context_clause="", user_input=content)
    
    return prompt

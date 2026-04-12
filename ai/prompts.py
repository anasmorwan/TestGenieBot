import re
import json
from typing import Any, Dict, List, Union

from utils.json_utils import parse_llm_json
from ai.llm_client import generate_smart_response, generate_free_response
from services.usage import is_paid_user_active
from storage.sqlite_db import get_user_difficulty

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
    difficulty = get_user_difficulty(user_id)
    
    language_instruction = build_strict_language_prompt(lang)

    return f"""
{language_instruction}

[JSON SCHEMA]
Return ONLY a JSON object in this structure:

{{
  "metadata": {{
    "domain": "e.g: Medicine",
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
      "branch": "e.g: anatomy",
      "complexity": "Analysis"
    }}
  ]
}}

[IMPORTANT RULES]
- Generate exactly {num_questions} questions if possible.
- Each question must have exactly 4 options.
- correct_index must be between 0 and 3.
- Keep questions concise and academically strong.
- {surface_level_rule}
- Difficulty level: {difficulty}
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

def safe_generate(user_id, prompt: str) -> str:
    """
    دالة وسيطة لضمان استخراج النص فقط في حال كانت 
    generate_smart_response تُرجع Tuple
    """  
    try:
        if is_paid_user_active(user_id):    
            response = generate_smart_response(prompt)
            if isinstance(response, tuple):
                return response[0]
            return response
    
        response = generate_smart_response(prompt)
        if isinstance(response, tuple):
            return response[0]
        return response
    except Exception as e:
        print(f"DEBUG: [User: {user_id}] safe_generate error: {e}", flush=True)
        return None


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

def pro_quiz_generator(user_id, content: Any, num_questions: int) -> Dict[str, Any]:
    # --- إضافة الحماية هنا أيضاً ---
    if isinstance(content, tuple):
        content = content[0]
    content = str(content) if content else ""
    try:
        target_lang = detect_text_language(content)

        # المحاولة الأولى
        prompt = build_pro_quiz_prompt(content, num_questions, target_lang)
        raw_response = safe_generate(user_id, prompt) # استخدام الدالة الآمنة
        
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

system_role = """
You are a precise AI quiz generator.
Your task is to create quiz questions strictly from the provided content.
""".strip()

quiz_rules = """
Rules:
- Use ONLY information in the content.
- Do NOT invent or assume information.
- Questions must test recall or understanding.
""".strip()

quiz_format = """
{
  "domain": "Medicine",
  "questions": [
    {
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "branch": "e.g: anatomy"
    }
  ]
}
Return ONLY valid JSON. No markdown.
""".strip()

surface_level_rule = "Avoid shallow, text-bound, surface-level retrieval, and definition-reliant questions. Do not generate questions that simply extract phrases from the text, ask for formulaic ratios, rephrase introductory sentences, or mimic definition patterns. Instead, generate inference-based, analytical, and applied questions that test real understanding of the CONTENT, not memorization or copying."



def build_quiz_prompt(user_id, content: Any, num_questions: int, user_instruction: str = None) -> str:
    # --- إضافة الحماية ---
    if isinstance(content, tuple):
        content = content[0]
    content = str(content) if content else ""
    
    target_lang = detect_text_language(content)
    difficulty = get_user_difficulty(user_id)

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
{system_role}

{quiz_rules}

{language_rule}

{surface_level_rule}

Generate {num_questions} quiz questions.

{user_part}
Difficulty level: {difficulty}

{quiz_format}

CONTENT:
{content}

[STRICT LIMITS]:
- Question text: Max 250 characters.
- EACH Option: Strictly max 95 characters.
- If an option is long, condense it without losing academic meaning.
    """.strip()

    return prompt

def build_adaptive_quiz_prompt(content: str, num_questions: int, is_pro: bool) -> str:
    """
    بناء برومبت متكيف يوزع الأسئلة بناءً على هيكلية النص (عادي أو Pro)
    """
    # تحديد المهمة بناءً على نوع المستخدم
    if is_pro:
        distribution_logic = f"""
[DISTRIBUTION STRATEGY - PRO USER]
- Distributed over 3 distinct topics/timeframes (60% Recent, 20% Oldest, 20% Random).
- Generate exactly {num_questions} questions proportionally:
  * ~60% from the 'Latest' section.
  * ~20% from the 'Oldest' section.
  * ~20% from the 'Random' section (if found, IF NOT THEN 40% FROM OLDEST SECTION).
- Create "Inter-topic" links if possible to enhance deep learning."""
    else:
        distribution_logic = f"""
[DISTRIBUTION STRATEGY - BASIC USER]
- Focus 100% on the provided 'Latest' content.
- Generate exactly {num_questions} high-quality questions for immediate recall."""

    # القواعد الصارمة (Strict Rules) بالإنجليزية لضمان انضباط الـ AI
    strict_rules = f"""
[STRICT OUTPUT RULES]
1. OUTPUT: ONLY a valid JSON object. No conversational text or markdown blocks.

2. FORMAT: 
{quiz_format}

3. LIMITS: Question < 250 chars. EACH option < 95 chars. Explanation < 200 chars.
4. QUALITY: Avoid "All of the above". Focus on academic reasoning.
5. LANGUAGE: Match the language of the 'Content' provided below."""

    prompt = f"""
{distribution_logic}

{strict_rules}

[OBJECTIVE]
Act as an expert Academic Tutor. Your goal is to trigger 'Active Recall'. 
Challenge the user's understanding, not just their memory.

Content to analyze:
{content}
    """.strip()

    return prompt
    





# ============================================================
#  برومبت الاستطلاعات
# ============================================================

Ar_polls_prompt = """
حوّل نص المستخدم إلى استطلاع تلجرام بصيغة JSON فقط.

القواعد:
- استخرج سؤالًا واضحًا وقصيرًا.
- إذا وُجدت خيارات، استخدمها كما هي لا تزد عليها.
- إذا لم توجد، أنشئ 2–4 خيارات مناسبة ومتوازنة.
- أسلوب التفاعل: صغ السؤال كما لو كنت مدير قناة تفاعلية على تلجرام. اجعله محادثيًا، جذابًا، يثير الفضول أو العاطفة، مع لمسة خفيفة من المرح أحيانًا. تجنب التكرار واللغة الجامدة.
- إذا كان النص غامضًا أو عشوائيًا، حوّله إلى سؤال عام تفاعلي وطبيعي.
- استخدم الإيموجي بشكل خفيف عند المناسب، خاصة في السياقات غير الرسمية، وتجنب الإفراط فيها.

تخصيص (اختياري):
- الطابع (tone): {tone_instruction}
- الهدف (goal): {goal_instruction}

المخرجات:
{{"poll": "...", "answers": ["...", "..."]}}

{context_clause}

النص:
{user_input}
"""

en_polls_prompt = """
Convert user input into a Telegram poll (JSON only).

Rules:
- Extract a clear, concise question.
- If options are given, use them exactly, do not suggest more options.
- If not, generate 2–4 relevant and balanced options.
- Engagement Style: Rewrite as if you are an active Telegram channel manager. Make it conversational, engaging, with subtle curiosity, emotional touch, or light humor when appropriate. Avoid repetition, stiff language, and robotic tone.
- If input is vague or random, create a general, natural, interactive question.
- Use emojis sparingly when appropriate, especially in casual contexts. Avoid overuse.

Customization (optional):
- Tone: {tone_instruction}
- Goal: {goal_instruction}

Output:
{{"poll": "...", "answers": ["...", "..."]}}

CONTEXT:
{context_clause}

Input:
{user_input}
"""

Ar_polls_prompt1 = """
حوّل نص المستخدم إلى استطلاع تلجرام بصيغة JSON فقط.

القواعد:
- استخرج سؤالًا واضحًا وقصيرًا.
- إن وُجدت خيارات، استخدمها كما هي.
- إن لم توجد، أنشئ 2-4 خيارات مناسبة ومتوازنة.
- اجعل الصياغة طبيعية وجذابة (ليست رسمية مفرطة ولا آلية).
- طابق النبرة مع السياق: جاد = رسمي، أصدقاء = خفيف.

- أسلوب التفاعل: أعد صياغة السؤال بطريقة طبيعية وشبيهة بأسلوب الإنسان، كما لو كنت مدير قناة تفاعلي في تلجرام.  
  اجعل السؤال جذابًا، محادثيًا، ويثير الفضول أو العاطفة عند المناسب، مع لمسة خفيفة من المرح أحيانًا.  
  تجنب التكرار، واللغة الجامدة، والنبرة الآلية.
- إذا كان الطلب غير واضح أو مجرد نص عشوائي، حاول صياغة سؤال عام مناسب مع الحفاظ على طابع تفاعلي وطبيعي.

المخرجات:
{{"poll": "...", "answers": ["...", "..."]}}

{context_clause}

النص:
{user_input}
"""


en_polls_prompt1 = """
Convert user input into a Telegram poll (JSON only).

Rules:
- Extract a clear, concise question.
- If options are given, keep them unchanged.
- If not, generate 2–4 relevant, balanced options.
- Keep wording natural and engaging (not robotic).
- Match tone to context: formal for serious groups, casual for friendly ones.

- Engagement Style: Rewrite the question as a human would, like an active Telegram channel manager.  
  Make it conversational, engaging, and scroll-stopping, with subtle curiosity, emotional touch, or light humor when appropriate.  
  Avoid repetition, stiff language, and robotic tone.
- If the input is vague or random, create a general question that still feels natural and interactive.

Output:
{{"poll": "...", "answers": ["...", "..."]}}

{context_clause}

Input:
{user_input}
"""


    
def clean_goal(text):
    return text.replace("📊", "").replace("⚖️", "").replace("🤝", "").strip()

def clean_tone(text):
    return text.replace("😊", "").replace("🎯", "").replace("🔥", "").strip()


def build_tone_instruction(tone, lang="ar"):
    if not tone:
        return "No specific preference — use the most suitable style for the context." if lang == "en" else "لا يوجد تخصيص — استخدم الأسلوب الأنسب للسياق."

    mapping_ar = {
        "رسمي": "استخدم أسلوبًا رسميًا ومهنيًا واضحًا.",
        "ودي": "استخدم أسلوبًا وديًا وخفيفًا وقريبًا من المحادثة.",
        "حماسي": "اجعل الصياغة حماسية وتدفع للتفاعل.",
    }

    mapping_en = {
        "رسمي": "Use a formal and professional tone.",
        "ودي": "Use a friendly and conversational tone.",
        "حماسي": "Make the tone energetic and engaging.",
    }

    mapping = mapping_en if lang == "en" else mapping_ar
    return mapping.get(tone, "Ignore this field." if lang == "en" else "تجاهل هذا الحقل.")

def build_goal_instruction(goal, lang="ar"):
    if not goal:
        return "No specific preference — use the most suitable style for the context." if lang == "en" else "لا يوجد تخصيص — استخدم الأسلوب الأنسب للسياق."

    mapping_ar = {
        "رأي": "صغ السؤال لطلب آراء المستخدمين.",
        "مقارنة": "صغ السؤال للمقارنة بين خيارات واضحة.",
        "قرار": "اجعل السؤال يساعد في اتخاذ قرار مباشر.",
        "ترفيهي": "اجعل السؤال خفيفًا وممتعًا للتفاعل.",
    }

    mapping_en = {
        "رأي": "Frame the question to gather opinions.",
        "مقارنة": "Frame the question as a comparison between options.",
        "قرار": "Make the question help in making a clear decision.",
        "ترفيهي": "Make the question light and fun to engage users.",
    }

    mapping = mapping_en if lang == "en" else mapping_ar
    return mapping.get(goal, "Ignore this field." if lang == "en" else "تجاهل هذا الحقل.")


def build_poll_prompt(content, tone=None, goal=None, channel_name=None):
    # --- إضافة الحماية ---
    if isinstance(content, tuple):
        content = content[0]
    content = str(content) if content else ""
    clean_goal = clean_goal(goal)
    clean_tone = clean_tone(tone)
    
    target_lang = detect_text_language(content)
    
    if channel_name:
        if target_lang == "Arabic":
            context_clause = f"\nملاحظة: هذا الاستطلاع مخصص لمجتمع/قناة باسم '{channel_name}'. يجب تعديل النبرة والمفردات لتناسب هذا الجمهور.\nمهم: يجب أن يكون السؤال وجميع الخيارات باللغة العربية فقط."
            
            goal_instruction = build_goal_instruction(clean_goal)
            tone_instruction = build_tone_instruction(clean_tone)
            
            prompt = Ar_polls_prompt.format(
                context_clause=context_clause,
                user_input=content,
                goal_instruction=goal_instruction,
                tone_instruction=tone_instruction
            )
        else:
            context_clause = f"\nNote: This poll is intended for a community/channel named '{channel_name}'. Adjust the tone and vocabulary to suit this audience.\nImportant: The question and all answer options must be in English only."
            
            goal_instruction = build_goal_instruction(clean_goal, lang="en")
            tone_instruction = build_tone_instruction(clean_tone, lang="en")
            
            prompt = en_polls_prompt.format(
                context_clause=context_clause, 
                user_input=content, 
                goal_instruction=goal_instruction,
                tone_instruction=tone_instruction
            )
    else:
        if target_lang == "Arabic":
            context_clause = "\nمهم: يجب أن يكون السؤال وجميع الخيارات باللغة العربية فقط."
            goal_instruction = build_goal_instruction(clean_goal)
            tone_instruction = build_tone_instruction(clean_tone)
            
            prompt = Ar_polls_prompt.format(
                context_clause=context_clause,
                user_input=content,
                goal_instruction=goal_instruction,
                tone_instruction=tone_instruction
            )
        else:
            context_clause = "\nImportant: The question and all answer options must be in English only."
            goal_instruction = build_goal_instruction(clean_goal, lang="en")
            tone_instruction = build_tone_instruction(clean_tone, lang="en")
            
            prompt = en_polls_prompt.format(
                context_clause=context_clause, 
                user_input=content, 
                goal_instruction=goal_instruction,
                tone_instruction=tone_instruction
            )
            
    return prompt

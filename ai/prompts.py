# prompts.py
ENGLISH_QUIZ_PROMPT = "Generate quiz questions strictly from content, return JSON only."
ARABIC_QUIZ_PROMPT = "قم بإنشاء أسئلة اختبار فقط من المحتوى المعطى، وأعد JSON صالح."


LANGUAGE_RULE = """
[CRITICAL LANGUAGE INSTRUCTION]
1. Analyze the exact language of the provided CONTENT.
2. The ENTIRE JSON output (keys can be English, but all values: questions, options, explanations, topics) MUST STRICTLY be written in the EXACT SAME LANGUAGE as the CONTENT.
3. NEVER translate the content. If the content is Arabic, output Arabic. If English, output English.
"""

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
# قواعد صارمة بالإنجليزية فقط (تستخدم عندما يكون المحتوى إنجليزي)
STRICT_ENG_RULE = """
[SYSTEM RULE: LANGUAGE ADHERENCE]
- THE CONTENT IS IN ENGLISH.
- YOU MUST GENERATE ALL TEXT (THINKING, QUESTIONS, OPTIONS, EXPLANATIONS) IN ENGLISH.
- DO NOT USE ARABIC. DO NOT TRANSLATE TO ARABIC.
"""

# قواعد صارمة بالعربية فقط (تستخدم عندما يكون المحتوى عربي)
STRICT_ARB_RULE = """
[قاعدة النظام: الالتزام باللغة]
- المحتوى باللغة العربية.
- يجب كتابة جميع النصوص (التفكير، الأسئلة، الخيارات، الشروحات) باللغة العربية فقط.
- يمنع استخدام الإنجليزية في القيم (Values) داخل الـ JSON.
"""

def get_dynamic_academic_prompt(lang):
    """بناء برومبت نظيف تماماً من أي لغة أخرى غير لغة الهدف"""
    rule = STRICT_ENG_RULE if lang == "English" else STRICT_ARB_RULE
    
    # لاحظ أننا أزلنا أي أمثلة عربية من هيكل الـ JSON لكي لا ينجذب لها النموذج
    return f"""
You are a Senior University Professor and Assessment Expert.
{rule}

[OPERATIONAL STEPS]:
1. Pedagogical Analysis: Identify core concepts.
2. Question Design: Focus on 'Application' and 'Analysis'.

[STRICT JSON STRUCTURE]:
Return ONLY a JSON object. All values MUST be in {lang.upper()}.
{{
  "detected_language": "{lang}",
  "_thinking": "Analyze the content here in {lang}",
  "metadata": {{
     "topics": ["Topic in {lang}"],
     "difficulty": "Medium",
     "discipline": "Subject in {lang}"
  }},
  "questions": [
     {{
       "question": "Question text in {lang}",
       "options": ["Option 1 in {lang}", "Option 2", "Option 3", "Option 4"],
       "correct_index": 0,
       "explanation": "Academic reasoning in {lang}",
       "complexity": "Analysis"
     }}
  ]
}}

[RULES]:
- No 'All of the above'.
- Question max 250 chars.
- Option max 95 chars.
"""



#----------------------------------------
#         برومبت الاختبارات ل PRO                    
#-----------------------------------------

# prompts.py

# تحديث قاعدة اللغة لتكون حاسمة (لا تقبل التأويل)
LANGUAGE_RULE = """
[CRITICAL LANGUAGE OVERRIDE]
1. First, detect the exact language of the provided CONTENT (e.g., Arabic, English).
2. You MUST write the ENTIRE output (_thinking, questions, options, explanations, topics) in THAT EXACT SAME LANGUAGE.
3. If the content is in Arabic, your thinking, explanations, and questions MUST be 100% in Arabic. NO EXCEPTIONS.
"""

ACADEMIC_PRO_INTEGRATED_PROMPT = f"""
You are a Senior University Professor and Assessment Expert.
Your task is to analyze the provided CONTENT and generate high-quality, rigorous Multiple Choice Questions (MCQs).

[OPERATIONAL STEPS]:
1. **Pedagogical Analysis**: Identify core academic concepts and potential misconceptions.
2. **Question Design**: Apply Bloom's Taxonomy. Focus on 'Application' and 'Analysis' levels.
3. **Drafting**: Create questions that require critical thinking. Ensure distractors are academic and plausible.

{LANGUAGE_RULE}

[STRICT JSON STRUCTURE]:
Return ONLY a JSON object with these exact keys. Replace the bracketed text with your output IN THE SAME LANGUAGE AS THE CONTENT:
{{
  "detected_content_language": "[Write the detected language here, e.g., Arabic]",
  "_thinking": "[Write your internal academic analysis HERE IN THE DETECTED LANGUAGE]",
  "metadata": {{
     "topics": ["[Topic 1 in detected language]", "[Topic 2 in detected language]"],
     "difficulty": "Medium",
     "discipline": "[e.g., Medicine, Law - IN THE DETECTED LANGUAGE]"
  }},
  "questions": [
     {{
       "question": "[Write the question text IN THE DETECTED LANGUAGE. Max 250 characters.]",
       "options": ["[Option A IN DETECTED LANGUAGE. Max 95 chars]", "[Option B]", "[Option C]", "[Option D]"],
       "correct_index": 0,
       "explanation": "[Write detailed academic reasoning IN THE DETECTED LANGUAGE. Max 200 chars.]",
       "complexity": "Analysis/Application"
     }}
  ]
}}

[RULES]:
- No trivial questions (0% recall).
- Distractors must be strong misleads.
- No 'All of the above'.
- STRICT LENGTH LIMITS: Option max 95 chars, Question max 250 chars, Explanation max 200 chars.
"""


# أضف هذا الجزء داخل البرومبت في ملف prompts.py


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
    "You are a strict University Professor and Board Examiner creating high-stakes academic MCQs.\n\n"
    "Based on the analysis below and the original content, generate rigorous questions.\n\n"
    "ACADEMIC RULES:\n"
    "- 0% Recall: Do NOT ask for simple definitions or direct facts.\n"
    "- 100% Cognitive Load: Questions MUST require Application, Analysis, or Evaluation of the concepts.\n"
    "- Clinical/Scenario-based (if applicable): Frame questions as real-world problems or academic case studies where possible.\n"
    "- Distractors (Wrong Options): MUST be highly plausible common misconceptions. No obvious or silly wrong answers.\n"
    "- Do NOT use 'All of the above' or 'None of the above'.\n\n"
    "Each question must include:\n"
    "- question (Clear, academic tone)\n"
    "- 4 options (Similar in length and grammatical structure)\n"
    "- correct_index (0-3)\n"
    "- explanation (Detailed academic rationale explaining why the correct answer is right AND why the distractors are wrong)\n"
    "- difficulty (Medium, Hard, Expert)\n"
    "- topic\n\n"
    f"{LANGUAGE_RULE}\n\n"
    "Output format (STRICT JSON ONLY):\n"
    f"{QUIZ_FORMAT}\n"
)


prompt3 = (
    "You are a rigorous Academic Peer-Reviewer.\n\n"
    "Review the following MCQs generated from the content.\n\n"
    "EVALUATION CRITERIA:\n"
    "1. Plausibility: Are the distractors tricky enough to confuse an unprepared student?\n"
    "2. Clarity: Is the wording grammatically perfect and academically formal?\n"
    "3. Depth: Does it test deep understanding rather than surface-level memorization?\n\n"
    "ACTION:\n"
    "- Rewrite any question that fails these criteria.\n"
    "- Strengthen weak distractors.\n"
    "- Enhance the explanation to be highly educational.\n\n"
    f"{LANGUAGE_RULE}\n\n"
    "Output format (STRICT JSON ONLY):\n"
    f"{QUIZ_FORMAT}\n"
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

import re

def detect_text_language(text):

    # البحث عن الحروف العربية في النص
    arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
    
    # إذا كان هناك أكثر من 15 حرفاً عربياً، فالنص عربي
    if len(arabic_chars) > 15:
        return "Arabic"
    return "English"
  
def pro_quiz_generator(content, num_questions=5):
    try:
        # 1. كشف اللغة برمجياً (هذا الجزء ممتاز عندك)
        target_lang = detect_text_language(content)
        
        # 2. جلب برومبت "نظيف" لا يحتوي إلا على لغة الهدف
        clean_prompt = get_dynamic_academic_prompt(target_lang)
        
        # 3. دمج المدخلات
        final_input = f"{clean_prompt}\n\nNUMBER OF QUESTIONS: {num_questions}\n\nCONTENT TO ANALYZE:\n{content}"
        
        # 4. إرسال الطلب
        raw_response = generate_smart_response(final_input)
        full_data = parse_llm_json(raw_response)

        if isinstance(full_data, list) and len(full_data) > 0:
            full_data = full_data[0]

        final_questions = full_data.get("questions", [])[:num_questions]

        if not final_questions:
            raise ValueError("No questions generated")

        return {
            "metadata": full_data.get("metadata", {}), 
            "questions": final_questions
        }
        
    except Exception as e:
        print(f"⚠️ Integrated Pro Generator Error: {e}")
        
        # نظام الاحتياط (Fallback) في حالة فشل الطلب المعقد
        # نعود للطريقة البسيطة لضمان عدم توقف الخدمة للمستخدم
        prompt = build_quiz_prompt(content, num_questions)
        fallback_raw = generate_smart_response(prompt)
        fallback_quizzes = parse_llm_json(fallback_raw)

        return {
            "metadata": {"fallback": True, "error": str(e)},
            "questions": fallback_quizzes if isinstance(fallback_quizzes, list) else []
        }



import json
from utils.json_utils import parse_llm_json

from ai.llm_client import generate_smart_response


# جزء من ملف prompts.py (أو الملف الذي يحوي الدالة)
# def pro_quiz_generator(content, num_questions=5):

  #  try:
        # بناء المدخلات بطلب واحد قوي
   #     integrated_input = f"{ACADEMIC_PRO_INTEGRATED_PROMPT}\n\nNUMBER OF QUESTIONS: {num_questions}\n\nCONTENT:\n{content}"
        
        # طلب واحد فقط للذكاء الاصطناعي
  #      raw_response = generate_smart_response(integrated_input)
        
        # تحليل الـ JSON الناتج
 #       full_data = parse_llm_json(raw_response)

        # التعامل مع احتمالية أن النتيجة قائمة أو قاموس
#        if isinstance(full_data, list) and len(full_data) > 0:
#            full_data = full_data[0]

        # استخراج البيانات الأساسية
        # نحن نأخذ 'questions' و 'metadata' فقط ونهمل '_thinking' لتوفير المساحة
 #       final_questions = full_data.get("questions", [])
#        metadata = full_data.get("metadata", {"discipline": "General Academic"})

        # تأكيد العدد المطلوب (قص الزيادة)
   #     final_questions = final_questions[:num_questions]

  #      if not final_questions:
#            raise ValueError("Empty questions list from LLM")

 #       return {
  #          "metadata": metadata, 
 #           "questions": final_questions
     #   }
        
 #   except Exception as e:
  #      print(f"⚠️ Integrated Pro Generator Error: {e}")
        
        # نظام الاحتياط (Fallback) في حالة فشل الطلب المعقد
        # نعود للطريقة البسيطة لضمان عدم توقف الخدمة للمستخدم
  #      prompt = build_quiz_prompt(content, num_questions)
   #     fallback_raw = generate_smart_response(prompt)
  #      fallback_quizzes = parse_llm_json(fallback_raw)

   #     return {
  #          "metadata": {"fallback": True, "error": str(e)},
  #          "questions": fallback_quizzes if isinstance(fallback_quizzes, list) else []
 #       }

# def pro_quiz_generator(content, num_questions=5):
#    """
#    محرك توليد الأسئلة الاحترافي بنظام الطبقات (Layers)
 #   """"
#    try:
        # الطبقة الأولى: فهم السياق
    #    analysis_input = f"{prompt1}\n\nCONTENT:\n{content}"
   #     analysis_result = generate_smart_response(analysis_input)
        
        # استخراج القاموس بأمان (بما أن الدالة ترجع قائمة، نأخذ العنصر الأول)
    #    extracted_analysis = parse_llm_json(analysis_result)
  #      analysis_data = extracted_analysis[0] if isinstance(extracted_analysis, list) and len(extracted_analysis) > 0 else extracted_analysis
        
        # الطبقة الثانية: التوليد
    #    generation_input = f"""
  #      {prompt2}
 #       
  #      ANALYSIS DATA:
  #      {json.dumps(analysis_data, ensure_ascii=False)}
#        
 #       CONTENT:
#        {content}
#        
#        Generate exactly {num_questions} questions.
#        """
#        raw_questions = generate_smart_response(generation_input)
#        parsed_questions = parse_llm_json(raw_questions)
#        
#        # الطبقة الثالثة: المراجعة
 #       # نرسل الأسئلة المبدئية للمراجعة
 #       review_input = f"{prompt3}\n\nQUESTIONS TO REVIEW:\n{json.dumps(parsed_questions, ensure_ascii=False)}"
 #       final_questions_raw = generate_smart_response(review_input)
#        
 #       # النتيجة النهائية جاهزة (وهي قائمة List جاهزة)
    #    final_quizzes = parse_llm_json(final_questions_raw)
  #      
  #      # التأكد من أن النتيجة النهائية قائمة صالحة
  #      if not isinstance(final_quizzes, list):
 #           final_quizzes = parsed_questions # استخدام نتيجة الطبقة الثانية كاحتياط
#            
#        return {
 #           "metadata": analysis_data, 
#            "questions": final_quizzes
#        }
        
#    except Exception as e:
 #       print(f"Pro Generator Error: {e}")
   #     # نظام الاحتياط (Fallback)
#        prompt = build_quiz_prompt(content, num_questions)
#        fallback_raw = generate_smart_response(prompt)
  #      fallback_quizzes = parse_llm_json(fallback_raw)

 #       return {
#            "metadata": {"fallback": True, "error": str(e)},
  #          "questions": fallback_quizzes if isinstance(fallback_quizzes, list) else []
  #      }










# --------------------------
#      توليد الأختبار ل free users   
#--------------------------
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
[STRICT LIMITS]:
- Question text: Max 250 characters.
- EACH Option: STRICTLY MAX 95 characters. This is a hard technical limit.
- If an option is long, condense it without losing the academic meaning.
"""

    return prompt



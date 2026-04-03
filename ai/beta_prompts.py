import os
import json
from ai.llm_client import generate_smart_response
from utils.json_utils import extract_json_objects_safely, parse_llm_json





explanation_style_guidelines = """
EXPLANATION STYLE (Hybrid Arabic-English, tutor-like):
You MUST write the explanation mainly in Arabic, with English medical terms kept exactly as they are.
Do NOT translate medical terms, diagnoses, drug names, lab tests, or anatomical structures into Arabic.
Do NOT write the explanation in full English.
Do NOT repeat the question stem or paraphrase it too closely.
Do NOT mirror the same wording or structure of the source text.

Use this exact 5-part structure, but keep it natural and concise:
1. 🎯 الخلاصة: one short Arabic sentence that states the core answer.
2. 🔍 التحليل: short Arabic reasoning with English medical terms embedded naturally.
3. ✅ لماذا هذه الإجابة؟: a direct logic explanation in Arabic.
4. 💡 حيلة الامتحان: a short exam trick or memory hook in Arabic.
5. ❌ استبعاد الخيارات: brief reasons why the main distractors are wrong.

Style rules:
- Keep the explanation compact and high-yield.
- Prefer simple Arabic with medical terms in English.
- Mention only the key clues from the source text.
- Never invent facts outside the source.
- Never make the explanation long-winded or repetitive.
"""

# أضف هذا المتغير داخل دالة generate_smart_batch_prompt
example_json_format = f"""
Output JSON format:
[
  {{
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_index": 0,
    "explanation": "🎯 خلاصة سريعة: تشخيص الـ Pyloric Stenosis...\\n🔍 Clinical Keys: Projectile vomiting, Olive-shaped mass...\\n💡 حيلة: Projectile vomiting + olive = Pyloric stenosis",
    "type": "Diagnosis"
  }}
]
"""




def analyze_text_metadata(text_content):
    """
    Analyze text domain, subject, difficulty, and confidence.
    """
    analysis_prompt = f"""
Return ONLY a JSON object with this exact structure:
{{
  "domain": "medicine",
  "subject": "anatomy | physiology | biochemistry | pathology | pharmacology | microbiology | clinical_medicine",
  "concepts": ["concept1", "concept2"],
  "estimated_difficulty": "early | mid | advanced",
  "source_mode": "textbook | mixed | case_based",
  "confidence": 0.0
}}

Rules:
- estimated_difficulty = early for definitions, lists, basic facts, and foundation-level content.
- estimated_difficulty = mid for conceptual or moderate reasoning content.
- estimated_difficulty = advanced for clinical cases, management, differential diagnosis, or multi-step reasoning.
- source_mode = textbook if the text is factual and non-case-based.
- source_mode = case_based if the text is a patient scenario.
- confidence must be between 0 and 1.

content:
{text_content[:1200]}
"""
    raw_response = generate_smart_response(analysis_prompt)
    parsed_response = parse_llm_json(raw_response)

    if isinstance(parsed_response, str):
        return json.loads(parsed_response)
    return parsed_response


def build_exact_question_plan(stage_weights, num_questions):
    """
    Convert stage weights into an exact per-question plan.
    Returns:
        counts: dict[type] = count
        plan: list[dict] in final generation order
    """
    weighted = {k: v * num_questions for k, v in stage_weights.items()}
    counts = {k: int(v) for k, v in weighted.items()}

    remainder = num_questions - sum(counts.values())
    fractional_parts = sorted(
        ((weighted[k] - counts[k], k) for k in stage_weights.keys()),
        reverse=True
    )

    for _, key in fractional_parts[:remainder]:
        counts[key] += 1

    # Build ordered plan
    plan = []
    slot = 1
    for q_type, count in counts.items():
        for _ in range(count):
            plan.append({"slot": slot, "type": q_type})
            slot += 1

    return counts, plan



def normalize_stage_with_heuristics(text_content, metadata):
    """
    Fallback heuristic to prevent wrong stage classification.
    """
    text_lower = text_content.lower()

    clinical_cues = [
        "patient", "fever", "pain", "jaundice", "vomiting", "diarrhea",
        "blood pressure", "x-ray", "ct", "mri", "ultrasound", "lab",
        "hemoglobin", "bilirubin", "ast", "alt", "alp", "ecg", "scleral icterus"
    ]

    textbook_cues = [
        "definition", "function", "structure", "enzyme", "pathway",
        "classification", "list", "parts", "origin", "insertion"
    ]

    clinical_hits = sum(1 for cue in clinical_cues if cue in text_lower)
    textbook_hits = sum(1 for cue in textbook_cues if cue in text_lower)

    stage = metadata.get("estimated_difficulty", "early")
    confidence = float(metadata.get("confidence", 0.5))

    # If LLM is uncertain, bias toward safer direct questions for educational text
    if confidence < 0.65 and textbook_hits >= clinical_hits:
        stage = "early"
    elif clinical_hits >= 3 and stage == "early":
        stage = "mid"

    return stage




def generate_smart_batch_prompt(text_content, num_questions=5):
    """
    دالة توليد البرومبت الشامل بناءً على الأوزان
    """
    # 1. تحليل النص لمعرفة السياق
    metadata = analyze_text_metadata(text_content)
    domain_name = metadata.get('domain', 'medicine')
    detected_subject = metadata['subject']
    user_stage = metadata['estimated_difficulty']

    current_dir = os.path.dirname(os.path.abspath(__file__))

    json_path = os.path.join(current_dir, 'domain_profile.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            full_json = json.load(f)
            config = full_json[domain_name]
    except FileNotFoundError:
        print(f"❌ لم يتم العثور على الملف في المسار: {json_path}")
        # يمكنك هنا وضع قيمة افتراضية أو رفع الخطأ بشكل أوضح
        raise
    
    
        
    # 3. تحضير نسب الأسئلة (Weights) كـ نص مقروء للبرومبت
    stage_weights = config["stages"][user_stage]["weights"]
    # تحويل { "recall": 0.4 } إلى "recall: 40%"
    weights_text = "\n".join([f"- {k.replace('_', ' ').title()}: {int(v * 100)}%" for k, v in stage_weights.items()])
    
    # 4. تحضير أولويات التخصص (Subject Priorities) كـ نص
    subject_matrix = config["subject_type_matrix"].get(detected_subject, {})
    high_priority = ", ".join(subject_matrix.get("high", ["general concepts"]))
    medium_priority = ", ".join(subject_matrix.get("medium", []))
    
    # 5. تحضير المشتتات (Distractors)
    distractors_text = "\n".join([f"- {rule}" for rule in config['generate_distractors']])

    # أضف هذا المنطق قبل بناء الـ final_prompt
    if user_stage == "early":
        target_structure = "Direct Academic Question (Clear and concise, focusing on facts)"
    else:
        target_structure = config['response_style']['structure'] # سيأخذ clinical_vignette من الـ JSON
  

    # 6. بناء البرومبت النهائي الموجه للذكاء الاصطناعي
    final_prompt = f"""
    SYSTEM ROLE: You are an expert {config['title']} Education Specialist.
    
    CONTEXT:
    This is an educational text for the {config['title']} domain, specifically the {detected_subject} subject.
    Target Student Level: {user_stage} stage.
    Key Concepts inside text: {", ".join(metadata['concepts'])}.

    TASK:
    Generate exactly {num_questions} USMLE-style MCQs based on the provided SOURCE TEXT. 
    Do NOT generate all questions in the same style. You MUST diversify them according to the following strict distribution:

    QUESTION TYPE DISTRIBUTION (Based on student stage):
    {weights_text}

    SUBJECT FOCUS PRIORITIES:
    Because this is {detected_subject}, follow these priorities for the question concepts:
    - High Focus: Give highest priority to questions testing [{high_priority}].
    - Medium Focus: Moderate priority for [{medium_priority}].

    DISTRACTOR RULES (CRITICAL):
    {distractors_text}

    FORMAT & STYLE:
    - Structure: {target_structure}
    - Tone: {config['response_style']['tone']}
    - Structure: Every question MUST use a {config['response_style']['structure']}.
    - Explanation Depth: {config['response_style']['explanation_depth']}. Explain why the correct answer is right AND strictly explain why each distractor is wrong.
    - Adherence: Use ONLY information derived from the SOURCE TEXT below.
    - explanation Language: Hybrid (English for Medical Terms, Arabic for explanation and logic).
    
    {explanation_style_guidelines}
    
    SOURCE TEXT:
    {text_content}
    
    OUTPUT FORMAT: Return ONLY a valid JSON array of question objects.
    {example_json_format}
    """
    
    return final_prompt

  

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
    Build a production-ready generation prompt with exact question planning.
    """
    metadata = analyze_text_metadata(text_content)
    domain_name = metadata.get('domain', 'medicine')
    detected_subject = metadata.get('subject', 'clinical_medicine')
    user_stage = normalize_stage_with_heuristics(text_content, metadata)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'domain_profile.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            full_json = json.load(f)
            config = full_json[domain_name]
    except FileNotFoundError:
        raise FileNotFoundError(f"Domain profile not found at: {json_path}")

    stage_weights = config["stages"][user_stage]["weights"]
    counts, question_plan = build_exact_question_plan(stage_weights, num_questions)

    weights_text = "\n".join([f"- {k}: {v}" for k, v in counts.items()])

    subject_matrix = config["subject_type_matrix"].get(detected_subject, {})
    high_priority = ", ".join(subject_matrix.get("high", ["general concepts"]))
    medium_priority = ", ".join(subject_matrix.get("medium", [])) or "general concepts"

    distractors_text = "\n".join([f"- {rule}" for rule in config['generate_distractors']])

    # Stage-specific style control
    if user_stage == "early":
        question_style_rule = """
QUESTION STYLE RULES:
- Use direct academic questions.
- Avoid patient vignettes unless the source text already contains one.
- Prefer recall, definition, identification, and basic concept questions.
- Do NOT force clinical scenarios.
- Use short stems.
"""
    elif user_stage == "mid":
        question_style_rule = """
QUESTION STYLE RULES:
- Mix direct questions and light clinical reasoning.
- Use a limited vignette only when it helps testing understanding.
- Keep stems concise.
"""
    else:
        question_style_rule = """
QUESTION STYLE RULES:
- Use clinical vignettes when appropriate.
- Prioritize reasoning, interpretation, and diagnosis/management logic.
- Keep one best answer only.
"""

    plan_text = "\n".join([f"{item['slot']}. {item['type']}" for item in question_plan])

    final_prompt = f"""
SYSTEM ROLE: You are an expert {config['title']} Education Specialist.

CONTEXT:
- Domain: {config['title']}
- Subject: {detected_subject}
- Student stage: {user_stage}
- Source mode: {metadata.get('source_mode', 'textbook')}
- Key concepts: {", ".join(metadata.get('concepts', []))}

TASK:
Generate exactly {num_questions} MCQs based ONLY on the SOURCE TEXT.

IMPORTANT:
- Follow the exact question plan below.
- Do not ignore the distribution.
- Do not make all questions clinical.
- Do not invent facts outside the text.
- Each question must have one best answer and plausible distractors.

EXACT QUESTION PLAN:
{plan_text}

QUESTION TYPE PRIORITIES:
- High priority: {high_priority}
- Medium priority: {medium_priority}

QUESTION DISTRACTOR RULES:
{distractors_text}

{question_style_rule}

GLOBAL STYLE:
- Tone: {config['response_style']['tone']}
- Explanation depth: {config['response_style']['explanation_depth']}
- For early stage, keep questions direct and factual.
- For mid and advanced, increase reasoning gradually.
- Do not repeat the same pattern across all questions.

EXPLANATION RULE:
- Use the hybrid Arabic-English explanation style below.
{explanation_style_guidelines}

SOURCE TEXT:
{text_content}

OUTPUT FORMAT:
Return ONLY a valid JSON array.
Each object must have:
- question
- options
- correct_index
- explanation
- type
- difficulty
"""

    return final_prompt  

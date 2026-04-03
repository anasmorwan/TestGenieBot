import os
import re
import json
from ai.llm_client import generate_smart_response
from utils.json_utils import parse_llm_json
from bot.bot_instance import mybot



def normalize_text_content(text_content):
    if isinstance(text_content, tuple):
        return " ".join(map(str, text_content))
    if text_content is None:
        return ""
    return str(text_content)


def canonicalize_key(value):
    """
    Convert any text to a stable config key:
    - lowercase
    - trim
    - normalize spaces/dashes
    - convert separators to underscore
    """
    value = normalize_text_content(value).strip().lower()
    value = re.sub(r"[\s\-]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.replace(" ", "_")


def parse_subject_field(subject_value, available_subjects=None, fallback="general"):
    """
    Accepts:
    - "anatomy | pathology"
    - "anatomy/pathology"
    - ["anatomy", "pathology"]

    Returns normalized subjects matched against available_subjects if provided.
    """
    if isinstance(subject_value, list):
        raw_parts = subject_value
    else:
        text = normalize_text_content(subject_value)
        raw_parts = re.split(r"\s*[|,/;&]\s*|\s+\band\b\s+", text, flags=re.IGNORECASE)

    available_map = {}
    if available_subjects:
        for s in available_subjects:
            available_map[canonicalize_key(s)] = s

    cleaned = []
    for part in raw_parts:
        key = canonicalize_key(part)
        if not key:
            continue

        # If config has this key, use the exact config key
        if available_map:
            matched = available_map.get(key)
            if matched and matched not in cleaned:
                cleaned.append(matched)
        else:
            if key not in cleaned:
                cleaned.append(key)

    return cleaned or [fallback]


def build_subject_allocation(subjects, num_questions):
    """
    Fair split across multiple subjects.
    """
    subjects = subjects or ["general"]
    base = num_questions // len(subjects)
    remainder = num_questions % len(subjects)

    allocation = {s: base for s in subjects}
    for i, s in enumerate(subjects):
        if i < remainder:
            allocation[s] += 1

    return allocation


def merge_subject_matrices(config, subjects):
    """
    Merge high/medium/low priorities across multiple subjects.
    """
    high, medium, low = [], [], []
    subject_blocks = []

    for subject in subjects:
        matrix = config.get("subject_type_matrix", {}).get(subject, {})
        s_high = matrix.get("high", [])
        s_medium = matrix.get("medium", [])
        s_low = matrix.get("low", [])

        high.extend(s_high)
        medium.extend(s_medium)
        low.extend(s_low)

        subject_blocks.append(
            f"- {subject}: high = {', '.join(s_high) if s_high else 'general concepts'}; "
            f"medium = {', '.join(s_medium) if s_medium else 'general concepts'}"
        )

    def dedupe(items):
        seen = set()
        out = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return {
        "high": dedupe(high) or ["general concepts"],
        "medium": dedupe(medium) or ["general concepts"],
        "low": dedupe(low),
        "subject_blocks": subject_blocks,
    }


def detect_source_language(text_content):
    text_content = normalize_text_content(text_content)
    arabic_chars = sum(1 for ch in text_content if '\u0600' <= ch <= '\u06FF')
    latin_chars = sum(1 for ch in text_content if ch.isalpha() and not ('\u0600' <= ch <= '\u06FF'))
    return "Arabic" if arabic_chars >= latin_chars else "English"


explanation_style_guidelines = """
EXPLANATION STYLE:
- Use the SAME language as the SOURCE TEXT.
- If source is English, write question, options, and explanation in English.
- If source is Arabic, write them in Arabic, while keeping standard medical terms in English when useful.
- Keep explanation very short: max 3 short lines, max 45 words.
- Do NOT repeat the stem.
- Do NOT make the explanation long or split it into many bullets.

Format:
🎯 Answer:
🔍 Why:
❌ Why not others:
"""


def analyze_text_metadata(text_content):
    text_content = normalize_text_content(text_content)

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
estimated_difficulty = early for definitions, lists, basic facts, and foundation-level content.
estimated_difficulty = mid for conceptual or moderate reasoning content.
estimated_difficulty = advanced for clinical cases, management, differential diagnosis, or multi-step reasoning.
source_mode = textbook if the text is factual and non-case-based.
source_mode = case_based if the text is a patient scenario.
confidence must be between 0 and 1.


content:
{text_content[:1200]}
"""
    raw_response = generate_smart_response(analysis_prompt)
    parsed_response = parse_llm_json(raw_response)

    if isinstance(parsed_response, str):  
        return json.loads(parsed_response)  
    return parsed_response


def build_exact_question_plan(stage_weights, num_questions):
    weighted = {k: v * num_questions for k, v in stage_weights.items()}
    counts = {k: int(v) for k, v in weighted.items()}

    remainder = num_questions - sum(counts.values())
    fractional_parts = sorted(
        ((weighted[k] - counts[k], k) for k in stage_weights.keys()),
        reverse=True
    )

    for _, key in fractional_parts[:remainder]:
        counts[key] += 1

    plan = []
    slot = 1
    for q_type, count in counts.items():
        for _ in range(count):
            plan.append({"slot": slot, "type": q_type})
            slot += 1

    return counts, plan


def normalize_stage_with_heuristics(text_content, metadata):
    text_content = normalize_text_content(text_content)
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

    if confidence < 0.65 and textbook_hits >= clinical_hits:
        stage = "early"
    elif clinical_hits >= 3 and stage == "early":
        stage = "mid"

    return stage


def sanitize_generated_questions(items, num_questions):
    if not isinstance(items, list):
        return items

    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            continue

        q = dict(item)
        q["question"] = str(q.get("question", "")).strip()
        q["options"] = [str(x).strip() for x in q.get("options", [])[:4]]
        q["explanation"] = " ".join(str(q.get("explanation", "")).split())
        q["type"] = str(q.get("type", "")).strip()
        q["difficulty"] = str(q.get("difficulty", "")).strip()
        cleaned.append(q)

    return cleaned[:num_questions]


def generate_smart_batch_prompt(text_content, num_questions=4):
    text_content = normalize_text_content(text_content)
    metadata = analyze_text_metadata(text_content)

    domain_name = metadata.get("domain", "medicine")
    print(f"📚 Domain : {domain_name}", flush=True)
    detected_subject = metadata.get("subject", "clinical_medicine")
    print(f"📖 subject : {detected_subject}", flush=True)
    user_stage = normalize_stage_with_heuristics(text_content, metadata)
    print(f"📊 current user_stage : {user_stage}", flush=True)
    source_language = detect_source_language(text_content)
    print(f"🌐 source_language is : {source_language}", flush=True)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "domain_profile.json")

    with open(json_path, "r", encoding="utf-8") as f:
        full_json = json.load(f)
        config = full_json[domain_name]

    stage_weights = config["stages"][user_stage]["weights"]
    counts, question_plan = build_exact_question_plan(stage_weights, num_questions)


    distractors_text = "\n".join([f"- {rule}" for rule in config["generate_distractors"]])
    
    available_subjects = list(config.get("subject_type_matrix", {}).keys())
    subjects = parse_subject_field(metadata.get("subject", "general"), available_subjects=available_subjects, fallback="general")
    subject_allocation = build_subject_allocation(subjects, num_questions)
    subject_bundle = merge_subject_matrices(config, subjects)
    mybot.send_message(chat_id=5048253124, text=f"beta prompt results:\n\n1.domain_name: {domain_name}\n2.detected_subject: {detected_subject}\n3. user_stage: {user_stage}\n4. text language: {source_language}\n5. available_subjects: {available_subjects}\n 6.subject_allocation: {subject_allocation}\n\7.subject_bundle: {subject_bundle}")
    


    if user_stage == "early":
        question_style_rule = (
            "Use direct academic questions. "
            "Avoid patient vignettes unless the source text is case-based. "
            "Prefer recall, definition, identification, and basic concept questions."
        )
    elif user_stage == "mid":
        question_style_rule = (
            "Mix direct questions and light reasoning. "
            "Use a short vignette only when it helps understanding."
        )
    else:
        question_style_rule = (
            "Use clinical reasoning when appropriate. "
            "Keep one best answer only."
        )

    plan_text = "\n".join([f"{item['slot']}. {item['type']}" for item in question_plan])

    final_prompt = f"""
SYSTEM ROLE: You are an expert {config['title']} Education Specialist.

CONTEXT:
- Subjects: {", ".join(subjects)}
- Student stage: {user_stage}
- Source mode: {metadata.get('source_mode', 'textbook')}
- Source language: {source_language}
- Key concepts: {", ".join(metadata.get('concepts', []))}

TASK:
Generate exactly {num_questions} MCQs based ONLY on the SOURCE TEXT.

HARD RULES:
- Return exactly {num_questions} items, no more and no less.
- Output language must match the SOURCE LANGUAGE.
- If the source text is English, write question, options, and explanation in English.
- If the source text is Arabic, write them in Arabic.
- Do not invent facts outside the source.
- Each question must have one best answer and plausible distractors.
- Keep explanations short.

EXACT QUESTION PLAN:
{plan_text}

SUBJECT COVERAGE PLAN:
{chr(10).join([f"- {s}: {n} question(s)" for s, n in subject_allocation.items()])}

DISTRACTOR RULES:
{distractors_text}

QUESTION STYLE:
{question_style_rule}

EXPLANATION RULE:
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


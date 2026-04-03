import os
import json
from ai.llm_client import generate_smart_response
from utils.json_utils import parse_llm_json


def normalize_text_content(text_content):
    if isinstance(text_content, tuple):
        return " ".join(map(str, text_content))
    if text_content is None:
        return ""
    return str(text_content)


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
    detected_subject = metadata.get("subject", "clinical_medicine")
    user_stage = normalize_stage_with_heuristics(text_content, metadata)
    source_language = detect_source_language(text_content)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "domain_profile.json")

    with open(json_path, "r", encoding="utf-8") as f:
        full_json = json.load(f)
        config = full_json[domain_name]

    stage_weights = config["stages"][user_stage]["weights"]
    counts, question_plan = build_exact_question_plan(stage_weights, num_questions)

    subject_matrix = config["subject_type_matrix"].get(detected_subject, {})
    high_priority = ", ".join(subject_matrix.get("high", ["general concepts"]))
    medium_priority = ", ".join(subject_matrix.get("medium", [])) or "general concepts"
    distractors_text = "\n".join([f"- {rule}" for rule in config["generate_distractors"]])

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
- Subject: {detected_subject}
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

QUESTION PRIORITIES:
- High priority: {high_priority}
- Medium priority: {medium_priority}

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


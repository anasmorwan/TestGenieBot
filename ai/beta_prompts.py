import os
import re
import json
from ai.llm_client import generate_smart_response
from utils.json_utils import parse_llm_json
from bot.bot_instance import mybot
from storage.sqlite_db import update_user_major, get_user_question_count, get_user_difficulty

from services.user_trap import save_user_knowledge

admin_id = 5048253124

def normalize_text_content(text_content):
    if isinstance(text_content, tuple):
        return " ".join(map(str, text_content))
    if text_content is None:
        return ""
    return str(text_content)

def clean_priority_list(items):
    items = [x for x in items if x and x != "general concepts"]
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
    
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

def analyze_text_metadata(text_content, config):
    
    valid_subjects = config.get("subjects", [])
    subjects_str = " | ".join(valid_subjects)
    
    analysis_prompt = f"""
Return ONLY a JSON object.
STRICT SUBJECT LIST:
{subjects_str}

Structure:
{{
"domain": "medicine",
"subject": "Select one or more from the STRICT LIST above",
"concepts": ["concept1", "concept2"],
"estimated_difficulty": "early | mid | advanced",
"cognitive_level": "recall | application | evaluation",
"source_mode": "textbook | mixed | case_based",
"confidence": 0.5
}}

STRICT RULES:
1. Use ONLY the subjects provided above.
2. If multiple subjects apply, join them with " | ".
3. Cognitive Level Guide:
   - recall: facts/definitions.
   - application: mechanisms/understanding.
   - evaluation: clinical judgment/decisions.

Difficulty Rules (STRICT):
- early = pure recall (definitions, lists, single facts, no reasoning)
- mid = requires understanding OR 1-step reasoning (explain, compare, mechanism)
- advanced = requires multi-step reasoning OR decision OR case interpretation

Hard constraints:
- If NO reasoning → MUST be early
- If ONE reasoning step → mid
- If MULTI-step reasoning or thinking → advanced
- DO NOT default to mid

General Rules:
- source_mode = textbook if the text is factual and non-case-based.
- source_mode = case_based if the text is a case scenario.
- confidence must be between 0 and 1.


Content:
{text_content[:1500]}
"""
    raw_response = generate_smart_response(analysis_prompt)
    parsed_response = parse_llm_json(raw_response)

    if isinstance(parsed_response, str):  
        return json.loads(parsed_response)  
    return parsed_response



    
def get_style_patterns(config, question_plan):
    # استخراج الأنماط الفريدة المطلوبة بناءً على الخطة
    required_types = set(item['type'] for item in question_plan)
    mapping = config.get("pattern_mapping", {})
    patterns_text = "STYLE GUIDELINES PER TYPE:\n"
    
    for q_type in required_types:
        pattern_key = mapping.get(q_type)
        if pattern_key and pattern_key in config:
            examples = "\n".join(config[pattern_key][:2]) # نأخذ مثالين فقط للاختصار
            patterns_text += f"Type '{q_type}':\n{examples}\n"
            
    return patterns_text
    


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

def normalize_stage_smart(user_id, metadata, config):
    user_level = get_user_difficulty(user_id)
    # مصفوفة الرتب لتسهيل المقارنة الرياضية
    rank = {"early": 1, "mid": 2, "advanced": 3}
    
    ai_difficulty = metadata.get("estimated_difficulty", "early")
    cognitive_level = metadata.get("cognitive_level", "recall")
    
    # 1. تحديد أعلى Bias للمواد المكتشفة
    detected_subjects = parse_subject_field(metadata.get("subject", ""), available_subjects=config["subjects"])
    subject_biases = config.get("subject_bias", {})
    
    max_bias_rank = 1
    for s in detected_subjects:
        b = subject_biases.get(s, "early")
        max_bias_rank = max(max_bias_rank, rank.get(b, 1))

    # 2. منطق الرفع (Promotion Logic)
    current_rank = rank.get(ai_difficulty, 1)
    
    # إذا كانت المادة صعبة بطبعها (مثل Pathology) والنموذج قال early، نرفعها لـ Mid
    final_rank_val = max(current_rank, max_bias_rank)
    
    # إذا كان المستوى المعرفي هو 'evaluation' (اتخاذ قرار)، يجب أن تكون حتماً advanced
    if cognitive_level == "evaluation":
        final_rank_val = 3

    reverse_rank = {1: "early", 2: "mid", 3: "advanced"}
    return reverse_rank.get(final_rank_val, "early")



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



def generate_smart_batch_prompt(user_id, text_content, num_questions):
    text_content = normalize_text_content(text_content)
    
    # تحميل الإعدادات أولاً (نفترض الطب كافتراضي حالياً)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "domain_profile.json"), "r", encoding="utf-8") as f:
        full_config = json.load(f)
        config = full_config["medicine"] # يمكن جعلها ديناميكية لاحقاً

    # 1. التحليل المبدئي
    metadata = analyze_text_metadata(text_content, config)


    detected_domain = metadata.get("domain", "General")
    update_user_major(user_id, detected_domain)
    save_user_knowledge(user_id, text_content, detected_domain)
        
    
    # 2. التطبيع الاحترافي للمستوى
    user_stage = normalize_stage_smart(user_id, metadata, config)

    available_subjects = config.get("subjects", [])
    
    # 3. جلب التخصصات وتوزيع الأسئلة
    subjects = parse_subject_field(
        metadata.get("subject", "general"), 
        available_subjects=available_subjects, 
        fallback=available_subjects[0] # بدلاً من general، خذ أول مادة في القائمة كافتراضي
    )
    subject_allocation = build_subject_allocation(subjects, num_questions)
    
    # 4. بناء خطة الأسئلة بناءً على أوزان الـ Stage المختار
    stage_weights = config["stages"][user_stage]["weights"]
    counts, question_plan = build_exact_question_plan(stage_weights, num_questions)

    # 5. استخراج "الأنماط" لتعزيز جودة الصياغة
    style_patterns = ""
    mapping = config.get("pattern_mapping", {})
    for q_type in counts.keys():
        pattern_key = mapping.get(q_type)
        if pattern_key and pattern_key in config:
            example = config[pattern_key][0] # نأخذ أول مثال كنمط صياغة
            style_patterns += f"- For '{q_type}': Use style like '{example}'\n"

    # 6. دمج مصفوفة الأولويات (Subject Matrix)
    subject_bundle = merge_subject_matrices(config, subjects)
    priority_block = f"HIGH PRIORITY CONCEPTS: {', '.join(subject_bundle['high'])}\n"
    priority_block += f"MEDIUM PRIORITY: {', '.join(subject_bundle['medium'])}"

    source_language = detect_source_language(text_content)
    
    # إرسال تقرير للمشرف (Admin Log)
    log_msg = (f"🚀 Generating {num_questions} Qs\n"
               f"📚 Subjects: {', '.join(subjects)}\n"
               f"📊 Final Stage: {user_stage}\n"
               f"🧠 Cog Level: {metadata.get('cognitive_level')}")
    mybot.send_message(chat_id=admin_id, text=log_msg)

    # 7. البرومبت النهائي (التحفة الفنية)
    final_prompt = f"""
SYSTEM ROLE: Expert {config['title']} Professor.

GOAL: Generate {num_questions} MCQs from the SOURCE TEXT.
TARGET LEVEL: {user_stage.upper()}

CONTEXT:
- Subjects: {", ".join(subjects)}

CONSTRAINTS:
- Language: {source_language}
- Exactly {num_questions} questions.
- Exactly 4 options per question.
- No facts outside the provided source.

QUESTION TYPES TO GENERATE:
{chr(10).join([f"- {item['slot']}. {item['type']}" for item in question_plan])}

STYLE & PATTERN GUIDES:
{style_patterns}

CONTENT PRIORITIES:
{priority_block}

DISTRACTOR RULES:
{chr(10).join(config['generate_distractors'])}

EXPLANATION GUIDELINES:
{explanation_style_guidelines}

SOURCE TEXT:
{text_content}

OUTPUT FORMAT: Return ONLY a JSON array of objects with: 
(question, options, correct_index, explanation, type, difficulty, Branch: "e.g: anatomy")
"""
    return final_prompt
            

import os
import json
from ai.llm_client import generate_smart_response
from utils.json_utils import extract_json_objects_safely, parse_llm_json



example_json_format = """
Output JSON format:

[
  {
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_index": 0
    "explanation": "Step-by-step reasoning...",
    "type": "Recall/Clinical/etc"
  }
]
"""




def analyze_text_metadata(text_content):
    """
    تحليل النص لمعرفة التخصص والمرحلة
    """
    analysis_prompt = f"""
    Analyze the following content and recognize the main domain, return ONLY a JSON object with this exact structure:
    {{
      "domain": "medicine",
      "subject": "one of (anatomy, physiology, biochemistry, pathology, pharmacology, microbiology, clinical_medicine)",
      "concepts": ["list of 3-5 key medical concepts"],
      "estimated_difficulty": "early", "mid", or "advanced"
    }}
    content:
    {text_content[:1000]}
    """
    
    raw_response = generate_smart_response(analysis_prompt) 
    # تأكد من أن parse_llm_json ترجع string يمكن تمريره لـ json.loads
    # أو إذا كانت ترجع dict مباشرة، الغي json.loads
    parsed_response = parse_llm_json(raw_response)
    if isinstance(parsed_response, str):
        return json.loads(parsed_response)
    return parsed_response


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
    - Tone: {config['response_style']['tone']}
    - Structure: Every question MUST use a {config['response_style']['structure']}.
    - Explanation Depth: {config['response_style']['explanation_depth']}. Explain why the correct answer is right AND strictly explain why each distractor is wrong.

    SOURCE TEXT:
    {text_content}
    
    OUTPUT FORMAT: Return ONLY a valid JSON array of question objects.
    {example_json_format}
    """
    
    return final_prompt
    

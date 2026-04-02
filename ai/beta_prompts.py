
import json
import random

def analyze_text_metadata(text_content):
    """
    إرسال طلب سريع لمعرفة التخصص والمفاهيم الأساسية للنص
    """
    analysis_prompt = f"""
    Analyze the following medical text and return ONLY a JSON object with this structure:
    {{
      "subject": "one of (anatomy, physiology, biochemistry, pathology, pharmacology, microbiology, clinical_medicine)",
      "concepts": ["list of 3-5 key medical concepts"],
      "estimated_difficulty": "easy/moderate/hard"
    }}
    Text: {text_content[:2000]} # نكتفي بأول 2000 حرف للسرعة
    """
    
    # هنا تضع طلب الـ API الخاص بك (Gemini أو OpenAI)
    # لنفترض أن النتيجة عادت كـ JSON
    response = call_fast_llm_api(analysis_prompt) 
    return json.loads(response)
    


def generate_smart_prompt(user_id, text_content):
    # 1. تحليل النص أولاً
    metadata = analyze_text_metadata(text_content)
    detected_subject = metadata['subject']
    
    # 2. جلب بيانات المستخدم (نفترض أننا نعرف المرحلة الدراسية من قاعدة البيانات)
    user_stage = get_user_academic_stage(user_id) # 'early', 'mid', or 'advanced'
    
    # 3. تحميل ملف القواعد (domain_profile.json)
    with open('domain_profile.json', 'r') as f:
        config = json.load(f)["medicine"]

    # 4. اختيار أنواع الأسئلة بناءً على الأوزان (Weighted Random)
    # سنختار نوع السؤال لكل سؤال نريد توليده (مثلاً نولد 5 أسئلة)
    stage_weights = config["stages"][user_stage]["weights"]
    
    # تحويل الأوزان إلى قائمة متوافقة مع random.choices
    types = list(stage_weights.keys())
    weights = list(stage_weights.values())
    
    # اختيار النوع الغالب لهذه الجلسة بناءً على الوزن
    chosen_type = random.choices(types, weights=weights, k=1)[0]
    
    # 5. البحث عن النمط (Pattern) المناسب للنوع المختار
    # نستخدم pattern_mapping للوصول لقائمة الأنماط الصحيحة
    pattern_key = config["pattern_mapping"].get(chosen_type, "recall_patterns")
    patterns_list = config.get(pattern_key, config["Recall Patterns"]) # fallback to recall
    pattern_example = random.choice(patterns_list)

    # 6. بناء البرومبت النهائي (The Master Prompt)
    final_prompt = f"""
    SYSTEM ROLE: You are an expert Medical Education Specialist (USMLE Style).
    
    ACADEMIC CONTEXT:
    - Subject: {detected_subject}
    - Key Concepts: {", ".join(metadata['concepts'])}
    - Target Level: {user_stage} stage
    
    QUESTION STRUCTURE:
    - Format: {config['response_style']['structure']}
    - Tone: {config['response_style']['tone']}
    - Complexity: Focus on {chosen_type} with a weight of {stage_weights[chosen_type]}
    
    MANDATORY PATTERN:
    Use this question phrasing style: "{pattern_example}"
    
    DISTRACTOR RULES (STRICT):
    {chr(10).join([f"- {rule}" for rule in config['generate_distractors']])}
    
    EXPLANATION STYLE:
    {config['response_style']['explanation_depth']} - Explain why the correct is right AND why others are wrong.
    
    SOURCE TEXT:
    {text_content}
    
    OUTPUT: Generate 1 high-quality MCQ in valid JSON format.
    """
    
    return final_prompt
    

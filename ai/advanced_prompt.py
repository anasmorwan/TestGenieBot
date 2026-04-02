



def build_prompt(user_stage, detected_subject, text_content):
    # 1. سحب الإعدادات من ملف الـ JSON
    domain_data = json_file["medicine"]
    weights = domain_data["stages"][user_stage]["weights"]
    matrix = domain_data["subject_type_matrix"][detected_subject]
    
    # 2. اختيار نمط السؤال بناءً على الـ High Priority في المصفوفة
    # مثلاً لو Anatomy نختار Recall Patterns
    priority_type = matrix["high"][0] # مثلاً recall
    pattern_key = domain_data["pattern_mapping"][priority_type]
    pattern_example = random.choice(domain_data[pattern_key])

    # 3. دمج التعليمات
    full_prompt = f"""
    Context: {text_content}
    Task: {domain_data['prompt_instructions']}
    Specific Pattern to follow: {pattern_example}
    
    Distractor Rules:
    {chr(10).join(domain_data['generate_distractors'])}
    
    Tone: {domain_data['response_style']['tone']}
    Structure: {domain_data['response_style']['structure']}
    """
    return full_prompt

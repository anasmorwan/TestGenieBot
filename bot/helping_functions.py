

def truncate_text(text, max_length=150, keep_first_line=True):
    """
    دالة لاختصار النصوص بشكل ذكي
    
    Args:
        text: النص الأصلي
        max_length: الحد الأقصى لعدد الأحرف
        keep_first_line: إذا كان True، يحتفظ بالسطر الأول فقط (يتجاهل باقي الأسطر)
    
    Returns:
        النص المختصر
    """
    if not text:
        return "لا يوجد نص"
    
    text = str(text)
    
    # إذا كان النص قصيراً، أعده كما هو
    if len(text) <= max_length and not keep_first_line:
        return text
    
    if keep_first_line:
        # استخراج السطر الأول فقط (قبل أول \n)
        first_line = text.split('\n')[0]
        
        # إذا كان السطر الأول أطول من الحد، اختصره
        if len(first_line) > max_length:
            return first_line[:max_length - 3] + "..."
        return first_line
    
    else:
        # اختصار عادي مع الحفاظ على آخر الكلمات
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text

import re
import json

def extract_json_from_string(text: str):
    """
    محاولة استخراج JSON من نص مع إصلاح الأخطاء الشائعة.
    """

    def clean_json_string(s: str) -> str:
        # استبدال علامات اقتباس ذكية بعادية
        s = s.replace("“", '"').replace("”", '"')
        s = s.replace("‘", "'").replace("’", "'")
        # إزالة أي أحرف غير صالحة شائعة في استجابات الذكاء الاصطناعي
        s = re.sub(r"[^\x20-\x7E\n\t\r{}[\],:\"']+", "", s)
        # إزالة الفواصل الزائدة قبل } أو ]
        s = re.sub(r",(\s*[}\]])", r"\1", s)
        return s

    # البحث عن JSON داخل ```json ... ```
    match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if match:
        cleaned = clean_json_string(match.group(1))
        try:
            return json.loads(cleaned)
        except Exception as e:
            print("⚠️ Failed to parse JSON inside ```json:", e, cleaned[:200])

    # البحث عن أول JSON array أو object
    match = re.search(r'[{][\s\S]*[}]', text)
    if match:
        cleaned = clean_json_string(match.group(0))
        try:
            return json.loads(cleaned)
        except Exception as e:
            print("⚠️ Failed to parse JSON from text:", e, cleaned[:200])

    # إذا فشل كل شيء، إرجاع قائمة فارغة
    return []




def extract_json_objects_safely(text: str):
    """
    يحاول استخراج جميع كائنات JSON داخل نص، ويتجاهل أي كائن تالف.
    يعيد قائمة بالكائنات الصالحة فقط.
    """
    objects = []

    # إزالة أي تنسيقات markdown ```json ... ```
    text = re.sub(r'```json\s*([\s\S]*?)\s*```', r'\1', text)

    # البحث عن جميع الكائنات {...} أو المصفوفات [...] بالترتيب
    pattern = re.compile(r'{.*?}|\[.*?\]', re.DOTALL)
    for match in pattern.finditer(text):
        candidate = match.group()
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                objects.append(obj)
            elif isinstance(obj, list):
                # إذا كانت مصفوفة داخلية، نضيف كل عنصر على حدة
                for item in obj:
                    if isinstance(item, dict):
                        objects.append(item)
        except json.JSONDecodeError:
            continue  # تجاهل أي JSON غير صالح

    return objects




def parse_llm_json(text):
    # 1. تنظيف علامات المارك داون أولاً
    text = re.sub(r'```json\s*|```', '', text).strip()

    # 2. محاولة القراءة المباشرة (إذا كان الرد JSON صافي)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. استخراج المصفوفة (Array) حصراً
    # نبحث عن أول [ وآخر ] ونأخذ ما بينهما
    try:
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"⚠️ Failed to extract JSON Array: {e}")

    # 4. إذا فشل، نستخدم دالتك القديمة كـ Fallback نهائي
    return extract_json_objects_safely(text)

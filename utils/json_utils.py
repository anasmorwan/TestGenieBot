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

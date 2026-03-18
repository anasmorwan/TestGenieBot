import re
import json

def extract_json_from_string(text: str):
    """
    تحاول استخراج JSON من نص يحتوي على كود Markdown أو نصوص أخرى.
    ترجع قائمة فارغة إذا فشل التحويل، مع طباعة الأخطاء للمتابعة.
    """
    # أولًا، البحث عن ```json ... ```
    match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if match:
        json_text = match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print("JSON decode error in ```json block:", e)
        except Exception as e:
            print("Unexpected error parsing JSON block:", e)

    # ثانيًا، البحث عن أول كائن JSON أو مصفوفة []
    braces = re.search(r'(.*|\{.*\})', text, re.DOTALL)
    if braces:
        json_text = braces.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print("JSON decode error in braces/brackets:", e)
        except Exception as e:
            print("Unexpected error parsing braces/brackets JSON:", e)

    # أخيرًا، أي فشل → رجع قائمة فارغة
    print("No valid JSON found, returning empty list.")
    return []

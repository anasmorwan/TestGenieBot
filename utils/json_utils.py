import re
import json

def extract_json_from_string(text: str):
    # محاولة استخراج JSON داخل ```json
    match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # استخراج أول JSON Array فقط
    match = re.search(r'\s*{[\s\S]*?}\s*', text)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    return []

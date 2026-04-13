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



# =========================================================
# smart parser
# =========================================================


import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

# =========================================================
# Helpers
# =========================================================

def dump_model(model: BaseModel) -> dict:
    """Pydantic v1/v2 compatible dump."""
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def strip_noise(text: str) -> str:
    """إزالة الماركداون والرموز الخفية فقط، بدون أي تعديل خطير على JSON."""
    if not isinstance(text, str):
        return ""

    text = text.replace("\ufeff", "").replace("\u200b", "")
    text = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    return text.strip()


def conservative_json_fix(text: str) -> str:
    """
    إصلاحات محافظة جدًا:
    - تحويل علامات الاقتباس الذكية
    - حذف trailing commas
    لا تغيّر أسماء المفاتيح، ولا تحاول تخمين مفاتيح ناقصة.
    """
    text = strip_noise(text)
    text = text.replace("“", '"').replace("”", '"').replace("„", '"')
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text.strip()


def extract_balanced_object_segments(text: str) -> List[str]:
    """
    استخراج كل المقاطع المتوازنة من النوع {...} من النص، مع احترام النصوص داخل JSON.
    هذا بديل آمن عن regex الخام.
    """
    text = strip_noise(text)
    segments: List[str] = []

    in_string = False
    escape = False
    depth = 0
    start: Optional[int] = None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    segments.append(text[start:i + 1])
                    start = None

    return segments


def extract_balanced_array_segments(text: str) -> List[str]:
    """
    استخراج كل المقاطع المتوازنة من النوع [...]
    """
    text = strip_noise(text)
    segments: List[str] = []

    in_string = False
    escape = False
    depth = 0
    start: Optional[int] = None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "[":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "]":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    segments.append(text[start:i + 1])
                    start = None

    return segments


def try_json_load(text: str) -> Optional[Union[dict, list]]:
    """محاولة تحميل JSON مرة واحدة فقط."""
    try:
        return json.loads(text)
    except Exception:
        return None


def parse_json_lenient(text: str) -> Optional[Union[dict, list]]:
    """
    حاول:
    1) النص كما هو
    2) بعد تنظيف محافظ
    3) أي segment متوازن كائن/مصفوفة
    """
    candidates: List[str] = []
    cleaned = strip_noise(text)
    candidates.append(cleaned)
    candidates.append(conservative_json_fix(cleaned))

    candidates.extend(extract_balanced_object_segments(cleaned))
    candidates.extend(extract_balanced_array_segments(cleaned))

    seen = set()
    ordered_candidates = []
    for c in candidates:
        c2 = c.strip()
        if c2 and c2 not in seen:
            seen.add(c2)
            ordered_candidates.append(c2)

    for candidate in ordered_candidates:
        obj = try_json_load(candidate)
        if obj is not None:
            return obj

    return None


def casefold_dict(data: dict) -> dict:
    """تحويل المفاتيح لنسخة case-insensitive بدون فقد القيم."""
    if not isinstance(data, dict):
        return {}
    return {str(k).strip().casefold(): v for k, v in data.items()}


def first_present(mapping: dict, aliases: List[str]) -> Any:
    for key in aliases:
        k = key.casefold()
        if k in mapping and mapping[k] not in (None, "", [], {}):
            return mapping[k]
    return None


def coerce_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def coerce_float(value: Any, default: float = 1.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def coerce_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        s = value.strip()
        if re.fullmatch(r"[+-]?\d+", s):
            try:
                return int(s)
            except Exception:
                return None
        if len(s) == 1 and s.upper() in "ABCD":
            return ord(s.upper()) - 65
    return None


def coerce_str_list(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        out = []
        for item in value:
            s = coerce_str(item)
            if s:
                out.append(s)
        return out

    if isinstance(value, tuple) or isinstance(value, set):
        out = []
        for item in value:
            s = coerce_str(item)
            if s:
                out.append(s)
        return out

    if isinstance(value, dict):
        items = list(value.items())

        def sort_key(kv: Tuple[Any, Any]):
            k = str(kv[0]).strip()
            if k.isdigit():
                return (0, int(k))
            if len(k) == 1 and k.isalpha():
                return (1, k.upper())
            return (2, k.casefold())

        items.sort(key=sort_key)
        out = []
        for _, v in items:
            s = coerce_str(v)
            if s:
                out.append(s)
        return out

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        parts = [p.strip(" \t\r\n-•*") for p in re.split(r"[\n;|]+", text) if p.strip(" \t\r\n-•*")]
        if len(parts) > 1:
            return parts
        return [text]

    return [coerce_str(value)]


def normalize_options(value: Any) -> List[str]:
    """
    خيارات السؤال:
    - list/tuple/set => كما هي
    - dict => نرتبها
    - string => نحاول تفكيكها بشكل بسيط
    """
    options = coerce_str_list(value)

    # تنظيف بسيط
    options = [opt.strip() for opt in options if opt and opt.strip()]

    # لو كانت مصفوفة واحدة فقط من نص طويل يحاول النموذج تمريرها
    if len(options) == 1 and "\n" in options[0]:
        lines = [x.strip(" \t\r\n-•*") for x in options[0].splitlines()]
        lines = [x for x in lines if x]
        if len(lines) > 1:
            options = lines

    return options


def infer_correct_index(item: dict, options: List[str]) -> Optional[int]:
    """
    قبول:
    - رقم صحيح
    - نص رقمي "0"
    - حرف A/B/C/D
    - نص يطابق أحد الخيارات
    - correct_answer / answer / right_answer / solution كنص
    """
    aliases = [
        "correct_index", "answer_index", "right_index", "correct", "answer"
    ]
    value = first_present(item, aliases)

    idx = coerce_int(value)
    if idx is not None and 0 <= idx < len(options):
        return idx

    if isinstance(value, str):
        s = value.strip().casefold()
        for i, opt in enumerate(options):
            if s == opt.strip().casefold():
                return i

    for alias in ["correct_answer", "right_answer", "solution", "answer_text"]:
        ans = first_present(item, [alias])
        if ans is None:
            continue
        ans_s = coerce_str(ans).casefold()
        for i, opt in enumerate(options):
            if ans_s == opt.strip().casefold():
                return i

    return None


def normalize_question_item(raw_item: Any) -> Optional[dict]:
    if not isinstance(raw_item, dict):
        return None

    item = casefold_dict(raw_item)

    question_text = coerce_str(first_present(item, ["question", "q", "prompt", "stem", "text"]))
    if not question_text:
        return None

    options = normalize_options(first_present(item, ["options", "choices", "answers", "variants", "alternatives"]))
    if len(options) < 2:
        return None

    # إصلاح هيكلي: نكمل حتى 4 فقط إذا كانت ناقصة، بدون اختراع محتوى
    if len(options) < 4:
        options = options + [""] * (4 - len(options))
    elif len(options) > 4:
        options = options[:4]

    correct_index = infer_correct_index(item, options)
    if correct_index is None or not (0 <= correct_index < len(options)):
        return None

    explanation = coerce_str(first_present(item, ["explanation", "rationale", "why", "note"]))
    branch = first_present(item, ["branch", "topic", "category", "subcategory"])
    branch = coerce_str(branch) if branch is not None else None

    normalized = {
        "question": question_text,
        "options": options,
        "correct_index": correct_index,
        "explanation": explanation,
        "branch": branch,
    }

    # تحقق نهائي من Pydantic
    try:
        validated = SimpleQuestion(**normalized)
        return dump_model(validated)
    except ValidationError:
        return None


def looks_like_question_dict(d: dict) -> bool:
    if not isinstance(d, dict):
        return False
    k = casefold_dict(d)
    return any(
        key in k
        for key in ["question", "q", "prompt", "stem", "options", "choices", "answers"]
    )


def salvage_questions_from_text(text: str) -> List[dict]:
    """
    إن فشل JSON الكامل، نحاول إنقاذ الأسئلة كعناصر منفردة.
    """
    raw_segments = extract_balanced_object_segments(text)
    candidates: List[dict] = []

    for seg in raw_segments:
        obj = try_json_load(seg)
        if obj is None:
            obj = try_json_load(conservative_json_fix(seg))

        if isinstance(obj, dict) and looks_like_question_dict(obj):
            q = normalize_question_item(obj)
            if q is not None:
                candidates.append(q)

    return candidates


def extract_string_field(text: str, field_names: List[str]) -> Optional[str]:
    """
    استخراج نص بسيط مثل domain أو subject من نص مشوش.
    لا يستخدمه إلا كـ fallback أخير.
    """
    if not isinstance(text, str):
        return None

    for name in field_names:
        pattern = re.compile(
            rf'(?is)"?{re.escape(name)}"?\s*:\s*"([^"]*?)"'
        )
        m = pattern.search(text)
        if m:
            value = m.group(1).strip()
            if value:
                return value

    return None


def extract_list_field(text: str, field_names: List[str]) -> List[str]:
    """
    استخراج قائمة نصية بسيطة من نص مشوش.
    """
    if not isinstance(text, str):
        return []

    for name in field_names:
        pattern = re.compile(rf'(?is)"?{re.escape(name)}"?\s*:\s*\[')
        m = pattern.search(text)
        if not m:
            continue

        tail = text[m.end() - 1:]
        # ابحث عن أول array متوازن من موضعها
        arrays = extract_balanced_array_segments(tail)
        if arrays:
            parsed = try_json_load(conservative_json_fix(arrays[0]))
            if isinstance(parsed, list):
                return coerce_str_list(parsed)

    return []


# =========================================================
# Pydantic Models
# =========================================================

class SimpleQuestion(BaseModel):
    question: str = ""
    options: List[str] = Field(default_factory=list)
    correct_index: int = 0
    explanation: str = ""
    branch: Optional[str] = None


class SimpleQuizOutput(BaseModel):
    domain: str = "Medicine"
    questions: List[SimpleQuestion] = Field(default_factory=list)


class StructureOutput(BaseModel):
    domain: str = "medicine"
    subject: str = ""
    concepts: List[str] = Field(default_factory=list)
    estimated_difficulty: str = "mid"
    cognitive_level: str = "application"
    source_mode: str = "textbook"
    confidence: float = 1.0


class ComplexMetadata(BaseModel):
    domain: str = "Medicine"
    topics: List[str] = Field(default_factory=list)
    difficulty: str = "Medium"
    discipline: str = ""


class ComplexQuestion(BaseModel):
    question: str = ""
    options: List[str] = Field(default_factory=list)
    correct_index: int = 0
    explanation: str = ""
    branch: str = ""
    complexity: str = "Analysis"


class ComplexQuizOutput(BaseModel):
    metadata: ComplexMetadata
    questions: List[ComplexQuestion] = Field(default_factory=list)


# =========================================================
# Normalizers
# =========================================================

def normalize_simple_quiz(raw: Union[dict, list], original_text: str) -> Optional[dict]:
    domain = "Medicine"
    questions_source: List[Any] = []

    if isinstance(raw, dict):
        data = casefold_dict(raw)

        domain = coerce_str(
            first_present(data, ["domain"])
            or first_present(casefold_dict(data.get("metadata", {})) if isinstance(data.get("metadata"), dict) else {}, ["domain"])
            or extract_string_field(original_text, ["domain"])
            or domain
        ) or domain

        questions_source = (
            raw.get("questions")
            or raw.get("Questions")
            or raw.get("question")
            or raw.get("items")
            or []
        )

        # إذا كان الكائن نفسه سؤالًا واحدًا
        if not questions_source and looks_like_question_dict(raw):
            questions_source = [raw]

    elif isinstance(raw, list):
        questions_source = raw
        domain = extract_string_field(original_text, ["domain"]) or domain

    # إن لم نحصل على أسئلة من البنية الرئيسية، نحاول الإنقاذ من النص
    if not questions_source:
        questions_source = salvage_questions_from_text(original_text)

    valid_questions: List[dict] = []
    for item in questions_source:
        q = normalize_question_item(item)
        if q is not None:
            valid_questions.append(q)

    if not valid_questions:
        return None

    try:
        validated = SimpleQuizOutput(domain=domain, questions=[SimpleQuestion(**q) for q in valid_questions])
        return dump_model(validated)
    except ValidationError:
        return None


def normalize_complex_quiz(raw: Union[dict, list], original_text: str) -> Optional[dict]:
    metadata_raw: Dict[str, Any] = {}
    questions_source: List[Any] = []

    if isinstance(raw, dict):
        data = casefold_dict(raw)

        metadata_raw = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        if not isinstance(metadata_raw, dict):
            metadata_raw = {}

        if not metadata_raw:
            metadata_raw = {
                "domain": first_present(data, ["domain"]) or extract_string_field(original_text, ["domain"]) or "Medicine",
                "topics": first_present(data, ["topics"]) or [],
                "difficulty": first_present(data, ["difficulty"]) or "Medium",
                "discipline": first_present(data, ["discipline"]) or "",
            }

        questions_source = raw.get("questions") or raw.get("Questions") or []
        if not questions_source and looks_like_question_dict(raw):
            questions_source = [raw]

    elif isinstance(raw, list):
        questions_source = raw
        metadata_raw = {
            "domain": extract_string_field(original_text, ["domain"]) or "Medicine",
            "topics": extract_list_field(original_text, ["topics"]),
            "difficulty": extract_string_field(original_text, ["difficulty"]) or "Medium",
            "discipline": extract_string_field(original_text, ["discipline"]) or "",
        }

    if not questions_source:
        questions_source = salvage_questions_from_text(original_text)

    valid_questions: List[dict] = []
    for item in questions_source:
        if not isinstance(item, dict):
            continue

        item_cf = casefold_dict(item)
        q = normalize_question_item(item)
        if q is None:
            continue

        # complex specific: لو كانت "complexity" موجودة فاحتفظ بها لو أمكن
        complexity = coerce_str(first_present(item_cf, ["complexity"])) or "Analysis"
        q["complexity"] = complexity

        try:
            valid_questions.append(dump_model(ComplexQuestion(**q)))
        except ValidationError:
            continue

    if not valid_questions:
        return None

    meta_cf = casefold_dict(metadata_raw)
    metadata_payload = {
        "domain": coerce_str(first_present(meta_cf, ["domain"]) or "Medicine") or "Medicine",
        "topics": coerce_str_list(first_present(meta_cf, ["topics"])),
        "difficulty": coerce_str(first_present(meta_cf, ["difficulty"]) or "Medium") or "Medium",
        "discipline": coerce_str(first_present(meta_cf, ["discipline"]) or ""),
    }

    try:
        validated = ComplexQuizOutput(
            metadata=ComplexMetadata(**metadata_payload),
            questions=[ComplexQuestion(**q) for q in valid_questions],
        )
        return dump_model(validated)
    except ValidationError:
        return None


def normalize_structure(raw: Union[dict, list], original_text: str) -> Optional[dict]:
    if not isinstance(raw, dict):
        return None

    data = casefold_dict(raw)

    # لو رجعت metadata بدل top-level، ندمجها
    meta = raw.get("metadata")
    if isinstance(meta, dict):
        meta_cf = casefold_dict(meta)
        merged = dict(meta_cf)
        merged.update(data)
        data = merged

    payload = {
        "domain": coerce_str(first_present(data, ["domain"]) or extract_string_field(original_text, ["domain"]) or "medicine"),
        "subject": coerce_str(first_present(data, ["subject"]) or extract_string_field(original_text, ["subject"]) or ""),
        "concepts": coerce_str_list(first_present(data, ["concepts"])),
        "estimated_difficulty": coerce_str(first_present(data, ["estimated_difficulty"]) or "mid"),
        "cognitive_level": coerce_str(first_present(data, ["cognitive_level"]) or "application"),
        "source_mode": coerce_str(first_present(data, ["source_mode"]) or "textbook"),
        "confidence": coerce_float(first_present(data, ["confidence"]) or 1.0, 1.0),
    }

    if not payload["subject"]:
        # structure بدون subject غالبًا غير مفيد
        return None

    try:
        validated = StructureOutput(**payload)
        return dump_model(validated)
    except ValidationError:
        return None


# =========================================================
# Main Parser
# =========================================================

def parse_llm_response(text: str, target_schema: str = "simple_quiz") -> Optional[dict]:
    """
    يقرأ رد النموذج ويحاول:
    - استخراج JSON كامل
    - أو إنقاذ الأسئلة/المفاتيح الجزئية
    - ثم يطبعها حسب الـ schema المطلوب
    """
    raw = parse_json_lenient(text)

    # fallback إضافي إذا فشل JSON بالكامل
    if raw is None:
        if target_schema == "simple_quiz":
            salvaged = salvage_questions_from_text(text)
            if salvaged:
                domain = extract_string_field(text, ["domain"]) or "Medicine"
                try:
                    validated = SimpleQuizOutput(
                        domain=domain,
                        questions=[SimpleQuestion(**q) for q in salvaged],
                    )
                    return dump_model(validated)
                except Validation

                

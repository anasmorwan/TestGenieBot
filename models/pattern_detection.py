import re
import unicodedata
from statistics import mean, pstdev
from typing import Optional, Dict, List, Tuple

# =========================
# إعدادات عامة
# =========================

MIN_TEXT_LEN = 12
MIN_QUESTION_LEN = 8
MIN_OPTIONS = 3
MAX_OPTIONS = 10
CONFIDENCE_THRESHOLD = 0.80

ARABIC_LETTERS = "أبجدهوزحطيكلمنسعفصقرشتثخذضظغ"
ARABIC_SEQ_COMMON_1 = ["أ", "ب", "ج", "د", "هـ", "و", "ز", "ح", "ط", "ي"]
ARABIC_SEQ_COMMON_2 = ["أ", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر"]

QUESTION_WORDS_AR = [
    "ما", "ماذا", "متى", "أين", "كيف", "لماذا", "هل", "أي", "كم", "من",
    "أذكر", "اشرح", "فسر", "قارن", "عرف", "اذكر"
]

QUESTION_WORDS_EN = [
    "what", "when", "where", "why", "how", "who", "whom", "whose", "which",
    "is", "are", "do", "does", "did", "define", "explain", "compare", "state"
]

QUESTION_PROMPTS_EN = [
    "choose the correct answer",
    "select the correct answer",
    "pick the correct answer",
    "which of the following",
    "what is the correct",
    "fill in the blank",
    "true or false",
    "complete the sentence",
    "identify the correct",
]

NEGATIVE_IMPERATIVE_PATTERNS = [
    r"^\s*(قل لي|احكي لي|اكتب لي|اشرح لي|لخص لي|اعطني|اعطيني|ارسم|ترجم|فصل|وضح)\b",
    r"^\s*(tell me|write|draw|explain|summarize|list|translate|describe|show me)\b",
]

BAD_PATTERNS = [
    r"https?://",
    r"www\.",
    r"^\s*(hi|hello|hey|thanks|thank you|ok|okay|lol)\b",
    r"^\s*(السلام عليكم|مرحبا|أهلا|اهلا)\b",
]

OPTION_PATTERNS = [
    r'^\s*[\(\[]?[A-Da-d][\)\]]?[\.\)\:\-]?\s+',                 # A) A. A: A- (A)
    r'^\s*[\(\[]?[1-9][\)\]]?[\.\)\:\-]?\s+',                    # 1) 1. 1: 1- (1)
    r'^\s*[\(\[]?[٠-٩][\)\]]?[\.\)\:\-]?\s+',                    # ١) ١. ١:
    r'^\s*[\-\*\•]\s+',                                          # - * •
    r'^\s*[\(\[]?[{letters}][\)\]]?[\.\)\:\-]?\s+'.format(letters=ARABIC_LETTERS),  # أ. ب) ت:
]

INLINE_OPTION_MARKER = (
    r'(?<!\S)(?:'
    r'[\(\[]?[A-Da-d][\)\]]?[\.\)\:\-]?\s+|'
    r'[\(\[]?[1-9][\)\]]?[\.\)\:\-]?\s+|'
    r'[\(\[]?[٠-٩][\)\]]?[\.\)\:\-]?\s+|'
    r'[\-\*\•]\s+|'
    r'[\(\[]?[' + ARABIC_LETTERS + r'][\)\]]?[\.\)\:\-]?\s+'
    r')'
)

# =========================
# أدوات مساعدة
# =========================

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("ـ", "")
    text = text.replace("\u200b", "")  # zero-width space
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str) -> List[str]:
    return [line.strip() for line in text.split("\n") if line.strip()]


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_bad_message(text: str) -> bool:
    lowered = text.lower()
    for pattern in BAD_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return True
    return False


def has_negative_imperative(text: str) -> bool:
    lowered = text.lower()
    for pattern in NEGATIVE_IMPERATIVE_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return True
    return False


def is_option_line(line: str) -> bool:
    return any(re.match(pattern, line) for pattern in OPTION_PATTERNS)


def strip_option_marker(line: str) -> str:
    cleaned = re.sub(
        r'^\s*[\(\[]?('
        r'[A-Da-d]|'
        r'[1-9]|'
        r'[٠-٩]|'
        r'[\-\*\•]|'
        r'[' + ARABIC_LETTERS + r']'
        r')[\)\]]?[\.\)\:\-]?\s+',
        '',
        line
    )
    return compact_whitespace(cleaned)


def looks_like_date_or_number_line(line: str) -> bool:
    line = line.strip()
    if re.fullmatch(r'\d{1,4}([/\-\.]\d{1,4}){1,3}', line):
        return True
    if re.fullmatch(r'[٠-٩\d\s,\.]+', line):
        return True
    return False


def count_scripts(text: str) -> Tuple[int, int, int]:
    arabic = len(re.findall(r'[\u0600-\u06FF]', text))
    latin = len(re.findall(r'[A-Za-z]', text))
    digits = len(re.findall(r'[0-9٠-٩]', text))
    return arabic, latin, digits


def detect_language(text: str) -> str:
    arabic, latin, _ = count_scripts(text)
    total = arabic + latin

    if total == 0:
        return "unknown"
    if arabic > 0 and latin == 0:
        return "ar"
    if latin > 0 and arabic == 0:
        return "en"

    ar_ratio = arabic / total
    en_ratio = latin / total

    if ar_ratio >= 0.75:
        return "ar"
    if en_ratio >= 0.75:
        return "en"
    return "mixed"


def has_question_signal(text: str) -> bool:
    if any(ch in text for ch in ("?", "؟")):
        return True

    lowered = text.lower()
    for word in QUESTION_WORDS_EN:
        if re.search(rf'\b{re.escape(word)}\b', lowered):
            return True

    for word in QUESTION_WORDS_AR:
        if re.search(rf'\b{re.escape(word)}\b', text):
            return True

    for prompt in QUESTION_PROMPTS_EN:
        if prompt in lowered:
            return True

    return False


def has_binary_quiz_context(text: str) -> bool:
    lowered = normalize_text(text).lower()
    patterns = [
        r'\b(true\s*/\s*false|false\s*/\s*true)\b',
        r'\b(yes\s*/\s*no|no\s*/\s*yes)\b',
        r'\b(صح\s*/\s*خطأ|خطأ\s*/\s*صح)\b',
        r'\b(صواب\s*/\s*خطأ|خطأ\s*/\s*صواب)\b',
        r'\b(نعم\s*/\s*لا|لا\s*/\s*نعم)\b',
        r'\b(true|false)\b',
        r'\b(yes|no)\b',
        r'\b(صح|خطأ)\b',
        r'\b(صواب|خطأ)\b',
        r'\b(نعم|لا)\b',
    ]
    return any(re.search(p, lowered, re.IGNORECASE) for p in patterns)


def option_word_count(option: str) -> int:
    return len([w for w in option.split() if w.strip()])


def coefficient_of_variation(values: List[int]) -> float:
    values = [v for v in values if v is not None]
    if not values:
        return 1.0
    if len(values) == 1:
        return 0.0
    m = mean(values)
    if m == 0:
        return 0.0
    return pstdev(values) / m


def option_shape_category(option: str) -> str:
    s = option.strip()
    if re.fullmatch(r'[0-9٠-٩.,]+', s):
        return "numeric"
    wc = option_word_count(s)
    if wc <= 1:
        return "single_word"
    if wc <= 4:
        return "short_phrase"
    return "long_phrase"


def extract_prefix_info(line: str) -> Optional[Tuple[str, str, str]]:
    """
    returns:
        (prefix_type, normalized_prefix, remainder)
    prefix_type in: en_alpha, numeric, ar_alpha, bullet
    """
    patterns = [
        (r'^\s*[\(\[]?([A-Da-d])[\)\]]?[\.\)\:\-]?\s+', "en_alpha"),
        (r'^\s*[\(\[]?([1-9])[\)\]]?[\.\)\:\-]?\s+', "numeric"),
        (r'^\s*[\(\[]?([٠-٩])[\)\]]?[\.\)\:\-]?\s+', "numeric"),
        (r'^\s*[\(\[]?([' + ARABIC_LETTERS + r'])[\)\]]?[\.\)\:\-]?\s+', "ar_alpha"),
        (r'^\s*[\-\*\•]\s+', "bullet"),
    ]

    for pattern, ptype in patterns:
        m = re.match(pattern, line)
        if m:
            if ptype == "bullet":
                return ("bullet", "-", re.sub(pattern, "", line).strip())

            raw = m.group(1)
            if ptype == "numeric":
                if raw in "٠١٢٣٤٥٦٧٨٩":
                    normalized = str("٠١٢٣٤٥٦٧٨٩".index(raw))
                else:
                    normalized = raw
            else:
                normalized = raw.upper()

            remainder = re.sub(pattern, "", line).strip()
            return (ptype, normalized, remainder)

    return None


def normalize_prefix_char(ch: str) -> str:
    if ch in "٠١٢٣٤٥٦٧٨٩":
        return str("٠١٢٣٤٥٦٧٨٩".index(ch))
    return ch.upper()


def check_prefix_consistency(options_raw: List[str]) -> Dict:
    """
    Returns a score and style info about prefix consistency.
    """
    parsed = []
    for opt in options_raw:
        info = extract_prefix_info(opt)
        if info and info[0] != "bullet":
            parsed.append(info)

    if len(parsed) < 2:
        return {
            "score": 0.0,
            "style": "none",
            "sequence_ok": False,
            "prefixes": [],
        }

    prefixes = [normalize_prefix_char(p[1]) for p in parsed]
    styles = [p[0] for p in parsed]

    style = styles[0]
    if any(s != style for s in styles):
        return {
            "score": 0.0,
            "style": "mixed",
            "sequence_ok": False,
            "prefixes": prefixes,
        }

    n = len(prefixes)

    if style == "en_alpha":
        seq = [chr(ord("A") + i) for i in range(10)]
        if prefixes == seq[:n]:
            return {"score": 1.0, "style": "en_alpha", "sequence_ok": True, "prefixes": prefixes}

    if style == "numeric":
        seq = [str(i) for i in range(1, 11)]
        if prefixes == seq[:n]:
            return {"score": 1.0, "style": "numeric", "sequence_ok": True, "prefixes": prefixes}

    for seq_name, seq in [
        ("ar_alpha_common_1", ARABIC_SEQ_COMMON_1),
        ("ar_alpha_common_2", ARABIC_SEQ_COMMON_2),
    ]:
        if prefixes == seq[:n]:
            return {"score": 1.0, "style": seq_name, "sequence_ok": True, "prefixes": prefixes}

    if style == "en_alpha":
        values = [ord(p) for p in prefixes if len(p) == 1 and p.isalpha()]
        if len(values) == n and values == sorted(values) and len(set(values)) == n:
            return {"score": 0.7, "style": "en_alpha", "sequence_ok": False, "prefixes": prefixes}

    if style == "numeric":
        values = [int(p) for p in prefixes if p.isdigit()]
        if len(values) == n and values == sorted(values) and len(set(values)) == n:
            return {"score": 0.7, "style": "numeric", "sequence_ok": False, "prefixes": prefixes}

    if style.startswith("ar_alpha"):
        return {"score": 0.5, "style": style, "sequence_ok": False, "prefixes": prefixes}

    return {"score": 0.0, "style": style, "sequence_ok": False, "prefixes": prefixes}


def structural_similarity_score(options: List[str]) -> Dict:
    """
    قياس تشابه البنية بين الخيارات.
    """
    word_counts = [option_word_count(o) for o in options]
    char_counts = [len(o) for o in options]
    categories = [option_shape_category(o) for o in options]

    cv_words = coefficient_of_variation(word_counts)
    cv_chars = coefficient_of_variation(char_counts)

    same_category_ratio = max(categories.count(c) for c in set(categories)) / len(categories)

    score = 0.0

    if cv_words <= 0.20:
        score += 0.45
    elif cv_words <= 0.40:
        score += 0.30
    elif cv_words <= 0.60:
        score += 0.15

    if cv_chars <= 0.20:
        score += 0.35
    elif cv_chars <= 0.40:
        score += 0.20
    elif cv_chars <= 0.60:
        score += 0.10

    if same_category_ratio >= 0.90:
        score += 0.20
    elif same_category_ratio >= 0.75:
        score += 0.10

    if cv_words > 0.80 or cv_chars > 0.80:
        score -= 0.20

    return {
        "score": max(0.0, min(1.0, score)),
        "cv_words": round(cv_words, 3),
        "cv_chars": round(cv_chars, 3),
        "same_category_ratio": round(same_category_ratio, 3),
    }


def negative_signal_score(text: str, lines: List[str]) -> Dict:
    """
    يقيس إشارات سلبية تقلل احتمال أن النص اختبار.
    """
    penalty = 0.0
    reasons = []

    if has_negative_imperative(text):
        penalty += 0.35
        reasons.append("imperative_or_chat_request")

    if lines:
        endings = sum(
            1 for line in lines
            if line.endswith(("،", ",", ";", "؛", ":", "…"))
        )
        ratio = endings / len(lines)
        if ratio >= 0.60 and len(lines) >= 3:
            penalty += 0.25
            reasons.append("prose_like_line_endings")

    long_lines = sum(1 for line in lines if len(line) > 120)
    if long_lines >= 2:
        penalty += 0.20
        reasons.append("too_many_long_lines")

    if len(lines) >= 4 and all(not is_option_line(l) for l in lines[:4]):
        if not has_question_signal(text):
            penalty += 0.15
            reasons.append("no_question_signal_in_multiline_text")

    return {
        "penalty": min(0.80, penalty),
        "reasons": reasons,
    }


def extract_inline_option_segments(text: str, min_options: int = MIN_OPTIONS) -> Optional[List[str]]:
    matches = list(re.finditer(INLINE_OPTION_MARKER, text))
    if len(matches) < min_options:
        return None

    segments = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        seg = text[start:end].strip()
        if seg:
            segments.append(seg)

    return segments if len(segments) >= min_options else None


def extract_inline_options(text: str, min_options: int = MIN_OPTIONS) -> Optional[List[str]]:
    segments = extract_inline_option_segments(text, min_options=min_options)
    if not segments:
        return None

    options = []
    for seg in segments:
        if re.match(INLINE_OPTION_MARKER, seg):
            options.append(strip_option_marker(seg))
        else:
            options.append(compact_whitespace(seg))

    options = [o for o in options if o]
    return options if len(options) >= min_options else None


def extract_question_from_inline(text: str) -> str:
    m = re.search(INLINE_OPTION_MARKER, text)
    if not m:
        return ""

    pre = text[:m.start()].strip()
    if not pre:
        return ""

    tail_idx = max(pre.rfind("?"), pre.rfind("؟"), pre.rfind(":"))
    if tail_idx != -1:
        tail = compact_whitespace(pre[tail_idx + 1:])
        if len(tail) >= MIN_QUESTION_LEN:
            return tail

    return compact_whitespace(pre)


def is_unlabeled_option_candidate(line: str) -> bool:
    s = line.strip()
    if not s:
        return False

    if len(s) > 120:
        return False

    wc = option_word_count(s)
    if wc > 12:
        return False

    if looks_like_date_or_number_line(s):
        return False

    comma_count = sum(s.count(ch) for ch in [",", "،", "؛", ";"])
    if comma_count >= 3:
        return False

    return True


def find_unlabeled_option_block(lines: List[str], min_options: int = MIN_OPTIONS) -> Optional[Tuple[int, List[str]]]:
    """
    يبحث عن كتلة خيارات بدون بادئات، بعد سطر/أسطر السؤال.
    """
    best = None

    for start in range(1, len(lines) - min_options + 1):
        block = []
        for line in lines[start:]:
            if is_option_line(line):
                break
            if is_unlabeled_option_candidate(line):
                block.append(line)
                if len(block) >= MAX_OPTIONS:
                    break
            else:
                if len(block) >= min_options:
                    break
                continue

        if len(block) >= min_options:
            sim = structural_similarity_score(block)
            candidate_score = sim["score"] + (0.05 if len(block) <= 6 else 0.0)
            if best is None or candidate_score > best["score"]:
                best = {"start": start, "block": block, "score": candidate_score, "sim": sim}

    if best:
        return best["start"], best["block"]
    return None


def language_bundle(question: str, options: List[str]) -> Dict:
    q_lang = detect_language(question)
    opt_text = " ".join(options)
    o_lang = detect_language(opt_text)

    mixed = (
        q_lang == "mixed" or
        o_lang == "mixed" or
        (q_lang != "unknown" and o_lang != "unknown" and q_lang != o_lang)
    )

    return {
        "question_language": q_lang,
        "option_language": o_lang,
        "mixed_language": mixed,
    }


def extract_question_from_lines(lines: List[str], first_option_idx: int) -> str:
    pre = lines[:first_option_idx]
    if not pre:
        return ""

    for i in range(len(pre) - 1, -1, -1):
        ln = pre[i].strip()
        lowered = ln.lower()
        if ln.endswith(("?", "؟", ":")) or "السؤال" in lowered or has_question_signal(ln):
            tail = ln.split(":")[-1].strip() if ":" in ln else ln
            tail = compact_whitespace(tail)
            if len(tail) >= MIN_QUESTION_LEN:
                return tail

    if len(pre) >= 3:
        candidate = compact_whitespace(" ".join(pre[-3:]))
        if len(candidate) >= MIN_QUESTION_LEN:
            return candidate

    return compact_whitespace(" ".join(pre))


# =========================
# الدالة الأساسية
# =========================

def detect_quiz_pattern(text: str) -> Optional[Dict]:
    """
    تكتشف سؤال اختيار من متعدد بالعربية أو الإنجليزية.
    تدعم:
    - الخيارات الأفقية داخل نفس السطر
    - الأسئلة الثنائية مثل صح/خطأ و True/False
    - السؤال متعدد الأسطر
    - اللغة المختلطة
    - درجة ثقة صارمة
    """
    if not text or len(text.strip()) < MIN_TEXT_LEN:
        return None

    text = normalize_text(text)
    if is_bad_message(text):
        return None

    lines = split_lines(text)
    if len(lines) < 2:
        return None

    binary_context = has_binary_quiz_context(text)
    min_options = 2 if binary_context else MIN_OPTIONS

    result_options = []
    question = ""
    explicit_mode = False
    unlabeled_mode = False
    prefix_info = None
    first_option_idx = None

    # -------------------------
    # 1) محاولة الخيارات الأفقية / داخل نفس السطر
    # -------------------------
    inline_options = extract_inline_options(text, min_options=min_options)
    inline_segments = extract_inline_option_segments(text, min_options=min_options)

    if inline_options:
        result_options = inline_options[:MAX_OPTIONS]
        question = extract_question_from_inline(text)
        explicit_mode = True
        unlabeled_mode = False

        if inline_segments:
            prefix_info = check_prefix_consistency(inline_segments[:len(result_options)])
        else:
            prefix_info = None
    else:
        # -------------------------
        # 2) محاولة الخيارات الصريحة في أسطر منفصلة
        # -------------------------
        explicit_option_lines = []

        for i, line in enumerate(lines):
            if is_option_line(line):
                explicit_option_lines.append(line)
                if first_option_idx is None:
                    first_option_idx = i

        if len(explicit_option_lines) >= min_options:
            explicit_mode = True
            result_options = [strip_option_marker(x) for x in explicit_option_lines[:MAX_OPTIONS]]
            result_options = [compact_whitespace(o) for o in result_options if compact_whitespace(o)]

            if first_option_idx is not None:
                question = extract_question_from_lines(lines, first_option_idx)
            else:
                for ln in lines:
                    if not is_option_line(ln):
                        question = compact_whitespace(ln)
                        break

            prefix_info = check_prefix_consistency(explicit_option_lines[:len(result_options)])
        else:
            # -------------------------
            # 3) محاولة كتلة خيارات بلا بادئات
            # -------------------------
            unlabeled = find_unlabeled_option_block(lines, min_options=min_options)
            if unlabeled is None:
                return None

            start_idx, block = unlabeled
            unlabeled_mode = True
            result_options = [compact_whitespace(x) for x in block[:MAX_OPTIONS] if compact_whitespace(x)]
            question = compact_whitespace(" ".join(lines[:start_idx]))

    if len(result_options) < min_options:
        return None

    if not question:
        return None

    if len(question) < MIN_QUESTION_LEN:
        return None

    # -------------------------
    # 4) طبقات التحقق
    # -------------------------
    score = 0.0
    layers = []

    def add(layer: str, points: float, reason: str):
        nonlocal score
        score += points
        layers.append({"layer": layer, "points": round(points, 3), "reason": reason})

    # Core structure
    if explicit_mode:
        add("structure", 2.30, "explicit_option_prefixes_found_or_inline_options")
    else:
        add("structure", 2.00, "unlabeled_option_block_found")

    # Question signal
    if has_question_signal(question):
        add("question_signal", 1.30, "question_like_language_or_punctuation")

    # Number of options
    if len(result_options) >= 4:
        add("option_count", 1.00, "four_or_more_options")
    elif len(result_options) == 3:
        add("option_count", 0.70, "three_options")
    elif len(result_options) == 2 and binary_context:
        add("option_count", 1.10, "binary_context_with_two_options")

    # Prefix consistency
    if explicit_mode and prefix_info:
        if prefix_info["sequence_ok"]:
            add("prefix_consistency", 1.20, f"sequential_prefixes_{prefix_info['style']}")
        elif prefix_info["score"] >= 0.7:
            add("prefix_consistency", 0.80, f"strong_same_style_prefixes_{prefix_info['style']}")
        elif prefix_info["score"] >= 0.5:
            add("prefix_consistency", 0.40, f"partial_prefix_consistency_{prefix_info['style']}")

    # Structural similarity
    sim = structural_similarity_score(result_options)
    if sim["score"] >= 0.80:
        add("structural_similarity", 1.00, "very_similar_option_lengths_and_shapes")
    elif sim["score"] >= 0.60:
        add("structural_similarity", 0.70, "similar_option_lengths_and_shapes")
    elif sim["score"] >= 0.40:
        add("structural_similarity", 0.35, "moderate_similarity")
    else:
        add("structural_similarity", -0.20, "weak_similarity")

    # Mixed-language handling
    lang = language_bundle(question, result_options)
    if lang["mixed_language"]:
        add("language_support", 0.35, "mixed_language_detected_but_accepted")
    else:
        add("language_support", 0.20, "single_language_detected")

    # Question multiline bonus
    if len(lines) >= 4 and first_option_idx is not None and first_option_idx >= 3:
        add("multiline_question", 0.45, "question_spans_multiple_lines_before_options")

    # Option compactness
    lengths = [len(o) for o in result_options]
    word_counts = [option_word_count(o) for o in result_options]
    cv_words = coefficient_of_variation(word_counts)
    cv_chars = coefficient_of_variation(lengths)

    if cv_words <= 0.20:
        add("option_shape_cv", 0.70, "very_low_word_count_variation")
    elif cv_words <= 0.40:
        add("option_shape_cv", 0.45, "low_word_count_variation")
    elif cv_words <= 0.60:
        add("option_shape_cv", 0.20, "moderate_word_count_variation")
    else:
        add("option_shape_cv", -0.35, "high_word_count_variation")

    if cv_chars <= 0.20:
        add("char_count_cv", 0.35, "very_low_char_variation")
    elif cv_chars <= 0.40:
        add("char_count_cv", 0.20, "low_char_variation")
    elif cv_chars <= 0.60:
        add("char_count_cv", 0.10, "moderate_char_variation")
    else:
        add("char_count_cv", -0.25, "high_char_variation")

    # Negative signals
    neg = negative_signal_score(text, lines)
    if neg["penalty"] > 0:
        add("negative_signals", -2.75 * neg["penalty"], ",".join(neg["reasons"]) or "negative_signals")

    # Prose penalty
    if not explicit_mode and len(lines) >= 3:
        endings = sum(1 for line in lines if line.endswith(("،", ",", ";", "؛")))
        ratio = endings / len(lines)
        if ratio >= 0.50:
            add("prose_penalty", -0.30, "too_many_lines_end_with_comma_like_punctuation")

    # Length penalty
    if max(lengths) > 180:
        add("length_penalty", -0.25, "one_or_more_options_are_too_long")

    # Unlabeled mode penalty without a question signal
    if unlabeled_mode and not has_question_signal(question):
        add("question_signal_penalty", -0.45, "unlabeled_options_without_question_signal")

    # -------------------------
    # 5) الحساب النهائي
    # -------------------------
    confidence = max(0.0, min(1.0, score / 7.0))
    is_quiz = confidence >= CONFIDENCE_THRESHOLD

    result = {
        "is_quiz": is_quiz,
        "confidence": round(confidence, 2),
        "question": question,
        "options": result_options,
        "count": len(result_options),
        "question_language": lang["question_language"],
        "option_language": lang["option_language"],
        "mixed_language": lang["mixed_language"],
        "prefix_consistency": prefix_info if explicit_mode else None,
        "structural_similarity": {
            "cv_words": sim["cv_words"],
            "cv_chars": sim["cv_chars"],
            "same_category_ratio": sim["same_category_ratio"],
            "score": sim["score"],
        },
        "validation_layers": layers,
        "negative_signals": neg["reasons"],
        "binary_context": binary_context,
    }

    return result if is_quiz else None
    

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

# Tier thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_LOW = 0.40

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
    r'^\s*[\(\[]?[A-Da-d][\)\]]?[\.\)\:\-]?\s+',
    r'^\s*[\(\[]?[1-9][\)\]]?[\.\)\:\-]?\s+',
    r'^\s*[\(\[]?[٠-٩][\)\]]?[\.\)\:\-]?\s+',
    r'^\s*[\-\*\•]\s+',
    r'^\s*[\(\[]?[{letters}][\)\]]?[\.\)\:\-]?\s+'.format(letters=ARABIC_LETTERS),
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

QUESTION_START_PATTERN = re.compile(r'^\s*(\d{1,3}|[٠-٩]{1,3})[\.\)\:\-]\s+')
QUESTION_PREFIX_RE = re.compile(r'^\s*(?:س/|السؤال|سؤال|question|q)\s*[:：\-]?\s*', re.IGNORECASE)

# =========================
# أدوات مساعدة
# =========================

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("ـ", "")
    text = text.replace("\u200b", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str) -> List[str]:
    return [line.strip() for line in text.split("\n") if line.strip()]


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def safe_preview(text: str, limit: int = 120) -> str:
    text = compact_whitespace(text)
    return text if len(text) <= limit else text[:limit - 1] + "…"


def is_bad_message(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered, re.IGNORECASE) for pattern in BAD_PATTERNS)


def has_negative_imperative(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered, re.IGNORECASE) for pattern in NEGATIVE_IMPERATIVE_PATTERNS)


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


def strip_question_prefix(line: str) -> str:
    s = compact_whitespace(line)
    s = QUESTION_PREFIX_RE.sub('', s, count=1)
    s = QUESTION_START_PATTERN.sub('', s, count=1)
    return compact_whitespace(s)


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
    parsed = []
    for opt in options_raw:
        info = extract_prefix_info(opt)
        if info:
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

    # Bullet groups are common in natural messages; reward consistency lightly.
    if style == "bullet":
        return {
            "score": 0.70 if len(prefixes) >= 3 else 0.35,
            "style": "bullet",
            "sequence_ok": False,
            "prefixes": prefixes,
        }

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
    penalty = 0.0
    reasons = []

    if has_negative_imperative(text):
        penalty += 0.30
        reasons.append("imperative_or_chat_request")

    if lines:
        endings = sum(
            1 for line in lines
            if line.endswith(("،", ",", ";", "؛", ":", "…"))
        )
        ratio = endings / len(lines)
        if ratio >= 0.60 and len(lines) >= 3:
            penalty += 0.20
            reasons.append("prose_like_line_endings")

    long_lines = sum(1 for line in lines if len(line) > 140)
    if long_lines >= 2:
        penalty += 0.15
        reasons.append("too_many_long_lines")

    return {
        "penalty": min(0.80, penalty),
        "reasons": reasons,
    }


def is_question_heading_line(line: str) -> bool:
    s = compact_whitespace(line)
    if not s:
        return False

    # Explicit question prefixes
    if QUESTION_PREFIX_RE.match(s):
        return True

    # Numeric question heading like: 1. What is ...
    m = QUESTION_START_PATTERN.match(s)
    if m:
        rest = strip_question_prefix(s)
        if has_question_signal(rest):
            return True
        if option_word_count(rest) >= 5 and len(rest) >= 25:
            return True

    # Plain question line
    if not QUESTION_START_PATTERN.match(s):
        if has_question_signal(s) and option_word_count(s) >= 3:
            return True

    return False


def split_quiz_blocks(lines: List[str]) -> List[List[str]]:
    """
    Splits a long message into blocks of questions.
    A new block starts only when a true question heading is detected.
    """
    blocks = []
    current = []

    for line in lines:
        if is_question_heading_line(line):
            if current and (any(is_option_line(x) for x in current) or has_question_signal(" ".join(current))):
                blocks.append(current)
                current = [line]
            elif not current:
                current = [line]
            else:
                current = [line]
        else:
            if current:
                current.append(line)
            else:
                current = [line]

    if current:
        blocks.append(current)

    return blocks


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
        if re.match(
            r'^\s*[\(\[]?[A-Da-d1-9٠-٩][\)\]]?[\.\)\:\-]?\s+|^\s*[\-\*\•]\s+|^\s*[\(\[]?[' + ARABIC_LETTERS + r'][\)\]]?[\.\)\:\-]?\s+',
            seg
        ):
            options.append(strip_option_marker(seg))
        else:
            options.append(compact_whitespace(seg))

    options = [o for o in options if o]
    return options if len(options) >= min_options else None


def extract_question_from_inline(text: str) -> str:
    m = re.search(
        r'(?<!\S)(?:[\(\[]?[A-Da-d1-9٠-٩][\)\]]?[\.\)\:\-]?\s+|[\-\*\•]\s+|[\(\[]?[' + ARABIC_LETTERS + r'][\)\]]?[\.\)\:\-]?\s+)',
        text
    )
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
    if not s or len(s) > 140:
        return False
    if looks_like_date_or_number_line(s):
        return False
    if option_word_count(s) > 14:
        return False

    comma_count = sum(s.count(ch) for ch in [",", "،", "؛", ";"])
    if comma_count >= 3:
        return False

    return True


def find_unlabeled_option_block(lines: List[str], min_options: int = MIN_OPTIONS) -> Optional[Tuple[int, List[str]]]:
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
            cand = sim["score"] + (0.05 if len(block) <= 6 else 0.0)
            if best is None or cand > best["score"]:
                best = {"start": start, "block": block, "score": cand, "sim": sim}

    if best:
        return best["start"], best["block"]
    return None


def language_bundle(question: str, options: List[str]) -> Dict:
    q_lang = detect_language(question)
    o_lang = detect_language(" ".join(options))
    mixed = (
        q_lang == "mixed" or
        o_lang == "mixed" or
        (q_lang not in ("unknown",) and o_lang not in ("unknown",) and q_lang != o_lang)
    )
    return {
        "question_language": q_lang,
        "option_language": o_lang,
        "mixed_language": mixed,
    }


def parse_quiz_block(block_lines: List[str]) -> Optional[Dict]:
    if not block_lines:
        return None

    block_lines = [ln.strip() for ln in block_lines if ln.strip()]
    if not block_lines:
        return None

    block_text = normalize_text("\n".join(block_lines))
    binary_context = has_binary_quiz_context(block_text)
    min_options = 2 if binary_context else MIN_OPTIONS

    first_line = block_lines[0]
    question_head = strip_question_prefix(first_line)

    explicit_option_lines = []
    first_option_idx = None
    for i, line in enumerate(block_lines[1:], start=1):
        if is_option_line(line):
            explicit_option_lines.append(line)
            if first_option_idx is None:
                first_option_idx = i

    inline_text = question_head + "\n" + "\n".join(block_lines[1:])
    inline_options = extract_inline_options(inline_text, min_options=min_options)
    inline_segments = extract_inline_option_segments(inline_text, min_options=min_options)

    mode = None
    prefix_info = None

    if inline_options:
        options = inline_options[:MAX_OPTIONS]
        question = extract_question_from_inline(inline_text) or question_head
        prefix_info = check_prefix_consistency(inline_segments[:len(options)]) if inline_segments else None
        mode = "inline"

    elif len(explicit_option_lines) >= min_options:
        options = [strip_option_marker(x) for x in explicit_option_lines[:MAX_OPTIONS]]
        options = [compact_whitespace(o) for o in options if compact_whitespace(o)]

        if first_option_idx is not None and first_option_idx > 1:
            question = compact_whitespace(" ".join([question_head] + block_lines[1:first_option_idx]))
        else:
            question = question_head

        prefix_info = check_prefix_consistency(explicit_option_lines[:len(options)])
        mode = "explicit"

    else:
        unlabeled = find_unlabeled_option_block(block_lines, min_options=min_options)
        if unlabeled is None:
            return None

        start_idx, block = unlabeled
        options = [compact_whitespace(x) for x in block[:MAX_OPTIONS] if compact_whitespace(x)]
        question = compact_whitespace(" ".join(block_lines[:start_idx])) if start_idx > 0 else question_head
        mode = "unlabeled"

    if len(options) < min_options or not question or len(question) < MIN_QUESTION_LEN:
        return None

    score = 0.0
    evidence = 0
    layers = []

    def add(layer: str, points: float, reason: str):
        nonlocal score, evidence
        score += points
        layers.append({"layer": layer, "points": round(points, 3), "reason": reason})
        if points > 0:
            evidence += 1

    # core structure
    if mode == "explicit":
        add("structure", 0.30, "explicit_option_prefixes_found")
    elif mode == "inline":
        add("structure", 0.30, "inline_options_found")
    else:
        add("structure", 0.24, "unlabeled_option_block_found")

    # question signal
    if QUESTION_PREFIX_RE.match(first_line) or is_question_heading_line(first_line):
        add("question_header", 0.10, "question_heading_detected")

    if has_question_signal(question):
        add("question_signal", 0.18, "question_like_language_or_punctuation")

    # option count
    if len(options) >= 4:
        add("option_count", 0.12, "four_or_more_options")
    elif len(options) == 3:
        add("option_count", 0.09, "three_options")
    elif len(options) == 2 and binary_context:
        add("option_count", 0.12, "binary_context_with_two_options")

    # prefix consistency
    if prefix_info:
        if prefix_info["sequence_ok"]:
            add("prefix_consistency", 0.12, f"sequential_prefixes_{prefix_info['style']}")
        elif prefix_info["style"] == "bullet":
            add("prefix_consistency", prefix_info["score"] * 0.10, "bullet_style_consistency")
        elif prefix_info["score"] >= 0.7:
            add("prefix_consistency", 0.08, f"strong_same_style_prefixes_{prefix_info['style']}")
        elif prefix_info["score"] >= 0.5:
            add("prefix_consistency", 0.05, f"partial_prefix_consistency_{prefix_info['style']}")

    # similarity
    sim = structural_similarity_score(options)
    if sim["score"] >= 0.80:
        add("structural_similarity", 0.12, "very_similar_option_lengths_and_shapes")
    elif sim["score"] >= 0.60:
        add("structural_similarity", 0.08, "similar_option_lengths_and_shapes")
    elif sim["score"] >= 0.40:
        add("structural_similarity", 0.04, "moderate_similarity")
    else:
        add("structural_similarity", -0.08, "weak_similarity")

    # language
    lang = language_bundle(question, options)
    if lang["mixed_language"]:
        add("language_support", 0.03, "mixed_language_detected_but_accepted")
    else:
        add("language_support", 0.02, "single_language_detected")

    # multiline bonus
    if len(block_lines) >= 4 and first_option_idx is not None and first_option_idx >= 2:
        add("multiline_question", 0.05, "question_spans_multiple_lines_before_options")

    # structural stability
    lengths = [len(o) for o in options]
    word_counts = [option_word_count(o) for o in options]
    cv_words = coefficient_of_variation(word_counts)
    cv_chars = coefficient_of_variation(lengths)

    if cv_words <= 0.20:
        add("option_shape_cv", 0.10, "very_low_word_count_variation")
    elif cv_words <= 0.40:
        add("option_shape_cv", 0.06, "low_word_count_variation")
    elif cv_words <= 0.60:
        add("option_shape_cv", 0.03, "moderate_word_count_variation")
    else:
        add("option_shape_cv", -0.06, "high_word_count_variation")

    if cv_chars <= 0.20:
        add("char_count_cv", 0.05, "very_low_char_variation")
    elif cv_chars <= 0.40:
        add("char_count_cv", 0.03, "low_char_variation")
    elif cv_chars <= 0.60:
        add("char_count_cv", 0.01, "moderate_char_variation")
    else:
        add("char_count_cv", -0.04, "high_char_variation")

    # negative signals
    neg = negative_signal_score(block_text, block_lines)
    if neg["penalty"] > 0:
        add("negative_signals", -neg["penalty"], ",".join(neg["reasons"]) or "negative_signals")

    if max(lengths) > 180:
        add("length_penalty", -0.05, "one_or_more_options_are_too_long")

    if not has_question_signal(question) and mode == "unlabeled":
        add("question_signal_penalty", -0.12, "unlabeled_options_without_question_signal")

    confidence = max(0.0, min(1.0, score))

    if confidence >= CONFIDENCE_HIGH:
        decision = "accept"
    elif confidence >= CONFIDENCE_LOW:
        decision = "review"
    else:
        decision = "reject"

    if decision == "reject":
        return None

    return {
        "decision": decision,
        "tier": "high" if decision == "accept" else "gray",
        "api_recommended": decision == "review",
        "is_quiz": True,
        "confidence": round(confidence, 2),
        "score": round(confidence, 2),  # backward compatibility
        "question": question,
        "options": options,
        "count": len(options),
        "question_language": lang["question_language"],
        "option_language": lang["option_language"],
        "mixed_language": lang["mixed_language"],
        "prefix_consistency": prefix_info,
        "structural_similarity": {
            "cv_words": round(cv_words, 3),
            "cv_chars": round(cv_chars, 3),
            "same_category_ratio": sim["same_category_ratio"],
            "score": sim["score"],
        },
        "validation_layers": layers,
        "negative_signals": neg["reasons"],
        "binary_context": binary_context,
        "mode": mode,
    }



def detect_quiz_pattern(text: str) -> Optional[Dict]:
    """
    Detects:
    - a single question with options
    - or a multi-question quiz in one message
    Returns:
        None        -> reject immediately
        dict(review)-> gray zone, send to API later
        dict(accept)-> high confidence, accept now
    """
    if not text or len(text.strip()) < MIN_TEXT_LEN:
        return None

    text = normalize_text(text)
    if is_bad_message(text):
        return None

    lines = split_lines(text)
    if len(lines) < 1:
        return None

    # If there are multiple question headings, prefer multi-block parsing.
    heading_count = sum(1 for l in lines if is_question_heading_line(l))

    if heading_count < 2:
        single = parse_quiz_block(lines)
        if single:
            return single

    blocks = split_quiz_blocks(lines)
    if len(blocks) >= 2:
        parsed_blocks = []
        for block in blocks:
            parsed = parse_quiz_block(block)
            if parsed:
                parsed_blocks.append(parsed)

        if parsed_blocks:
            avg_conf = sum(b["confidence"] for b in parsed_blocks) / len(parsed_blocks)
            strong_count = sum(1 for b in parsed_blocks if b["decision"] == "accept")

            decision = (
                "accept" if (avg_conf >= CONFIDENCE_HIGH and strong_count >= 2)
                else "review" if avg_conf >= CONFIDENCE_LOW
                else "reject"
            )

            if decision != "reject":
                strongest = max(parsed_blocks, key=lambda x: x["confidence"])
                return {
                    "decision": decision,
                    "tier": "high" if decision == "accept" else "gray",
                    "api_recommended": decision == "review",
                    "is_quiz": True,
                    "quiz_type": "multi_question",
                    "confidence": round(avg_conf, 2),
                    "score": round(avg_conf, 2),  # backward compatibility
                    "questions_count": len(parsed_blocks),
                    "strong_blocks": strong_count,
                    "blocks": parsed_blocks,
                    "question": strongest["question"],
                    "options": strongest["options"],
                    "count": strongest["count"],
                    "question_language": strongest["question_language"],
                    "option_language": strongest["option_language"],
                    "mixed_language": strongest["mixed_language"],
                }

    # fallback: try as a single block if multi split did not help
    single = parse_quiz_block(lines)
    if single:
        return single

    return None

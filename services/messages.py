MESSAGES = {
    "ar": {
        "Generating quiz": "جاري توليد الإختبار…",
        "FILE_READ_ERROR": "لم أستطع قراءة الملف.",
        "QUIZ_FAILED": "فشل توليد الاختبار.",
        "FILE_TOO_LARGE": "الملف كبير جداً (الحد 5MB)",
        "QUIZ_CREATED": "تم توليد {count} سؤال!"
    },

    "en": {
        "Generating quiz": "Generating quiz…",
        "FILE_READ_ERROR": "I couldn't read the file.",
        "QUIZ_FAILED": "Quiz generation failed.",
        "FILE_TOO_LARGE": "File is too large (limit 5MB)",
        "QUIZ_CREATED": "Generated {count} questions!"
    }
}

def get_message(key, lang="ar", **kwargs):
    text = MESSAGES.get(lang, {}).get(key, key)
    return text.format(**kwargs)

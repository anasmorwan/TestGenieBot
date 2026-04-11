from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

mapping = {
    "goal": {
        "قرار": "🤝قرار",
        "مقارنة": "⚖️ مقارنة",
        "رأي": "📊 رأي"
    },
    "tone": {
        "ودي": "😊 ودي",
        "رسمي": "🎯 رسمي",
        "حماسي": "🔥 حماسي"
    },
}


def get_poll_customize_keyboard(selected_tone="ودي", selected_goal="رأي", set=False):
    markup = InlineKeyboardMarkup(row_width=3)

    # 🎯 الهدف
    goals = ["📊 رأي", "⚖️ مقارنة", "🤝 قرار"]
    goal_buttons = []
    normalized_goal = mapping.get("goal").get(selected_goal)
    for g in goals:
        text = f"✅ {g}" if g == normalized_goal else g
        goal_buttons.append(InlineKeyboardButton(text, callback_data=f"goal_{g}"))
    markup.row(*goal_buttons)

    # 🎭 الطابع
    tones = ["😊 ودي", "🔥 حماسي", "🎯 رسمي"]
    normalized_tone = mapping.get("tone").get(selected_tone)
    tone_buttons = []
    for t in tones:
        text = f"✅ {t}" if t == normalized_tone else t
        tone_buttons.append(InlineKeyboardButton(text, callback_data=f"tone_{t}"))
    markup.row(*tone_buttons)

    # ⚙️ خيارات إضافية
    text = "✅ تم حفظ الإعدادات" if set else "⚙️ حفظ"   
    markup.row(
        InlineKeyboardButton(text, callback_data="poll_advanced")
    )

    # 🚀 توليد
    text_1 = "🚀 إعادة توليد الآن" if set else "🚀 إعادة توليد الاستطلاع"
    markup.row(
        InlineKeyboardButton(text_1, callback_data="regenerate")
    )

    return markup

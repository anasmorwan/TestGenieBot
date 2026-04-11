from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton



def get_poll_customize_keyboard(selected_tone="ودي", selected_goal="رأي"):
    markup = InlineKeyboardMarkup(row_width=3)

    # 🎯 الهدف
    goals = ["📊 رأي", "⚖️ مقارنة", "🤝 قرار"]
    goal_buttons = []
    for g in goals:
        text = f"✅ {g}" if g == selected_goal else g
        goal_buttons.append(InlineKeyboardButton(text, callback_data=f"goal_{g}"))
    markup.row(*goal_buttons)

    # 🎭 الطابع
    tones = ["😊 ودي", "🎯 رسمي", "🔥 حماسي"]
    tone_buttons = []
    for t in tones:
        text = f"✅ {t}" if t == selected_tone else t
        tone_buttons.append(InlineKeyboardButton(text, callback_data=f"tone_{t}"))
    markup.row(*tone_buttons)

    # ⚙️ خيارات إضافية
    markup.row(
        InlineKeyboardButton("⚙️ حفظ", callback_data="poll_advanced")
    )

    # 🚀 توليد
    markup.row(
        InlineKeyboardButton("🚀 إعادة توليد الاستطلاع", callback_data="regenerate")
    )

    return markup

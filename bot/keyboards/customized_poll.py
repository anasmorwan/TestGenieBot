from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_poll_customize_keyboard(selected_tone="ودي", selected_goal="رأي", is_set=False):
    markup = InlineKeyboardMarkup(row_width=3)

    # 🎯 الهدف
    goals = ["📊 رأي", "⚖️ مقارنة", "🤝 قرار"]
    goal_buttons = []
    
    for g in goals:
        # ✅ قارن العنصر مع selected_goal مباشرة (بدون المسافات الزائدة)
        if g == selected_goal:  # التصحيح هنا
            text = f"✅ {g}"
        else:
            text = g
        goal_buttons.append(InlineKeyboardButton(text, callback_data=f"goal_{g}"))
    markup.row(*goal_buttons)

    # 🎭 الطابع
    tones = ["😊 ودي", "🔥 حماسي", "🎯 رسمي"]
    tone_buttons = []
    for t in tones:
        # ✅ قارن العنصر مع selected_tone مباشرة
        if t == selected_tone:  # التصحيح هنا
            text = f"✅ {t}"
        else:
            text = t
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

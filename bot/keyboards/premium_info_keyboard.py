from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def premium_info_keyboard():
    # إعداد لوحة الأزرار
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("💳 اختيار الخطة", callback_data="plans"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    ]
    keyboard.add(*buttons)
    return keyboard

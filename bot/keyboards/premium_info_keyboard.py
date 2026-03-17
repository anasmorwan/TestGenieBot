from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def premium_info_keyboard():
    # إعداد لوحة الأزرار
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("💳 تفعيل TestGenie Pro", callback_data="plans"),
        InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    ]
    keyboard.add(*buttons)
    return keyboard

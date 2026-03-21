from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_keyboard():
    # إعداد لوحة الأزرار
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("⚡ جرب Pro الآن", callback_data="plans"),
        InlineKeyboardButton("📊 ماذا ستحصل؟", callback_data="premium_info"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    ]
    keyboard.add(*buttons)
    return keyboard


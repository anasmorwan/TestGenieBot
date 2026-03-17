from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_keyboard():
    # إعداد لوحة الأزرار
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("💳 تفعيل TestGenie Pro", callback_data="plans"),
        InlineKeyboardButton("🔍 معرفة المميزات", callback_data="premium_info"),
        InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    ]
    keyboard.add(*buttons)
    return keyboard


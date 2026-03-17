from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_keyboard():
    # إعداد لوحة الأزرار
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("💳 تفعيل TestGenie Pro", callback_data="buy_subscription"),
        InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    ]
    keyboard.add(*buttons)
    return keyboard

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_keyboard():
    # إعداد لوحة الأزرار
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("💳 شراء الاشتراك", callback_data="buy_subscription"),
        InlineKeyboardButton("🔙 رجوع", callback_data="go_account_settings")
    ]
    keyboard.add(*buttons)
    return keyboard


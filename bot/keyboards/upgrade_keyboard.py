from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_keyboard():
    # إعداد لوحة الأزرار
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("💳 تفعيل TestGenie Pro", callback_data="buy_subscription"),
        InlineKeyboardButton("🔍 معرفة المميزات", callback_data="premium_info"),
        InlineKeyboardButton("🔙 رجوع", callback_data="go_account_settings")
    ]
    keyboard.add(*buttons)
    return keyboard


from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

def upgrade_keyboard()
    # إعداد لوحة الأزرار
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 شراء الاشتراك", callback_data="buy_subscription")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="go_account_settings")]
    ])
    return keyboard


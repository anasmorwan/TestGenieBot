from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def paid_plans_keyboard():

    upgrade_options_keyboard = InlineKeyboardMarkup(row_width=1)
    upgrade_options_keyboard.add(
        InlineKeyboardButton("🔥 اشتراك Pro", callback_data="buy_subscription1"),
        InlineKeyboardButton("⭐ اشتراك Pro+", callback_data="buy_subscription2"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    )
    return upgrade_options_keyboard

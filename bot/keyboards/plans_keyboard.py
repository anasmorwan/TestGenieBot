from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_options_keyboard():

    upgrade_options_keyboard = InlineKeyboardMarkup(row_width=1)
    upgrade_options_keyboard.add(
        InlineKeyboardButton("🟢 خطة Pro", callback_data="buy_subscription"),
        InlineKeyboardButton("🔵 خطة Pro+", callback_data="buy_subscription"),
        InlineKeyboardButton("📩 تواصل معي", url="https://t.me/anasM2002"),
        InlineKeyboardButton("🔙 رجوع", callback_data="go_account_settings")
    )
    return upgrade_options_keyboard

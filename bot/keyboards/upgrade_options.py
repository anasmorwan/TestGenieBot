from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_options_keyboard():

    upgrade_options_keyboard = InlineKeyboardMarkup(row_width=1)
    upgrade_options_keyboard.add(
        InlineKeyboardButton("🌟 الدفع بالنجوم", callback_data="pay_stars"),
        InlineKeyboardButton("🏦 الدفع المحلي (السودان)", callback_data="pay_local"),
        InlineKeyboardButton("📩 تواصل معي للدفع", url="https://t.me/anasM2002"),
        InlineKeyboardButton("🔙 رجوع", callback_data="plans")
    )
    return upgrade_options_keyboard

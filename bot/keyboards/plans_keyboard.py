from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def paid_plans_keyboard():

    upgrade_options_keyboard = InlineKeyboardMarkup(row_width=1)
    upgrade_options_keyboard.add(
        InlineKeyboardButton("🟢 خطة Pro", callback_data="buy_subscription"),
        InlineKeyboardButton("🔵 خطة Pro+", callback_data="buy_subscription"),
        InlineKeyboardButton("📩 تواصل معي", url="https://t.me/anasM2002"),
        InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    )
    return upgrade_options_keyboard

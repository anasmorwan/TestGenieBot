from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def send_poll_keyboard(text, poll_code):
    markup = InlineKeyboardMarkup(row_width=1)

    btn_status = InlineKeyboardButton("🚀 نشر في القناة", callback_data=f"post_poll:{poll_code}")
    btn_upgrade = InlineKeyboardButton("🔄 إعادة توليد", callback_data=f"regenerate:{text}")

    

    markup.add(btn_status, btn_upgrade, btn_back)
    return markup

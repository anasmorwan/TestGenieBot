from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def send_poll_keyboard(text, poll_code):
    markup = InlineKeyboardMarkup(row_width=1)

    btn_post = InlineKeyboardButton("🚀 نشر في القناة", callback_data=f"post_poll:{poll_code}")
    btn_regenerate = InlineKeyboardButton("🔄 إعادة توليد", callback_data=f"regenerate:{text}")

    

    markup.add(btn_post, btn_regenerate)
    return markup

def escape_action_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    
    btn_cancel = InlineKeyboardButton("× إلغاء", callback_data=f"cancel")

    

    markup.add(btn_cancel)
    return markup

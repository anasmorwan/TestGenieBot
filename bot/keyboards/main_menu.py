# main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("👈 📄 ابدأ بإرسال ملف", callback_data="go_generate"),
        InlineKeyboardButton("⚡ سؤال سريع", callback_data="quick_quiz"),
        InlineKeyboardButton("⚙️ حسابي", callback_data="go_account_settings"),
    ]
    keyboard.add(*buttons)
    keyboard.add(
        InlineKeyboardButton("➕ أضفني إلى مجموعة", url=f"https://t.me/{bot_username}?startgroup=true")
    )
    return keyboard

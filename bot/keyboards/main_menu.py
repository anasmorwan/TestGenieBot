# main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.row(
        InlineKeyboardButton("📝 نص مباشر", callback_data="input_text"),
        InlineKeyboardButton("📎 إرسال ملف", callback_data="go_generate")

    return keyboard

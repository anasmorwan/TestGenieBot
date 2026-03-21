# main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)

    buttons = [
        InlineKeyboardButton("📄 إرسل ملف", callback_data="go_generate"),
        InlineKeyboardButton("✍️ إرسل نص", callback_data="input_text"),
        InlineKeyboardButton("⚙️ المزيد", callback_data="more_options")
    ]
    keyboard.add(*buttons)
    return keyboard


 
    

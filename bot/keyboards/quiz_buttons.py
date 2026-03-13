# quiz_keyboard

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def quiz_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("📝 إبدأ", callback_data="go_generate"),
        InlineKeyboardButton("​🚀 نشر في القناة", callback_data="quick_quiz"),
        ]
    keyboard.add(*buttons)
    
    return keyboard

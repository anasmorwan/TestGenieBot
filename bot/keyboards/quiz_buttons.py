# quiz_keyboard

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def quiz_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("📝 إبدأ", callback_data="start_quiz"),
        InlineKeyboardButton("​🚀 نشر في القناة", callback_data="post_quiz"),
        ]
    keyboard.add(*buttons)
    
    return keyboard

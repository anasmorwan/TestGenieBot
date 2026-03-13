# quiz_keyboard

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def quiz_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("📝 إبدأ", callback_data=f"start_quiz:{quiz_code}"),
    InlineKeyboardButton("​🚀 نشر في القناة", callback_data="post_quiz")
        ]
    keyboard.add(*buttons)
    
    return keyboard
